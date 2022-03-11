# -*- coding: utf-8 -*-
from odoo import http

# class MethodHrLre(http.Controller):
#     @http.route('/method_hr_lre/method_hr_lre/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/method_hr_lre/method_hr_lre/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('method_hr_lre.listing', {
#             'root': '/method_hr_lre/method_hr_lre',
#             'objects': http.request.env['method_hr_lre.method_hr_lre'].search([]),
#         })

#     @http.route('/method_hr_lre/method_hr_lre/objects/<model("method_hr_lre.method_hr_lre"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('method_hr_lre.object', {
#             'object': obj
#         })