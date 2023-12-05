from odoo import fields, models, api


class ShipstationResPartner(models.Model):
    _inherit = 'res.partner'


    third_party_account_ids = fields.One2many('third.party.account.number', 'partner_id', string='Third Party Account')