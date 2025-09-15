# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class EretailProductLink(models.Model):
    _name = 'eretail.product.link'
    _description = 'eRetail Product Link'

    product_id = fields.Many2one('product.template', string='Producto Odoo', required=True, ondelete='cascade')
    eretail_goods_code = fields.Char(
        string='GoodsCode eRetail', 
        required=True,
        help="ID único del producto en eRetail (ej. JND-7800). Generalmente es la Referencia Interna de Odoo."
    )
    # En una implementación real, eretail_tag_ids sería un Many2many a un nuevo modelo eretail.tag
    # Para simplificar, usamos un campo de texto.
    eretail_tag_ids_text = fields.Text(string='TagIDs (texto)', help="IDs de etiquetas eRetail, separadas por comas.")
    eretail_template = fields.Char(string='Plantilla eRetail', default='REG', help="Plantilla a usar en eRetail (ej. REG, SAL).")
    eretail_last_sync = fields.Datetime(string='Última Sincronización', readonly=True)
    eretail_sync_status = fields.Selection([
        ('pending', 'Pendiente'),
        ('synced', 'Sincronizado'),
        ('error', 'Error')
    ], string='Estado Sincronización', default='pending', copy=False)
    
    _sql_constraints = [
        ('eretail_goods_code_uniq', 'unique (eretail_goods_code)', 'El GoodsCode de eRetail debe ser único!')
    ]

    def action_retry_sync(self):
        for link in self:
            try:
                link.product_id.sync_with_eretail()
            except Exception as e:
                _logger.error("Error al reintentar sincronización para %s: %s", link.eretail_goods_code, e)
                self.env['mail.activity'].create({
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                    'res_id': link.id,
                    'res_model_id': self.env.ref('eretail_odoo_integration.model_eretail_product_link').id,
                    'summary': _('Error de Sincronización eRetail'),
                    'note': _('Falló el reintento de sincronización. Detalles: %s') % e,
                    'user_id': self.env.user.id,
                })

    @api.model
    def cron_mass_sync(self):
        _logger.info("Iniciando CRON de sincronización masiva con eRetail.")
        products_to_sync = self.search([('product_id.active', '=', True)])
        for link in products_to_sync:
            try:
                link.product_id.sync_with_eretail()
            except Exception as e:
                _logger.error("Error en CRON para producto %s: %s", link.eretail_goods_code, e)
        _logger.info("CRON de sincronización masiva con eRetail finalizado.")