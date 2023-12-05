# -*- coding: utf-8 -*-
from odoo import fields, models
import logging
from datetime import datetime

_logger = logging.getLogger("Shipstation")
from odoo.addons.shipstation_shipping_odoo_integration.models.shipstation_store_vts import shipstation_store_vts


def shipstation_order_managing_function(self, configuration=False, orders=False, operation_id=False,
                                        product_operation_id=False, product_datas=False, csvwriter=False,
                                        customer_csvwriter=False, customer_operation_id=False):
    shipstation_product_data_obj = self.env['shipstation.product.data']
    for order in orders:
        shipstation_order_id = order.get('orderId')
        shipstation_order_number = order.get('orderNumber')
        sale_order = self.env['sale.order'].search(
            [('shipstation_order_id', '=', shipstation_order_id), ('state', '!=', 'cancel'),
             ('shipstation_store_id', '=', self.id)], limit=1, order='date_order desc')
        warehouse_id = False
        date_time_str = order.get('orderDate')
        _logger.info('Date Time Str {0} Type : {1}'.format(date_time_str, type(date_time_str)))
        date = date_time_str[0:10]
        time = date_time_str[11:19]
        date_time = "{0} {1}".format(date, time)
        date_time_obj = datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')
        order_date = fields.Datetime.to_string(date_time_obj)
        if sale_order:
            sale_order = sale_order.filtered(lambda so: so.date_order.strftime("%Y-%m-%d") == date)
        if not sale_order:
            customerEmail = order.get('customerEmail')
            customerId = order.get('customerId')

            cust_response = order.get("shipTo")
            customer_name = cust_response.get('name')
            street = cust_response.get('street1')
            street2 = cust_response.get('street2')
            city = cust_response.get('city')
            state = cust_response.get('state')
            zip = cust_response.get('postalCode')
            country_code = cust_response.get('country')
            country_id = self.env['res.country'].search([('code', '=', country_code)], limit=1)
            state_id = self.env['res.country.state'].search([('code', '=', state)], limit=1)
            customer_csvwriter.writer.writerow(
                [customer_name, self.id, street, city, zip, state, country_code, customerEmail])

            if customerId == None:
                partner_obj = self.env['res.partner'].search(
                    [('imported_from_shipstation', '=', True), ('street', '=', street),
                     ('name', '=', customer_name), ('zip', '=', zip), ('city', '=', city),
                     ('email', '=', customerEmail)], limit=1)
                if not partner_obj:
                    customer_vals = {'name': customer_name,
                                     'street': street,
                                     'street2': street2,
                                     'city': city,
                                     'state_id': state_id and state_id.id,
                                     'country_id': country_id and country_id.id,
                                     'zip': zip,
                                     'email': customerEmail if not customerEmail == None else "",
                                     'shipstation_customerId': "",
                                     'imported_from_shipstation': True}
                    partner_obj = self.env['res.partner'].create(customer_vals)
                    _logger.info('Partner Created {}'.format(partner_obj.name))
                    response_msg = "Partner Created : {0}".format(partner_obj.name)
                    self.create_shipstation_operation_details(customer_operation_id, response_msg, False,
                                                              'customer')
            else:
                partner_obj = self.env['res.partner'].search([('shipstation_customerId', '=', customerId)],
                                                             limit=1)
            if not partner_obj:
                partner_obj = self.import_customer_from_shipstation(configuration, customerId,
                                                                    customer_operation_id)
                if not partner_obj:
                    message = "Customer Is Not Found In Order Response! Shipstation Order ID : {0}, Shipstation Order Number : {1}".format(
                        shipstation_order_id, shipstation_order_number)
                    self.create_shipstation_operation_details(customer_operation_id, order, True, 'sale_order')
                    continue

            shipping_partner_state = order.get('shipTo').get('state')
            shipping_partner_country = order.get('shipTo').get('country')
            state_id = self.env['res.country.state'].search([('code', '=', shipping_partner_state)], limit=1)
            country_id = self.env['res.country'].search([('code', '=', shipping_partner_country)], limit=1)
            vals = {
                'name': order.get('shipTo').get('name'),
                'street': order.get('shipTo').get('street1'),
                'street2': order.get('shipTo').get('street2'),
                'city': order.get('shipTo').get('city'),
                'state_id': state_id and state_id.id or False,
                'country_id': country_id and country_id.id or False,
                'phone': order.get('shipTo').get('phone'),
                'zip': order.get('shipTo').get('postalCode'),
                'type': 'delivery',
                'parent_id': partner_obj.id}

            carrierCode = order.get('carrierCode')
            serviceCode = order.get('serviceCode')
            packageCode = order.get('packageCode')
            carrier_id = self.carrier_id
            if not carrier_id:
                carrier_id = self.env['delivery.carrier'].search(
                    [('shipstation_carrier_id.code', '=', carrierCode),
                     ('shipstation_delivery_carrier_service_id.service_code', '=', serviceCode)], limit=1)
                if not carrierCode == None and not serviceCode == None:
                    if not carrier_id:
                        shipstation_carrier_id = self.env['shipstation.delivery.carrier'].search(
                            [('code', '=', carrierCode)])
                        shipstation_service_id = self.env['shipstation.delivery.carrier.service'].search(
                            [('service_code', '=', serviceCode)])
                        if shipstation_carrier_id and shipstation_service_id:
                            delivery_package_id = self.env['shipstation.delivery.package'].search(
                                [('package_code', '=', packageCode)], limit=1)
                            carrier_id = self.env['delivery.carrier'].create({"name": serviceCode,
                                                                              "delivery_type": "shipstation",
                                                                              "store_id": self.id,
                                                                              "integration_level": "rate",
                                                                              "shipstation_carrier_id": shipstation_carrier_id.id,
                                                                              'delivery_package_id': delivery_package_id.id,
                                                                              "shipstation_delivery_carrier_service_id": shipstation_service_id.id,
                                                                              "product_id": self.env.ref(
                                                                                  'shipstation_shipping_odoo_integration.shipstation_service_product').id
                                                                              })

            shipstation_warehouse_id = order.get('advancedOptions') and order.get('advancedOptions').get(
                'warehouseId')
            _logger.info(" Advance Option >>>>>>>>>>>>>>>>>>>>>{}".format(order.get('advancedOptions')))
            shipstation_warehouse_obj = self.env['shipstation.warehouse.detail'].search(
                [('warehouse_id', '=', shipstation_warehouse_id)], limit=1)
            _logger.info(
                "Shipstation Warehouse : {0} Shipstation Warehouse obj:{1}".format(shipstation_warehouse_id,
                                                                                   shipstation_warehouse_obj))
            warehouse_id = False
            if shipstation_warehouse_obj:
                warehouse_id = self.env['stock.warehouse'].search(
                    [('shipstation_warehouse_id', '=', shipstation_warehouse_obj.id)], limit=1)
            warehouse_id = warehouse_id if warehouse_id else self.warehouse_id
            if not warehouse_id:
                response_msg = "Warehouse  is not availabel :{0} ".format(shipstation_warehouse_id)
                _logger.info(response_msg)
                self.create_shipstation_operation_details(operation_id, response_msg, True, 'sale_order')
                continue

            delivery_price = order.get('shippingAmount', 0.0)
            vals.update({'partner_id': partner_obj.id,
                         'partner_invoice_id': partner_obj and partner_obj.id,
                         'partner_shipping_id': partner_obj and partner_obj.id,
                         'date_order': order_date,
                         'carrier_id': carrier_id and carrier_id.id,
                         'company_id': self.env.user.company_id.id,
                         'warehouse_id': warehouse_id.id,
                         'carrierCode': carrierCode,
                         'serviceCode': serviceCode,
                         'delivery_price': delivery_price
                         })
            is_create_order = True
            customField1 = order.get('advancedOptions').get('customField1') if order.get('advancedOptions').get(
                'customField1') else ""
            customField2 = order.get('advancedOptions').get('customField2') if order.get('advancedOptions').get(
                'customField2') else ""
            customField3 = order.get('advancedOptions').get('customField3') if order.get('advancedOptions').get(
                'customField3') else ""
            customField_deatils = "{0} : {1} : {2}".format(customField1, customField2, customField3)

            product_error_message = []
            for order_line in order.get('items'):
                option_name = ""
                product_name = order_line.get('name')
                product_sku = order_line.get("sku")
                product_qty = order_line.get("quantity")
                product_item_id = order_line.get("orderItemId")
                _logger.info("Order Items : {}".format(order_line))
                for option in order_line.get('options'):
                    option_name += option.get('name') + " " + option.get('value')
                if not product_sku:
                    product_id = self.env['product.product'].search([('default_code', '=', product_name.lower())],
                                                                    limit=1)
                    _logger.info(" IF CONDITION : {}".format(product_id))
                else:
                    product_id = self.env['product.product'].search([('default_code', '=', product_sku)], limit=1)
                    _logger.info("ELSE CONDITION : {}".format(product_id))
                if not product_id:
                    # vals
                    product_vals = self.create_product_from_shipstation(product_name, product_sku)
                    # product_template_id = self.env['product.template'].create(vals)
                    product_template_id = self.env['product.template'].create(product_vals)
                    product_id = self.env['product.product'].search([('product_tmpl_id', '=', product_template_id.id)])
                    response_msg = "{0} Product Created".format(product_id.name)
                    self.create_shipstation_operation_details(product_operation_id, response_msg, True,
                                                              'product')
                if not product_id:
                    response_msg = "Sale Order : {2} Prouduct Not Found  Product SKU : {0} and  Name : {1}".format(
                        product_sku, product_name, shipstation_order_number)
                    self.create_shipstation_operation_details(product_operation_id, response_msg, True,
                                                              'product')
                    is_create_order = False
                    product_error_message.append(order_line)
                    if not shipstation_product_data_obj.sudo().search(
                            [('store_id', '=', self.id), ('product_sku', '=', product_sku)]):
                        csvwriter.writer.writerow([product_item_id, product_sku, product_qty, product_name])
                        shipstation_product_data_obj.create({'store_id': self.id, 'product_sku': product_sku})
                    product_datas = True
                    continue

            if is_create_order:
                order_vals = self.sudo().create_sales_order_from_shipstation(vals)
                # shipstation_warehouse_address_id = self.shipstation_configuration_id.shipstation_warehouse_address_id
                order_vals.update({'shipstation_order_id': shipstation_order_id,
                                   'name': shipstation_order_number,
                                   'shipstation_order_number': shipstation_order_number,
                                   'shipstation_store_id': self.id,
                                   'shipstation_store': self.id,
                                   'serviceCode': serviceCode,
                                   'carrierCode': carrierCode,
                                   'user_id': self.user_id and self.user_id.id,
                                   'gift_note': order.get('giftMessage', ''),
                                   'customer_note': order.get('customerNotes', ''),
                                   # 'order_custom_data': customField_deatils,
                                   'orderStatus': order.get('orderStatus')})
                order_id = self.env['sale.order'].sudo().create(order_vals)
                response_msg = "Sale Order Created {0}".format(order_id.name)
                _logger.info("Sale Order Created {0}".format(order_id.name))
                self.sudo().create_shipstation_operation_details(operation_id, response_msg, False,
                                                                 'sale_order')
                if carrier_id and carrier_id.delivery_type == 'shipstation':
                    rate_record = carrier_id.shipstation_rate_shipment(order=order_id)
                    base_shipping_cost = rate_record.get('price')
                    order_id.set_delivery_line(carrier_id, base_shipping_cost)
                for order_line in order.get('items'):
                    _logger.info("ORDER ITEMS : {}".format(order_line))
                    option_name = ""
                    product_name = order_line.get('name')

                    product_sku = order_line.get("sku")
                    if not product_sku:
                        product_id = self.env['product.product'].search(
                            [('default_code', '=', product_name.lower())], limit=1)
                        _logger.info(" IF CONDITION : {}".format(product_id))
                    else:
                        product_id = self.env['product.product'].sudo().search(
                            [('default_code', '=', product_sku)], limit=1)
                        _logger.info("ELSE CONDITION : {}".format(product_id))
                    if not product_id:
                        vals = self.create_product_from_shipstation(product_name, product_sku)
                        product_template_id = self.env['product.template'].create(vals)
                        product_id = self.env['product.product'].search(
                            [('product_tmpl_id', '=', product_template_id.id)])
                        response_msg = "{0} Product Created".format(product_id.name)
                        self.create_shipstation_operation_details(product_operation_id, response_msg, True,
                                                                  'product')

                    if not product_id:
                        continue

                    quantity = order_line.get('quantity')
                    price = order_line.get('unitPrice')

                    for option in order_line.get('options'):
                        option_name += option.get('name') + ":" + option.get('value') + "\n"
                    if price < 0:
                        product_id = self.env.ref('shipstation_shipping_odoo_integration.shipstation_discount')
                    vals = {'product_id': product_id.id, 'price_unit': price, 'order_qty': quantity,
                            'order_id': order_id.id, 'description': product_name + "\n" + option_name,'product_uom':product_id.uom_id and product_id.uom_id.id,
                            'company_id': self.env.user.company_id.id}

                    order_line = self.sudo().create_sale_order_line_from_shipstation(vals)
                    if option_name:
                        order_line.update({'name': option_name})
                    self.env['sale.order.line'].sudo().create(order_line)
                if order_id.shipstation_store_id.add_vat_line:
                    vat_price = order.get('taxAmount', 0.0)
                    if vat_price > 0:
                        vat_product_id = self.env.ref('shipstation_shipping_odoo_integration.shipstation_vat')
                        taxline_vals = {'product_id': vat_product_id.id, 'price_unit': vat_price,
                                        'product_uom_qty': 1,
                                        'order_id': order_id.id, 'name': vat_product_id.name,
                                        'company_id': self.env.user.company_id.id
                                        }
                        self.env['sale.order.line'].sudo().create(taxline_vals)

                try:
                    # order_id.action_confirm()
                    print(order_id)
                except Exception as e:
                    continue
                self._cr.commit()
            else:
                message = "Shipstation Order ID : {0}, Shipstation Order Number : {1}, Order Is Not Created In Odoo Beacuse of Some Order Products Are Not Available In Odoo. Product Information : {2}".format(
                    shipstation_order_id, shipstation_order_number, product_error_message)
                self.create_shipstation_operation_details(operation_id, message, True, 'sale_order')
                self._cr.commit()
        else:
            message = "Order Is Already Exist {}".format(sale_order and sale_order.name)
            self.create_shipstation_operation_details(operation_id, message, True, 'sale_order')
            self._cr.commit()
    return product_datas


shipstation_store_vts.shipstation_order_managing_function = shipstation_order_managing_function


def create_sales_order_from_shipstation(self, vals):
    sale_order = self.env['sale.order']
    pricelist_id = self.env['product.pricelist'].search(
        [('id', '=', self.pricelist_id.id)])
    order_vals = {
        'company_id': vals.get('company_id'),
        'partner_id': vals.get('partner_id'),
        'partner_invoice_id': vals.get('partner_invoice_id'),
        'partner_shipping_id': vals.get('partner_shipping_id'),
        'warehouse_id': vals.get('warehouse_id'),
    }
    if self.partner_id:
        order_vals.update({'partner_id': self.partner_id.id,
                           'partner_shipping_id': vals.get('partner_id')})
    new_record = sale_order.new(order_vals)
    #new_record.onchange_partner_id()
    order_vals = sale_order._convert_to_write({name: new_record[name] for name in new_record._cache})
    new_record = sale_order.new(order_vals)
    #new_record.onchange_partner_shipping_id()
    order_vals = sale_order._convert_to_write({name: new_record[name] for name in new_record._cache})
    order_vals.update({
        'company_id': vals.get('company_id'),
        'picking_policy': 'direct',
        'partner_invoice_id': vals.get('partner_invoice_id'),
        'partner_shipping_id': vals.get('partner_shipping_id'),
        'partner_id': vals.get('partner_id'),
        'date_order': vals.get('date_order', ''),
        'state': 'draft',
        'carrier_id': vals.get('carrier_id', '')
    })
    if self.partner_id:
        order_vals.update({'partner_id': self.partner_id.id,
                           'partner_invoice_id': self.partner_id.id,
                           'partner_shipping_id': vals.get('partner_id')})
    return order_vals


shipstation_store_vts.create_sales_order_from_shipstation = create_sales_order_from_shipstation


class ShipstationStore(models.Model):
    _inherit = 'shipstation.store.vts'

    user_id = fields.Many2one('res.users', string='Sales Person')
    add_vat_line = fields.Boolean(string='Add VAT ?')
    carrier_id = fields.Many2one('delivery.carrier', string='Shipping Method')
    partner_id = fields.Many2one('res.partner', string='Parent Customer')
    create_multi_shipment = fields.Boolean(string='Create Multi Shipment?')
