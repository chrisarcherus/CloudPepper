from odoo import api, models, _


class ProductSales(models.AbstractModel):
    _name = 'report.bluemax_product_sales_report.product_sales'
    _description = "Report Product Sales"

    @api.model
    def _get_report_values(self, docids, data=None):
        if self.env.context.get('product_sales_pdf_report'):
            if data.get('report_data'):
                data.update(
                    {'account_data': data.get('report_data')['product_report_lines'][0],
                     'Filters': data.get('report_data')['filters'],
                     'company': self.env.company,
                     'total': data.get('report_data')['product_report_lines'][2],

                     })

        return data
