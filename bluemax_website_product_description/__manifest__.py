# -*- coding: utf-8 -*-

{
    'name': 'eCommerce Description',
    'version': '1.0',
    'summary': 'eCommerce Description',
    'depends': ['base', 'product', 'website', 'website_sale', 'stock'],
    'images': ['static/description/banner.png'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/website_product_description_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
