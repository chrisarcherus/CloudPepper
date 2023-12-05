# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ShipstationAccountMove(models.Model):
    _inherit = 'account.move'

    shipment_trc_number = fields.Char(string='Shipment Tracking Number', compute='_compute_ship_station_tracking_number')

    def _compute_ship_station_tracking_number(self):
        for record in self:
            sale_id = record.invoice_line_ids.mapped('sale_line_ids.order_id')
            if sale_id and sale_id.picking_ids:
                picking_ids = sale_id and sale_id.picking_ids
                tracking_number = picking_ids.mapped('carrier_tracking_ref')
                if tracking_number:
                    tracking_number = [number for number in tracking_number if number]
                    record.shipment_trc_number = ', '.join(tracking_number)
            else:
                record.shipment_trc_number = False
