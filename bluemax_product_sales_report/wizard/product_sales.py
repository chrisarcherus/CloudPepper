import json
import time
import io
from datetime import date, timedelta

from odoo import fields, models, api, _
from odoo.tools import float_is_zero
from odoo.exceptions import UserError

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class ProductSalesReportWizard(models.TransientModel):
    _name = 'account.product.sales.wizard'
    _description = 'Account Product Sales Wizard'

    def _get_date_from(self):
        first_day_of_current_month = date.today().replace(day=1)
        last_day_of_previous_month = first_day_of_current_month - \
            timedelta(days=1)
        first_day_of_previous_month = last_day_of_previous_month.replace(day=1)
        return first_day_of_previous_month

    def _get_date_to(self):
        first_day_of_current_month = date.today().replace(day=1)
        last_day_of_previous_month = first_day_of_current_month - \
            timedelta(days=1)
        return last_day_of_previous_month

    date_from = fields.Date(string='Start Date', default=_get_date_from)
    date_to = fields.Date(string='End Date', default=_get_date_to)
    product_ids = fields.Many2many('product.product', string='Products')
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, default=lambda self: self.env.company)
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')
    default_code = fields.Char("Internal Reference Filter")

    def create_sales_report(self):
        productSalesList = []
        domain = [('move_type', '=', 'out_invoice')]
        if self.company_id:
            domain += [('company_id', '=', self.company_id.id)]
        if self.date_from:
            domain += [('date', '>=', self.date_from)]
        if self.date_to:
            domain += [('date', '<=', self.date_to)]
        if self.target_move and self.target_move == 'posted':
            domain += [('parent_state', '=', 'posted')]
        if self.product_ids:
            domain += [('product_id', 'in', self.product_ids.ids)]
        if self.default_code:
            domain += [('product_id.default_code', 'like', self.default_code)]

        moveLines = self.env['account.move.line'].sudo().search(domain)
        if not moveLines:
            raise UserError(_("No records found."))

        for line in moveLines.filtered(lambda x: x.product_id):
            costPrice = line.product_id.standard_price * line.quantity
            grossProfit = line.price_subtotal - costPrice

            same_product_lines = line.move_id.invoice_line_ids.filtered(
                lambda x: x.product_id.id == line.product_id.id and x.price_subtotal == line.price_subtotal
            )
            if same_product_lines:
                data = {
                    'product_id': line.product_id.id,
                    'internal_reference': line.product_id.default_code or '',
                    'location': line.move_id.location_id.name or '',
                    'move_id': line.move_id.id,
                    'customer': line.move_id.partner_id.id,
                    'invoice_date': line.date,
                    'invoice_quantity': line.quantity,
                    # 'list_price': line.product_id.lst_price,
                    # 'standard_price': line.product_id.standard_price,
                    'amount': line.price_subtotal,
                    'cost': costPrice,
                    'gross_profit': grossProfit,
                    'gross_profit_margin': round(grossProfit / line.price_subtotal * 100, 2) if line.price_subtotal > 0 else 0,
                    'user_id': line.move_id.invoice_user_id.id,
                    'company_id': line.company_id.id,
                    'currency_id': line.currency_id.id,
                }
                productSales = self.env['account.product.sales'].sudo().create(
                    data)
                productSalesList.append(productSales.id)

        if self.date_from and self.date_to:
            name = 'Sales Inventory Report Of ' + \
                str(self.date_from.strftime('%m-%d-%Y')) + \
                ' To ' + str(self.date_to.strftime('%m-%d-%Y'))
        elif self.date_from:
            name = 'Sales Inventory Report Of ' + \
                str(self.date_from.strftime('%m-%d-%Y'))
        elif self.date_to:
            name = 'Sales Inventory Report Of ' + \
                str(self.date_to.strftime('%m-%d-%Y'))
        else:
            name = 'Sales Inventory Report'

        return {
            'name': _(name),
            'view_mode': 'tree',
            'res_model': 'account.product.sales',
            'views': [(self.env.ref('bluemax_product_sales_report.view_account_product_sales_tree').id, 'tree')],
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', productSalesList)],
            'target': 'current',
            # 'res_id': wizard.id,
            # 'context': context,
            'context': {'group_by': 'product_id'}
        }


class ProductSalesReport(models.TransientModel):
    _name = 'account.product.sales'
    _description = 'Account Product Sales'

    product_id = fields.Many2one('product.product', string='Product')
    internal_reference = fields.Char(string='Internal Reference')
    location = fields.Char(string="Location")
    move_id = fields.Many2one('account.move', string='Invoice')
    invoice_date = fields.Date(string='Invoice Date')
    invoice_quantity = fields.Float(string='QTY')
    # list_price = fields.Monetary(string="Price EA")
    # standard_price = fields.Monetary(string="Cost EA")
    amount = fields.Monetary(string="Total Sale")
    cost = fields.Monetary(string="Total Cost")
    gross_profit = fields.Monetary(string="GP (Price)")
    gross_profit_margin = fields.Float(string="GP (%)")
    customer = fields.Many2one('res.partner', string="Customer")
    user_id = fields.Many2one('res.users', string='Salesperson')
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id', depends=[
                                  "company_id"], store=True, precompute=True, ondelete="restrict")

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(ProductSalesReport, self).read_group(
            domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy
        )
        product_sales = self.env['account.product.sales']
        for line in res:
            if '__domain' in line:
                product_sales = self.search(line['__domain'])
            if 'gross_profit' in fields and 'amount' in fields:
                total_gross_profit = sum(product_sales.mapped('gross_profit'))
                total_amount = sum(product_sales.mapped('amount'))

                line['gross_profit_margin'] = (
                    total_gross_profit / total_amount * 100
                ) if total_amount != 0 else 0
        return res
