from odoo import api, fields, models


class ShipstationMultiPack(models.Model):
    _name = "shipstation.multi.pack"
    _description = "Shipstation Multi Pack"

    shipstation_height = fields.Float(string='Height', help="Height")
    shipstation_width = fields.Float(string='Width', help='Width')
    shipstation_length = fields.Float(string='Length', help='Length')
    shipstation_weight = fields.Float(string='Weight', help='Weight')
    custom_tracking_number = fields.Char(string="Shipstation Tracking Number",
                                         help="If tracking number available print it in this field.")
    shipstation_shipment_id = fields.Char(string="Shipstation Shipment", help="Shipstation Shipment ID.", copy=False)
    shipstation_picking_id = fields.Many2one("stock.picking", string="Stock Picking")
