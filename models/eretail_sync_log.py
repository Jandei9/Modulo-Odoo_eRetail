# -*- coding: utf-8 -*-
from odoo import models, fields

class EretailSyncLog(models.Model):
    _name = 'eretail.sync.log'
    _description = 'eRetail Synchronization Log'
    _order = 'create_date desc'

    product_id = fields.Many2one('product.template', string='Producto Odoo', readonly=True)
    eretail_goods_code = fields.Char(string='GoodsCode eRetail', readonly=True)
    sync_type = fields.Selection([
        ('compare', 'Comparación'),
        ('update', 'Actualización'),
        ('refresh', 'Refresco Etiqueta'),
        ('error', 'Error de Proceso')
    ], string='Acción', readonly=True)
    diff_data = fields.Text(string='Diferencias Detectadas (JSON)', readonly=True)
    result = fields.Selection([
        ('ok', 'OK'),
        ('warning', 'Warning'),
        ('error', 'Error')
    ], string='Resultado', readonly=True)
    eretail_response = fields.Text(string='Respuesta eRetail API', readonly=True)