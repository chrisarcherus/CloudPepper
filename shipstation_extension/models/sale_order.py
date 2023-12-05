from odoo import api, fields, models


class ShipstationExtSaleOrder(models.Model):
    _inherit ='sale.order'

    def action_confirm(self):
        res = super(ShipstationExtSaleOrder, self).action_confirm()
        if not self.carrier_id:
            ss_carrier_id = self.company_id and self.company_id.shipstation_carrier_id
            if ss_carrier_id:
                vals = ss_carrier_id.rate_shipment(order=self)
                if vals['success']:
                    price = vals['price']
                    if price:
                        self.set_delivery_line(ss_carrier_id, price)
        return res
