# -*- coding: utf-8 -*-

from odoo import models, fields


class ChatGPTTags(models.TransientModel):
    _name = 'wr.chatgpt.tags'
    _description = 'wr.chatgpt.tags'
    _rec_name = 'name'
    _order = 'id desc'

    name = fields.Char(string="Name")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
