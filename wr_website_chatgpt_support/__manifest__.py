# -*- coding: utf-8 -*-

{
    'name': 'Website ChatGPT Support',
    "version": "1.0",
    'category': 'General',
    'summary': 'Website ChatGPT Support',
    'description': """Website ChatGPT Support""",
    "author": "Vraja Technologies",
    "website": "https://www.vrajatechnologies.com",
    'depends': ['web', 'website'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/support_view.xml',
    ],
    'auto_install': False,
    'installable': True,
    "license": "LGPL-3",
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
