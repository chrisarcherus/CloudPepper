from odoo import fields, models


class ShipstationConfiguration(models.Model):
    _inherit = 'shipstation.odoo.configuration.vts'

    update_create_shipping_charge = fields.Boolean(string='Update/Create Shipping Charge on SO Line')