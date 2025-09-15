# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import json

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    eretail_link_id = fields.One2many('eretail.product.link', 'product_id', string='Vínculo eRetail')

    @api.multi
    def write(self, vals):
        # Hook para sincronización inmediata de precios
        if 'list_price' in vals:
            for product in self:
                if product.eretail_link_id:
                    product.sync_with_eretail(force_update=True)
        return super(ProductTemplate, self).write(vals)

    def button_sync_with_eretail(self):
        self.ensure_one()
        if not self.eretail_link_id:
            # Crear el vínculo si no existe, usando la referencia interna
            if not self.default_code:
                raise models.ValidationError("El producto debe tener una 'Referencia Interna' para vincularse con eRetail.")
            self.env['eretail.product.link'].create({
                'product_id': self.id,
                'eretail_goods_code': self.default_code,
            })
        self.sync_with_eretail(force_update=True)
        return True

    def sync_with_eretail(self, force_update=False):
        self.ensure_one()
        if not self.eretail_link_id:
            return

        api_service = self.env['eretail.api.service'].get_service()
        link = self.eretail_link_id[0]
        goods_code = link.eretail_goods_code
        log_model = self.env['eretail.sync.log']

        # 1. Obtener datos de eRetail
        eretail_data = api_service.get_product_data(goods_code)

        # 2. Preparar datos de Odoo
        price_with_tax = self.list_price * 1.21 # Asumiendo 21% IVA
        odoo_data = {
            'default_code': self.default_code,
            'barcode': self.barcode or '',
            'name': self.name,
            'list_price_taxed': "%.2f" % price_with_tax,
        }

        # 3. Comparar datos
        diffs = {}
        if eretail_data:
            # Lógica de comparación simplificada. Debe ser adaptada a la estructura real de `getList`.
            # Asumimos que getList devuelve un item con un array `items`.
            eretail_items = eretail_data.get('items', [])
            if len(eretail_items) > 2:
                if eretail_items[0] != odoo_data['default_code']: diffs['goods_code'] = (eretail_items[0], odoo_data['default_code'])
                if eretail_items[1] != odoo_data['name']: diffs['name'] = (eretail_items[1], odoo_data['name'])
                if float(eretail_items[2]) != float(odoo_data['list_price_taxed']): diffs['price'] = (eretail_items[2], odoo_data['list_price_taxed'])
        
        log_model.create({
            'product_id': self.id, 'eretail_goods_code': goods_code,
            'sync_type': 'compare', 'diff_data': json.dumps(diffs) if diffs else "Sin diferencias",
            'result': 'ok', 'eretail_response': json.dumps(eretail_data)
        })

        # 4. Actualizar si hay cambios o si se fuerza
        if diffs or not eretail_data or force_update:
            # Formato según el ejemplo de /api/goods/saveList
            payload_items = [
                self.default_code or '',      # GoodsCode
                self.name,                    # Nombre del producto
                "%.2f" % price_with_tax,      # Precio con IVA
                "%.2f" % self.list_price,     # Precio sin IVA (ejemplo)
                self.barcode or '',           # Código de barras (UPC)
                # ... Rellenar los 27 campos según la plantilla
            ]
            # Rellenar hasta 27 campos para coincidir con la API
            payload_items += [''] * (27 - len(payload_items))

            payload = [{
                "shopCode": "0001", # Debe venir de la configuración
                "template": link.eretail_template,
                "items": payload_items,
            }]
            
            update_result = api_service.update_product(payload)
            
            log_vals = {
                'product_id': self.id, 'eretail_goods_code': goods_code,
                'sync_type': 'update', 'eretail_response': json.dumps(update_result)
            }

            if update_result and update_result.get('code') == 0:
                log_vals['result'] = 'ok'
                link.write({'eretail_last_sync': fields.Datetime.now(), 'eretail_sync_status': 'synced'})
                
                # 5. Refrescar etiquetas
                # La API refresh requiere tag IDs, que no tenemos.
                # Asumimos que la actualización del producto es suficiente o
                # usamos un refresh por tienda si la API lo permite.
                # refresh_result = api_service.refresh_tags_by_product(goods_code)
                # log_model.create(...)
                
            else:
                # Manejo de errores
                log_vals['result'] = 'error'
                if update_result and update_result.get('code') == 9999: # Bug de backup
                    log_vals['result'] = 'warning'
                
                link.write({'eretail_sync_status': 'error'})

            log_model.create(log_vals)

    @api.model
    def mass_sync_action(self, product_ids):
        products = self.browse(product_ids)
        for product in products:
            try:
                product.button_sync_with_eretail()
            except Exception as e:
                _logger.error("Error en sincronización masiva para %s: %s", product.name, e)