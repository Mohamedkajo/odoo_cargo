# -*- coding: utf-8 -*-
"""CargoDeliveryZoneController — Zone listing and coordinate check."""
import json
import logging

from odoo import http
from odoo.http import request

from odoo.addons.cargo_base.constants import HTTP_200, HTTP_400, ERR_VALIDATION
from odoo.addons.cargo_api.controllers.base import CargoBaseController
from odoo.addons.cargo_delivery_zone.models.cargo_delivery_zone import CargoDeliveryZone

_logger = logging.getLogger(__name__)


def _ok(data, status=HTTP_200):
    return request.make_response(
        json.dumps(data), status=status,
        headers=[('Content-Type', 'application/json')],
    )


class CargoDeliveryZoneController(CargoBaseController):

    @http.route('/api/delivery-zones', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    def list_zones(self, **kw):
        """GET /api/delivery-zones — list active delivery zones."""
        zones = request.env['cargo.delivery.zone'].sudo().search([('is_active', '=', True)])
        return _ok([z.to_zone_dict() for z in zones])

    @http.route('/api/delivery-zones/check', auth='none', methods=['POST'],
                type='http', csrf=False, save_session=False)
    def check_zone(self, **kw):
        """POST /api/delivery-zones/check  body: { lat, lng }"""
        try:
            body = json.loads(request.httprequest.get_data(as_text=True) or '{}')
            lat  = float(body['lat'])
            lng  = float(body['lng'])
        except (KeyError, TypeError, ValueError):
            return _ok({'error': ERR_VALIDATION, 'message': 'lat and lng are required numbers.'}, HTTP_400)

        zone = CargoDeliveryZone.find_for_coordinates(request.env, lat, lng)
        if not zone:
            return _ok({'covered': False, 'zone': None})
        return _ok({'covered': True, 'zone': zone.to_zone_dict()})
