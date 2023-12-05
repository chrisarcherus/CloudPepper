import os
import base64
import binascii
import logging
from requests import request
from PyPDF2 import PdfFileMerger
from odoo.exceptions import ValidationError
from odoo import fields,models,api,_
from odoo.tools import pdf
from odoo.addons.shipstation_shipping_odoo_integration.models.stock_picking_vts import StockPicking
_logger = logging.getLogger("shipstation")

def generate_label_from_shipstation(self):
    if not self.shipstation_multi_pac_ids:
        raise ValidationError("Please Add Package Dimesnion and Weight On Table")
    _logger.info(">>>>>>>>>>>>>>>>>> Generate Lebel")
    shipment_cost = 0.0
    self.ensure_one()
    if not self.carrier_id:
        raise ValidationError("Please set proper delivery method")
    final_tracking_number = []
    input_path = []
    label_datas = []
    file_name = self.name
    pdf_merger = PdfFileMerger()
    file_name = file_name.replace('/', '_')
    file_path = "/tmp/waves/"
    directory = os.path.dirname(file_path)
    try:
        os.stat(directory)
    except:
        os.system("mkdir %s" % (file_path))
    error_detail = ""
    if any(move.product_id.weight <= 0.0 for move in self.move_ids):
        raise ValidationError("Need to set Product Weight.")
    for package_id in self.shipstation_multi_pac_ids:
        _logger.info("Inside Package : %s" % (package_id))
        try:
            # if not package_id.is_generate_label_in_shipstation:
            #     continue
            weight = package_id.shipstation_weight
            carrier_id = self.carrier_id
            if carrier_id.store_id.create_multi_shipment:
                body = carrier_id.generate_shipment_from_shipstation(self, package_id, weight)
                _logger.info("Label Body >>>>>>>>>>> : %s" % (body))
                response_data = carrier_id.api_calling_function("/shipments/createlabel", body)
            else:
                body = carrier_id.generate_label_from_shipstation(self, package_id, weight)
                _logger.info("Label Body >>>>>>>>>>> : %s" % (body))
                response_data = carrier_id.api_calling_function("/orders/createlabelfororder", body)
            _logger.info("Label Response Data: %s" % (response_data))
            if response_data.status_code == 200:
                responses = response_data.json()
                _logger.info("Label Responsese >>>> After 200 : %s" % (responses))
                shipment_id = responses.get('shipmentId')
                if shipment_id:
                    self.shipstation_shipment_id = shipment_id
                    label_data = responses.get('labelData')
                    tracking_number = responses.get('trackingNumber')
                    shipment_cost += responses.get('shipmentCost')
                    final_tracking_number.append(tracking_number)
                    base_data = binascii.a2b_base64(str(label_data))
                    label_datas.append(base_data)
                    tracking_message = (_("Shipstation Tracking Number: </b>%s") % (tracking_number))
                    message_id = self.message_post(
                        body=tracking_message)  # attachments=[('%s_Shipstation_Tracking_%s.pdf' % (self.name ,tracking_number), base_data)]
                    # package_id.response_message = "Sucessfully Label Generated"
                    package_id.custom_tracking_number = tracking_number
                    package_id.shipstation_shipment_id = shipment_id
                    input_path.append("%s_%s.pdf" % (file_path, tracking_number))
                    # with open("%s_%s.pdf" % (file_path, tracking_number), "ab") as f:
                    #     f.write(base64.b64decode(message_id and message_id.attachment_ids[0] and message_id.attachment_ids[0].datas))
                    logmessage = _("<b>Tracking Numbers:</b> %s") % (tracking_number)
                    label_data_pdf = binascii.a2b_base64(str(label_data))
                    self.message_post(body=logmessage, attachments=[("%s.pdf" % (self.id), label_data_pdf)])
            else:
                error_code = "%s" % (response_data.status_code)
                _logger.info("ERROR CODE: %s" % (error_code))
                error_message = response_data.reason
                _logger.info("Package : ERROR Response: %s" % (response_data))
                error_detail = {'error': error_code + " - " + error_message + " - %s" % (
                            response_data.text or response_data.content)}
                # if response_data.json():
                #     error_detail = {'error': error_code + " - " + error_message + " - %s"%(response_data.json())}
                # package_id.response_message = error_detail
        except Exception as e:
            # package_id.response_message = e
            _logger.info("Exception >>>>> Inside Package: %s" % (e))
    # if self.weight_bulk:
    #     try:
    #         weight = self.weight_bulk
    #         body = self.carrier_id and self.carrier_id.generate_label_from_shipstation(self, False, weight)
    #         # warehouse_location_id = self.sale_id and self.sale_id.shipstation_warehouse_address_id
    #         # response_data=self.carrier_id and self.carrier_id.api_calling_function("/shipments/createlabel", body, warehouse_location_id)
    #         response_data = self.carrier_id.api_calling_function("/orders/createlabelfororder", body)
    #         if response_data.status_code == 200:
    #             responses = response_data.json()
    #             shipment_id = responses.get('shipmentId')
    #             if shipment_id:
    #                 self.shipstation_shipment_id = shipment_id
    #                 label_data = responses.get('labelData')
    #                 tracking_number = responses.get('trackingNumber')
    #                 shipment_cost += responses.get('shipmentCost')
    #                 final_tracking_number.append(tracking_number)
    #                 base_data = binascii.a2b_base64(str(label_data))
    #                 label_datas.append(base_data)
    #                 tracking_mesage = (_("Shipstation Tracking Number: </b>%s") % (tracking_number))
    #                 message_id = self.message_post(
    #                     body=tracking_mesage)  # attachments=[('%s_Shipstation_Tracking_%s.pdf' % (self.name ,tracking_number), base_data)]
    #                 input_path.append("%s_%s.pdf" % (file_path, tracking_number))
    #                 # with open("%s_%s.pdf" % (file_path, tracking_number), "ab") as f:f.write(base64.b64decode(message_id and message_id.attachment_ids[0] and message_id.attachment_ids[0].datas))
    #                 logmessage = _("<b>Tracking Numbers:</b> %s") % (tracking_number)
    #                 label_data_pdf = binascii.a2b_base64(str(label_data))
    #                 self.message_post(body=logmessage, attachments=[("%s.pdf" % (self.id), label_data_pdf)])
    #         else:
    #             error_code = "%s" % (response_data.status_code)
    #             _logger.info("Inside Bulk Weight ERROR CODE: %s" % (error_code))
    #             error_message = response_data.reason
    #             _logger.info("ERROR Reponse Data: %s" % (response_data))
    #             error_detail = {'error': error_code + " - " + error_message + " - %s" % (response_data.json())}
    #             # if response_data.json():
    #             #     error_detail = {'error': error_code + " - " + error_message + " - %s"%(response_data.json())}
    #             self.message_post(body=error_detail)
    #
    #     except Exception as e:
    #         self.message_post(body=e)
    #         _logger.info("Exception >>> Inside Bulk Weight: %s" % (e))
    if not final_tracking_number:
        # _logger.info("Not Final Tracking Number: %s" % (response_data))
        raise ValidationError("{}".format(error_detail))
    self.carrier_tracking_ref = ','.join(final_tracking_number)
    margin = (shipment_cost * 10)/100
    total_cost = shipment_cost + margin
    self.shipment_cost = total_cost
    delivery_line = self.sale_id and self.sale_id.order_line.filtered(lambda line:line.is_delivery)
    if delivery_line:
        delivery_line.price_unit = self.shipment_cost
    else:
        self.sale_id._create_delivery_line(self.carrier_id, shipment_cost)

    # for path in input_path:
    #     pdf_merger.append(path)

    file_data_temp = pdf.merge_pdf(label_datas)
    file_data_temp = base64.b64encode(file_data_temp)

    att_id = self.env['ir.attachment'].create(
        {'name': "Wave -%s.pdf" % (file_name or ""), 'type': 'binary', 'datas': file_data_temp or "",
         'mimetype': 'application/pdf', 'res_model': 'stock.picking', 'res_id': self.id, 'res_name': self.name})

    return True
    # return {
    #     'type': 'ir.actions.act_url',
    #     'url': '/web/binary/download_document?model=ir.attachment&field=datas&id=%s&filename=%s.pdf' % (
    #     att_id.id, self.name.replace('/', '_')),
    #     'target': 'self'
    # }

StockPicking.generate_label_from_shipstation = generate_label_from_shipstation
class StockPickingVts(models.Model):
    _inherit = 'stock.picking'



    third_party_account_id = fields.Many2one('third.party.account.number', string="Third party account number",
                                             help="enter third party's account number",)
    parent_id = fields.Many2one('res.partner', related='partner_id.parent_id', store=True)
    shipstation_multi_pac_ids = fields.One2many("shipstation.multi.pack", "shipstation_picking_id",
                                                string="Shipstation Multi Pack")

    @api.onchange('shipstation_multi_pac_ids')
    def onchange_shipstation_multi_pac_ids(self):
        if not self.carrier_id and self.picking_type_code == 'outgoing':
            raise ValidationError("Please Select The Carrier.")

    # @api.onchange('partner_id')
    # def onchange_partner(self):
    #     for rec in self:
    #         if rec.partner_id and rec.partner_id.parent_id:
    #             return {'domain': {'third_party_account_id':[('partner_id', 'in', [rec.partner_id.id and rec.partner_id.parent_id.id, rec.partner_id.id])] }}
    #         else:
    #             return {'domain': {'third_party_account_id':[('partner_id', '=', rec.partner_id.id)] }}


