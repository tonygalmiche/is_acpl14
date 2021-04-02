# -*- coding: utf-8 -*-
{
    'name'     : 'InfoSaône - Module Odoo 14 pour ACPL',
    'version'  : '0.1',
    'author'   : 'InfoSaône',
    'category' : 'InfoSaône',
    'description': """
InfoSaône - Module Odoo 14 pour ACPL
===================================================
""",
    'maintainer' : 'InfoSaône',
    'website'    : 'http://www.infosaone.com',
    'depends'    : [
        'base',
        'stock',
        'sale_management',
        'account',
        'purchase',
],
    'data' : [
        'security/ir.model.access.csv',
        'report/layouts.xml',
        'report/conditions_generales_de_vente_templates.xml',
        'report/sale_report_templates.xml',
        'views/report_invoice.xml',
        'views/account_move_view.xml',
        'views/sale_view.xml',
        'views/partner_view.xml',
        'views/is_export_compta_view.xml',
        'views/product_view.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'qweb': [
    ],
}

