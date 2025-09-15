# -*- coding: utf-8 -*-
{
    'name': "eRetail 3.2 Integration",
    'summary': """
        Integra Odoo con el sistema de etiquetas electrónicas eRetail 3.2.""",
    'description': """
        - Sincronización de productos y precios con eRetail.
        - Gestión de logs y estado de sincronización.
        - Acciones manuales y automáticas.
    """,
    'author': "Eduardo Núñez Vázquez",
    'website': "https://www.jandei.com",
    'category': 'Sales',
    'version': '12.0.1.0.0',
    'depends': ['base', 'product', 'mail'],
    'external_dependencies': {'python': ['requests']},
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/product_views.xml',
        'views/eretail_product_link_views.xml',
        'views/eretail_sync_log_views.xml',
        'views/eretail_menus.xml',
        'data/eretail_cron.xml',
    ],
    'installable': True,
    'application': True,
}