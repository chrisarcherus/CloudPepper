# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ShipstationExt(models.Model):
    _inherit = 'res.company'

    shipstation_carrier_id = fields.Many2one('delivery.carrier')
