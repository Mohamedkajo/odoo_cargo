# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
CargoDriverController — Driver profile, status and location REST endpoints.

Driver data lives on res.users (extended by cargo_driver with cargo_driver_*
fields).  All endpoints require cargo_role = 'driver'.

Routes:
  GET   /api/driver/profile     — driver profile from res.users
  PATCH /api/driver/profile     — update vehicle details
  POST  /api/driver/status      — go online / offline
  PATCH /api/driver/location    — update GPS coordinates
  GET   /api/driver/earnings    — today's earnings summary
  GET   /api/driver/orders      — assigned orders (sale.order via cargo_delivery)
"""
import json
import logging
from datetime import datetime, timezone

from odoo import http
from odoo.http import request

from cargo_base.constants import HTTP_200, HTTP_400
from cargo_api.controllers.base import CargoBaseController
from cargo_api.utils.decorators import require_cargo_auth

_logger = logging.getLogger(__name__)


def _ok(data, status=HTTP_200):
    return request.make_response(
        json.dumps(data),
        status=status,
        headers=[('Content-Type', 'application/json')],
    )


def _err(code, msg, status=HTTP_400):
    return _ok({'error': code, 'message': msg}, status)


def _json_body():
    try:
        return json.loads(request.httprequest.get_data(as_text=True) or '{}')
    except Exception:
        return {}


class CargoDriverController(CargoBaseController):

    @http.route('/api/driver/profile', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth(roles=['driver'])
    def cargo_driver_profile(self, **kwargs):
        """GET /api/driver/profile — full driver profile."""
        return _ok(request.cargo_user.cargo_driver_to_api_dict())

    @http.route('/api/driver/profile', auth='none', methods=['PATCH'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth(roles=['driver'])
    def cargo_driver_update_profile(self, **kwargs):
        """PATCH /api/driver/profile — update vehicle details."""
        user = request.cargo_user
        body = _json_body()
        updatable = {
            'vehicleType':  'cargo_driver_vehicle_type',
            'vehiclePlate': 'cargo_driver_vehicle_plate',
            'vehicleColor': 'cargo_driver_vehicle_color',
            'vehicleYear':  'cargo_driver_vehicle_year',
        }
        vals = {odoo_f: body[app_f] for app_f, odoo_f in updatable.items() if app_f in body}
        if vals:
            user.sudo().write(vals)
        return _ok({'message': 'Profile updated.'})

    @http.route('/api/driver/status', auth='none', methods=['POST'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth(roles=['driver'])
    def cargo_driver_status(self, **kwargs):
        """POST /api/driver/status — { "online": true/false, "lat": N, "lng": N }"""
        user    = request.cargo_user
        body    = _json_body()
        online  = bool(body.get('online', True))
        lat     = body.get('lat') or None
        lng     = body.get('lng') or None
        if online:
            user.cargo_driver_go_online(lat=lat, lng=lng)
        else:
            user.cargo_driver_go_offline()
        return _ok({'isOnline': user.cargo_driver_is_online})

    @http.route('/api/driver/location', auth='none', methods=['PATCH'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth(roles=['driver'])
    def cargo_driver_location(self, **kwargs):
        """PATCH /api/driver/location — { "lat": N, "lng": N }"""
        user = request.cargo_user
        body = _json_body()
        try:
            lat = float(body['lat'])
            lng = float(body['lng'])
        except (KeyError, TypeError, ValueError):
            return _err('ERR_VALIDATION', 'lat and lng are required floats.')
        user.cargo_driver_update_location(lat, lng)

        # Also update any active delivery records linked to this driver
        active_deliveries = request.env['cargo.delivery'].sudo().search([
            ('driver_id', '=', user.id),
            ('status', 'in', ['assigned', 'picked_up', 'on_the_way']),
        ])
        if active_deliveries:
            active_deliveries.write({'driver_lat': lat, 'driver_lng': lng})

        return _ok({'lat': lat, 'lng': lng, 'updatedAt': datetime.now(timezone.utc).isoformat()})

    @http.route('/api/driver/earnings', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth(roles=['driver'])
    def cargo_driver_earnings(self, **kwargs):
        """GET /api/driver/earnings — today's delivery stats."""
        user  = request.cargo_user
        today = datetime.now(timezone.utc).date().isoformat()

        deliveries_today = request.env['cargo.delivery'].sudo().search([
            ('driver_id', '=', user.id),
            ('status',    '=', 'delivered'),
            ('delivered_at', '>=', today),
        ])
        earnings_today = sum(
            d.order_id.cargo_delivery_fee or 0
            for d in deliveries_today
            if d.order_id
        )
        return _ok({
            'totalDeliveries':  user.cargo_driver_total_deliveries,
            'totalEarnings':    user.cargo_driver_total_earnings,
            'deliveriesToday':  len(deliveries_today),
            'earningsToday':    earnings_today,
            'rating':           user.cargo_driver_rating,
        })

    @http.route('/api/driver/orders', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth(roles=['driver'])
    def cargo_driver_orders(self, **kwargs):
        """GET /api/driver/orders — orders currently assigned to this driver."""
        user = request.cargo_user
        deliveries = request.env['cargo.delivery'].sudo().search([
            ('driver_id', '=', user.id),
            ('status', 'not in', ['delivered', 'failed']),
        ], order='create_date desc', limit=20)
        return _ok([d.to_delivery_dict() for d in deliveries])
