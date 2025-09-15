# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    eretail_api_url = fields.Char(string='eRetail API URL', config_parameter='eretail.api_url')
    eretail_api_user = fields.Char(string='eRetail API User', config_parameter='eretail.api_user')
    eretail_api_password = fields.Char(string='eRetail API Password', config_parameter='eretail.api_password')