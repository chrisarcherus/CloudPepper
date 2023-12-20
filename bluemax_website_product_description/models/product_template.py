from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_brand_name = fields.Char(string="Brand Name")
    x_line_alpha = fields.Char(string="Line Alpha")
    x_mfg_part_number = fields.Char(string="Manufacturer Part Number")
    ecommerce_description = fields.Html(
        "Description", translate=True,
        help="The description will be displayed on the website product page")
    ecommerce_disclaimer = fields.Html(
        "Disclaimer", translate=True,
        help="The Disclaimer will be displayed on the website product page")
    specification_ids = fields.One2many('product.specification', 'product_id')