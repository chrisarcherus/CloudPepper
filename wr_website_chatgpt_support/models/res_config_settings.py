# -*- coding: utf-8 -*-

import ast

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    wr_chatgpt_tags_ids = fields.Many2many('wr.chatgpt.tags', string="CharGPT Tags")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        wr_chatgpt_tags_ids = params.get_param('wr_chatgpt_tags_ids', default='[]')
        res.update(wr_chatgpt_tags_ids=[(6, 0, ast.literal_eval(wr_chatgpt_tags_ids))])
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("wr_chatgpt_tags_ids", self.wr_chatgpt_tags_ids.ids)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
