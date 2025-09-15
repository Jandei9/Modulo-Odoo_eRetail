# -*- coding: utf-8 -*-
from odoo import models, api
import requests
import json
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

# Singleton para el token
TOKEN_CACHE = {
    'token': None,
    'expiry': None,
}

class ERetailApiService(models.AbstractModel):
    _name = 'eretail.api.service'
    _description = 'eRetail API Service'

    @api.model
    def get_service(self):
        """Punto de entrada para obtener una instancia del servicio."""
        return self

    def _get_credentials(self):
        ICP = self.env['ir.config_parameter'].sudo()
        url = ICP.get_param('eretail.api_url', '')
        user = ICP.get_param('eretail.api_user', '')
        password = ICP.get_param('eretail.api_password', '')
        if not all([url, user, password]):
            raise models.ValidationError("Faltan credenciales de eRetail en la configuración.")
        return url, user, password
    
    def _get_token(self):
        now = datetime.now()
        if TOKEN_CACHE.get('token') and TOKEN_CACHE.get('expiry') and now < TOKEN_CACHE['expiry']:
            return TOKEN_CACHE['token']
        
        url_base, user, password = self._get_credentials()
        url = f"{url_base}/api/login"
        payload = {"userName": user, "password": password}
        headers = {'Content-Type': 'application/json'}
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 0 and data.get('body'):
                TOKEN_CACHE['token'] = data['body']
                TOKEN_CACHE['expiry'] = now + timedelta(hours=5, minutes=50) # El token dura 6 horas
                return TOKEN_CACHE['token']
            else:
                _logger.error("Error de autenticación eRetail: %s", data)
                return None
        except requests.exceptions.RequestException as e:
            _logger.error("Error de conexión al obtener token eRetail: %s", e)
            return None

    def _make_request(self, method, endpoint, payload=None):
        token = self._get_token()
        if not token:
            return {'code': -1, 'message': 'Fallo al obtener token de autenticación'}

        url_base, _, _ = self._get_credentials()
        url = f"{url_base}{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        try:
            if method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=payload, timeout=15)
            else: # GET
                response = requests.get(url, headers=headers, timeout=15)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            _logger.error("Error HTTP en API eRetail (%s): %s", url, e.response.text)
            return {'code': e.response.status_code, 'message': e.response.text}
        except requests.exceptions.RequestException as e:
            _logger.error("Error de conexión en API eRetail (%s): %s", url, e)
            return {'code': -1, 'message': str(e)}

    def get_product_data(self, goods_code):
        endpoint = "/api/Goods/getList"
        payload = {
            "pageIndex": 1, "pageSize": 1, "goodsCode": goods_code,
            "shopCodeCst": "0001" # Debe venir de la configuración
        }
        response = self._make_request('POST', endpoint, payload=payload)
        if response.get('body') and response['body'].get('itemList'):
            return response['body']['itemList'][0]
        return {}

    def update_product(self, payload):
        endpoint = "/api/goods/saveList"
        return self._make_request('POST', endpoint, payload=payload)

    def refresh_tags(self, shop_code, tag_ids):
        # Esta función requeriría los IDs de las etiquetas, que no tenemos directamente.
        # Una alternativa es un refresco por tienda o producto.
        # La API mostrada `/api/esl/tag/Refresh` parece la adecuada.
        endpoint = "/api/esl/tag/Refresh"
        payload = {
            "shopCode": shop_code,
            "refreshType": 4, # 4 = Price Tag ID List
            "tags": tag_ids
        }
        return self._make_request('POST', endpoint, payload=payload)