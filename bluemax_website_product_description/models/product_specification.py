from odoo import fields, models


class ProductSpecification(models.Model):
    _name = 'product.specification'
    _description = 'Specification'

    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Specification Name', required=True)
    value = fields.Char(string='Specification Value')
    product_id = fields.Many2one('product.template')
