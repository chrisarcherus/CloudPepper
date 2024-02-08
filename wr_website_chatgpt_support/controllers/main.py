# -*- coding: utf-8 -*-

import ast

from markupsafe import Markup
from odoo import http, release
from odoo.addons.iap.tools import iap_tools
from odoo.exceptions import AccessError
from odoo.http import request

DEFAULT_LIBRARY_ENDPOINT = 'https://media-api.odoo.com'
DEFAULT_OLG_ENDPOINT = 'https://olg.api.odoo.com'


class WebsiteChatGPTSupport(http.Controller):

    @http.route("/chatgpt/support", type='http', auth="user", website=True)
    def chatgpt_support(self, **kw):
        return request.render('wr_website_chatgpt_support.website_chatgpt_support_view')

    @http.route("/chatgpt/search_prompt", type='http', auth="user", website=True)
    def chatgpt_search_prompt(self, **kw):
        print("\n kw >>>>>>>> ", kw)
        vals = {}
        try:
            IrConfigParameter = request.env['ir.config_parameter'].sudo()
            olg_api_endpoint = IrConfigParameter.get_param('web_editor.olg_api_endpoint', DEFAULT_OLG_ENDPOINT)
            prompt = kw.get('prompt')
            tags = ''
            wr_chatgpt_tags_ids = IrConfigParameter.get_param('wr_chatgpt_tags_ids', default='[]')
            wr_chatgpt_tags_ids = ast.literal_eval(wr_chatgpt_tags_ids)
            print("\n\n wr_chatgpt_tags_ids >>>>>>> ", wr_chatgpt_tags_ids)
            if wr_chatgpt_tags_ids:
                wr_chatgpt_tags_ids = request.env['wr.chatgpt.tags'].sudo().browse(wr_chatgpt_tags_ids)
                if wr_chatgpt_tags_ids:
                    tags = ' '.join([wr_chatgpt_tags_id.name for wr_chatgpt_tags_id in wr_chatgpt_tags_ids])
            if prompt:
                prompt = "%s %s %s %s" % (prompt, kw.get('txt_odoo_version'), kw.get('txt_ent_comm'), tags)
            print("\n\n prompt >>>>>>>> ", prompt)
            response = iap_tools.iap_jsonrpc(olg_api_endpoint + "/api/olg/1/chat", params={
                'prompt': prompt,
                'conversation_history': [],
                'version': release.version,
            }, timeout=30)
            if response['status'] == 'success':
                vals = {'success': True, 'message': 'Success',
                        'text': Markup(response['content'].replace('\n', '</br>'))}
                print("\n\n vals >>>>> ", vals)
            elif response['status'] == 'error_prompt_too_long':
                vals = {'success': True, 'message': 'Sorry, your prompt is too long. Try to say it in fewer words.'}
            else:
                vals = {'success': True, 'message': 'Sorry, we could not generate a response. Please try again later.'}
        except AccessError:
            vals = {'success': True, 'message': 'Oops, it looks like our AI is unreachable!'}
        finally:
            return request.render('wr_website_chatgpt_support.website_chatgpt_support_view', vals)

    # @http.route("/llm/generate_text", type="json", auth="user")
    # def generate_text(self, params):
    #     try:
    #         IrConfigParameter = request.env['ir.config_parameter'].sudo()
    #         olg_api_endpoint = IrConfigParameter.get_param('web_editor.olg_api_endpoint', DEFAULT_OLG_ENDPOINT)
    #         response = iap_tools.iap_jsonrpc(olg_api_endpoint + "/api/olg/1/chat", params={
    #             'prompt': prompt,
    #             'conversation_history': [],
    #             'version': release.version,
    #         }, timeout=30)
    #         if response['status'] == 'success':
    #             return {'success': True, 'message': 'Success', 'text': response['content']}
    #         elif response['status'] == 'error_prompt_too_long':
    #             return {'success': True, 'message': 'Sorry, your prompt is too long. Try to say it in fewer words.'}
    #         else:
    #             return {'success': True, 'message': 'Sorry, we could not generate a response. Please try again later.'}
    #     except AccessError:
    #         return {'success': True, 'message': 'Oops, it looks like our AI is unreachable!'}
