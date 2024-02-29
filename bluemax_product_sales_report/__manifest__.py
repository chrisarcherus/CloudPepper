{
    'name': "Product Sales Report",
    'version': "17.0.1.0.0",
    'summary': """""",
    'description': """""",
    'author': "BlueMax",
    'company': 'BlueMax',
    'maintainer': 'BlueMax',
    'website': 'https://www.nckwebtech.com/',
    'category': 'Report',
    'depends': ['base', 'account', 'stock'],
    'data': [
            'security/account_security.xml',
            'security/ir.model.access.csv',
            'views/account_move_views.xml',
            'wizard/product_sale_views.xml',
            # 'report/product_sale_report.xml',
    ],
    "assets": {
        "web.assets_backend": [
            "bluemax_product_sales_report/static/src/change_gp_total.js",
            "bluemax_product_sales_report/static/src/bluemax_product_sales_report.js",
            "bluemax_product_sales_report/static/src/bluemax_product_sales_report.scss",
            "bluemax_product_sales_report/static/src/bluemax_product_sales_report.xml",
        ]
    },
    'images': ['static/description/banner.png'],
    'license': "AGPL-3",
    'installable': True,
    'application': True,
    'price': 78.50,
    'currency': 'USD',
}
