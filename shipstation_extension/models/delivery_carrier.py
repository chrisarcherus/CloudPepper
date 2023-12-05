import base64
import json
import logging
import time
from datetime import datetime
from requests import request
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.addons.shipstation_shipping_odoo_integration.models.delivery_carrier import DeliveryCarrier

_logger = logging.getLogger(__name__)


@api.model
def shipstation_send_shipping(self, pickings):
    for picking in pickings:
        if not picking.shipstation_multi_pac_ids:
            raise ValidationError("Need to Multi Pack Weight and Dimension.")
        if any(move.product_id.weight <= 0.0 for move in picking.move_ids):
            raise ValidationError("Need to set Product Weight.")
        if not picking.shipstation_order_id and not picking.carrier_id.store_id.create_multi_shipment:
            body = self.create_or_update_order(picking)
            try:
                response_data = self.api_calling_function("/orders/createorder", body)
            except Exception as error:
                raise ValidationError(error)
            if response_data.status_code == 200:
                responses = response_data.json()
                _logger.info("Response Data: %s" % (responses))
                order_id = responses.get('orderId')
                order_key = responses.get('orderKey')
                order_number = responses.get('orderNumber')
                if order_id:
                    picking.shipstation_order_id = order_id
                    picking.shipstation_order_key = order_key
                    picking.shipstation_sale_order_number = order_number
                    picking.carrier_price = responses.get('shipmentCost', 0.0)
                    if not (picking and picking.sale_id and picking.sale_id.shipstation_order_number):
                        picking.sale_id.shipstation_order_number = order_number
                        picking.sale_id.shipstation_order_id = order_id
                        picking.sale_id.is_exported_to_shipstation = True
                        picking.sale_id.shipstation_store_id = picking.carrier_id and picking.carrier_id.store_id.id
                return [{'exact_price': 0.0, 'tracking_number': ''}]
            else:
                error_code = "%s" % (response_data.status_code)
                error_message = response_data.reason
                error_detail = {'error': error_code + " - " + error_message + " - "}
                # if response_data.json():
                #     error_detail = {'error': error_code + " - " + error_message + " - %s" % (response_data.json())}
                raise ValidationError("{}".format(error_detail))
        return [{'exact_price': 0.0, 'tracking_number': ''}]


DeliveryCarrier.shipstation_send_shipping = shipstation_send_shipping


class ShipstationDeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    def create_or_update_order(self, picking):
        request_data = super(ShipstationDeliveryCarrier, self).create_or_update_order(picking)
        client_order_ref = picking and picking.sale_id and picking.sale_id.client_order_ref or False
        if picking.shipstation_multi_pac_ids:
            request_data.get('weight').update({"value": picking.shipstation_multi_pac_ids[0].shipstation_weight})
            request_data.get('dimensions').update({"length": picking.shipstation_multi_pac_ids[0].shipstation_length})
            request_data.get('dimensions').update({"width": picking.shipstation_multi_pac_ids[0].shipstation_width})
            request_data.get('dimensions').update({"height": picking.shipstation_multi_pac_ids[0].shipstation_length})
        if picking.third_party_account_id:
            if request_data.get('advancedOptions'):
                request_data.get('advancedOptions').update({'billToParty': 'third_party', 'billToAccount': '{}'.format(
                    picking.third_party_account_id.account_number), 'billToPostalCode': '{}'.format(
                    picking and picking.partner_id.zip), 'billToCountryCode': "{}".format(
                    picking.third_party_account_id.billing_country_id.code)})
                if client_order_ref:
                    request_data.get('advancedOptions').update({'customField1': client_order_ref})
            else:
                request_data.update({'advancedOptions': {'billToParty': 'third_party', 'billToAccount': '{}'.format(
                    picking.third_party_account_id.account_number), 'billToPostalCode': '{}'.format(
                    picking and picking.partner_id.zip), 'billToCountryCode': "{}".format(
                    picking.third_party_account_id.billing_country_id.code)}})
                if client_order_ref:
                    request_data.get('advancedOptions').update({'customField1': client_order_ref})
        return request_data

    def generate_label_from_shipstation(self, picking, package_id=False, weight=False):
        res = super(ShipstationDeliveryCarrier, self).generate_label_from_shipstation(picking, package_id=package_id,
                                                                                      weight=weight)
        client_order_ref = picking and picking.sale_id and picking.sale_id.client_order_ref or False
        if client_order_ref:
            res.update({'advancedOptions': {'customField1': client_order_ref}})
        return res

    def generate_shipment_from_shipstation(self, picking, package_id=False, weight=False):
        picking_receiver_id = picking.partner_id
        picking_sender_id = picking.picking_type_id.warehouse_id.partner_id
        # weight = picking.shipping_weight
        # package_length = package_id.package_type_id.packaging_length if package_id and package_id.package_type_id else self.delivery_package_id.length
        # package_id = package_id and package_id.packaging_id
        shipstation_shipping_charge_id = picking.sale_id.shipstation_shipping_charge_id
        shipstation_service_code = shipstation_shipping_charge_id.shipstation_service_code if picking.sale_id.shipstation_shipping_charge_id else picking.carrier_id.shipstation_delivery_carrier_service_id.service_code
        # shipstation_service_code = shipstation_shipping_charge_id.shipstation_service_code
        # custom_package_id = package_id and package_id.package_type_id or self.delivery_package_id
        weight = package_id.shipstation_weight
        total_weight = self.get_total_weight(weight)
        client_order_ref = picking and picking.sale_id and picking.sale_id.client_order_ref or False
        request_data = {
            "carrierCode": "%s" % (self.shipstation_carrier_id and self.shipstation_carrier_id.code),
            "serviceCode": "%s" % (shipstation_service_code),
            "packageCode": "package",
            "confirmation": self.confirmation or "none",
            "shipDate": "%s" % (time.strftime("%Y-%m-%d")),
            "testLabel": True if not self.prod_environment else False,
            "weight": {
                "value": total_weight,
                "units": self.weight_uom or "pounds",
            },
            "dimensions": {
                "units": self.shipstation_dimentions or "inches",
                "length": package_id.shipstation_length or 0.0,
                "width": package_id.shipstation_width or 0.0,
                "height": package_id.shipstation_height or 0.0
            },
            "shipFrom": {
                "name": "%s" % (picking_sender_id.name),
                "company": "",
                "street1": "%s" % (picking_sender_id.street or ""),
                "street2": "%s" % (picking_sender_id.street2 or ""),
                "city": "%s" % (picking_sender_id.city or ""),
                "state": "%s" % (picking_sender_id.state_id and picking_sender_id.state_id.code or ""),
                "postalCode": "%s" % (
                        picking_sender_id.zip[:5] or "") if picking_sender_id.country_id.code == "US" else "%s" % (
                        picking_sender_id.zip or ""),
                "country": "%s" % (picking_sender_id.country_id and picking_sender_id.country_id.code or ""),
                "phone": "%s" % (picking_sender_id.phone or ""),
                "residential": self.shipstation_delivery_carrier_service_id and self.shipstation_delivery_carrier_service_id.residential_address
            },
            "shipTo": {
                "name": "%s" % (picking_receiver_id.name),
                "company": "",
                "street1": "%s" % (picking_receiver_id.street or ""),
                "street2": "%s" % (picking_receiver_id.street2 or ""),
                "city": "%s" % (picking_receiver_id.city or ""),
                "state": "%s" % (picking_receiver_id.state_id and picking_receiver_id.state_id.code or ""),
                "postalCode": "%s" % (picking_receiver_id.zip[
                                      :5] or "") if picking_receiver_id.country_id.code == "US" else "%s" % (
                        picking_receiver_id.zip or ""),
                "country": "%s" % (picking_receiver_id.country_id and picking_receiver_id.country_id.code or ""),
                "phone": "%s" % (picking_receiver_id.phone or ""),
                "residential": self.shipstation_delivery_carrier_service_id and self.shipstation_delivery_carrier_service_id.residential_address
            },
            "advancedOptions": {'customField1': client_order_ref},
            "testLabel": True if not self.prod_environment else False,
        }
        if picking.third_party_account_id:
            request_data.get('advancedOptions').update({'billToParty': 'third_party', 'billToAccount': '{}'.format(
                picking.third_party_account_id.account_number), 'billToCountryCode': "{}".format(
                picking.third_party_account_id.billing_country_id.code), 'billToPostalCode': '{}'.format(
                picking and picking.partner_id.zip)})
        return request_data
