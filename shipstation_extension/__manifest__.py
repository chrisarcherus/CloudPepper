{
    'name': 'Shipstation Extension',
    'version': '1.0.0',
    'summary': 'Shipstation Extesion',
    'description': '',
    'category': '',
    'author': 'Vraja Technologies',
    'website': '',
    'license': '',
    'depends': ['shipstation_shipping_odoo_integration'],
    'data': [
        'security/ir.model.access.csv',
        'views/invoice_report.xml',
        'views/account_move.xml',
        'views/res_partner.xml',
        'views/stock_picking.xml',
        'views/shipstation_store_vts.xml',
        'views/third_party_account_number.xml',
        'views/res_company.xml'
    ],
    'demo': [''],
    'installable': True,
    'auto_install': False,
}

# 14.05.02.2022
# version changelog get parent and child zip code
# 14.09.02.2022
# custom changes based on chris requirement
# 14.11.02.2020
# fix 'shipstation_store_id' issue

# 15.18.02.2022
# fix the shipstation_rate_shipment() bug

# 15.01.03.2022
# fix generate label weight bug

# 15.16.03.2022
# add tracking number in invoice

# 15.22.03.2022
# fix tracking number view in invoice

#15.31.03.2022
#fix shipment name bug in label