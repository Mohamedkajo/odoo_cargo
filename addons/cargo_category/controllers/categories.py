# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
CargoCategoryController

Routes owned by cargo_category:

  GET /api/categories   — list all active cargo.store.category records
                          Used by the Flutter home-screen tab bar.
"""

import json
import logging

from odoo import http
from odoo.http import request

from cargo_base.constants import HTTP_200
from cargo_api.controllers.base import CargoBaseController

_logger = logging.getLogger(__name__)


class CargoCategoryController(CargoBaseController):

    @http.route(
        '/api/categories',
        auth='none',
        methods=['GET'],
        type='http',
        csrf=False,
        save_session=False,
    )
    def cargo_list_categories(self, **kwargs):
        """
        GET /api/categories

        Returns all active store categories ordered by sequence.
        No authentication required — public endpoint.
        """
        cats = request.env['cargo.store.category'].sudo().search([])
        return request.make_response(
            json.dumps([c.to_category_dict() for c in cats]),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )
