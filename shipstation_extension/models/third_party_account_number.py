from odoo import fields,models,api,_

class ThirdPartyAccountNumber(models.Model):
    _name = "third.party.account.number"
    _description = "Third Party Account Number"

    name = fields.Char(string='Third Party Account Name',required=True)
    account_number = fields.Char(string='Account Number',required=True)
    billing_country_id = fields.Many2one('res.country',string='Country',required=True)
    partner_id = fields.Many2one('res.partner', string='Partner')
    parent_id = fields.Many2one('res.partner',related='partner_id.parent_id', store=True)

