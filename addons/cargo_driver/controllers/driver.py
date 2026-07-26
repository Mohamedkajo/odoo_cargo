# -*- coding: utf-8 -*-
"""CargoDriverController — Driver-facing REST endpoints."""
import json
import logging

from odoo import http, fields as odoo_fields
from odoo.http import request

from cargo_base.constants import HTTP_200, HTTP_201, HTTP_400, HTTP_404, ERR_VALIDATION, ERR_NOT_FOUND
from cargo_api.controllers.base import CargoBaseController
from cargo_api.utils.decorators import require_cargo_auth

_logger = logging.getLogger(__name__)


def _body():
    try:
        return json.loads(request.httprequest.get_data(as_text=True) or '{}')
    except Exception:
        return {}


def _ok(data, status=HTTP_200):
    return request.make_response(
        json.dumps(data), status=status,
        headers=[('Content-Type', 'application/json')],
    )


class CargoDriverController(CargoBaseController):

    def _get_driver(self, user_id):
        return request.env['cargo.driver'].sudo().search(
            [('user_id', '=', user_id)], limit=1
        )

    @http.route('/api/driver/profile', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth('driver', 'admin')
    def driver_get_profile(self, **kw):
        driver = self._get_driver(request.cargo_user.id)
        if not driver:
            return _ok({'error': ERR_NOT_FOUND, 'message': 'Driver profile not found.'}, HTTP_404)
        return _ok(driver.to_driver_dict())

    @http.route('/api/driver/profile', auth='none', methods=['PATCH'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth('driver', 'admin')
    def driver_update_profile(self, **kw):
        driver = self._get_driver(request.cargo_user.id)
        if not driver:
            return _ok({'error': ERR_NOT_FOUND, 'message': 'Driver profile not found.'}, HTTP_404)
        body = _body()
        vals = {}
        for api_key, model_key in [
            ('vehicleType', 'vehicle_type'), ('vehiclePlate', 'vehicle_plate'),
            ('vehicleColor', 'vehicle_color'),
        ]:
            if api_key in body:
                vals[model_key] = body[api_key]
        if vals:
            driver.write(vals)
        return _ok(driver.to_driver_dict())

    @http.route('/api/driver/status', auth='none', methods=['POST'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth('driver', 'admin')
    def driver_set_status(self, **kw):
        """POST /api/driver/status  body: { status: 'online'|'offline', lat?, lng? }"""
        body   = _body()
        driver = self._get_driver(request.cargo_user.id)
        if not driver:
            return _ok({'error': ERR_NOT_FOUND, 'message': 'Driver profile not found.'}, HTTP_404)
        status = body.get('status', 'online')
        if status == 'online':
            driver.set_online(
                lat=body.get('lat') and float(body['lat']),
                lng=body.get('lng') and float(body['lng']),
            )
        else:
            driver.set_offline()
        return _ok(driver.to_driver_dict())

    @http.route('/api/driver/location', auth='none', methods=['PATCH'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth('driver', 'admin')
    def driver_update_location(self, **kw):
        """PATCH /api/driver/location  body: { lat, lng }"""
        body   = _body()
        driver = self._get_driver(request.cargo_user.id)
        if not driver:
            return _ok({'error': ERR_NOT_FOUND, 'message': 'Driver profile not found.'}, HTTP_404)
        try:
            lat = float(body['lat'])
            lng = float(body['lng'])
        except (KeyError, TypeError, ValueError):
            return _ok({'error': ERR_VALIDATION, 'message': 'lat and lng are required numbers.'}, HTTP_400)
        driver.write({
            'current_lat': lat, 'current_lng': lng,
            'location_updated_at': odoo_fields.Datetime.now(),
        })
        return _ok({'lat': lat, 'lng': lng, 'updatedAt': driver.location_updated_at.isoformat()})

    @http.route('/api/driver/earnings', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth('driver', 'admin')
    def driver_earnings(self, **kw):
        """GET /api/driver/earnings — lifetime and today's earnings."""
        driver = self._get_driver(request.cargo_user.id)
        if not driver:
            return _ok({'error': ERR_NOT_FOUND, 'message': 'Driver profile not found.'}, HTTP_404)
        return _ok({
            'totalEarnings':     driver.total_earnings,
            'totalDeliveries':   driver.total_deliveries,
            'rating':            driver.rating,
        })
