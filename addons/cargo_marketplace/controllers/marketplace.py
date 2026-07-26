# -*- coding: utf-8 -*-
"""CargoMarketplaceController — Public platform settings endpoint."""
import json
import logging

from odoo import http
from odoo.http import request

from cargo_base.constants import HTTP_200
from cargo_api.controllers.base import CargoBaseController

_logger = logging.getLogger(__name__)


class CargoMarketplaceController(CargoBaseController):

    @http.route('/api/settings', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    def public_settings(self, **kw):
        """GET /api/settings — public platform configuration for the Flutter app."""
        settings = request.env['cargo.marketplace.settings'].sudo().get_settings()
        return request.make_response(
            json.dumps(settings.to_public_dict()),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )
