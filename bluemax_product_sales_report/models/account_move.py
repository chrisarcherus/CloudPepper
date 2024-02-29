from odoo import fields, models, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    location_id = fields.Many2one('stock.warehouse', string='Location')
