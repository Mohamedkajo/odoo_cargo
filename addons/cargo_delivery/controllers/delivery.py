# -*- coding: utf-8 -*-
"""CargoDeliveryController — Delivery tracking and status endpoints."""
import json
import logging

from odoo import http
from odoo.http import request

from cargo_base.constants import HTTP_200, HTTP_400, HTTP_404, ERR_VALIDATION, ERR_NOT_FOUND
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


class CargoDeliveryController(CargoBaseController):

    @http.route('/api/orders/<int:order_id>/tracking', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth()
    def order_tracking(self, order_id, **kw):
        """GET /api/orders/:orderId/tracking — live delivery info for the customer."""
        user  = request.cargo_user
        order = request.env['cargo.order'].sudo().browse(order_id)
        if not order.exists() or order.user_id.id != user.id:
            return _ok({'error': ERR_NOT_FOUND, 'message': 'Order not found.'}, HTTP_404)

        delivery = request.env['cargo.delivery'].sudo().search(
            [('order_id', '=', order_id)], limit=1
        )
        if not delivery:
            return _ok({
                'deliveryId': None,
                'status': order.status,
                'driver': None,
                'etaMinutes': None,
            })
        return _ok(delivery.to_tracking_dict())

    @http.route('/api/deliveries/<int:delivery_id>', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth('driver', 'admin')
    def get_delivery(self, delivery_id, **kw):
        """GET /api/deliveries/:id — delivery detail for driver or admin."""
        delivery = request.env['cargo.delivery'].sudo().browse(delivery_id)
        if not delivery.exists():
            return _ok({'error': ERR_NOT_FOUND, 'message': 'Delivery not found.'}, HTTP_404)
        return _ok(delivery.to_tracking_dict())

    @http.route('/api/deliveries/<int:delivery_id>/status', auth='none', methods=['PATCH'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth('driver', 'admin')
    def update_delivery_status(self, delivery_id, **kw):
        """PATCH /api/deliveries/:id/status  body: { status, lat?, lng?, eta? }"""
        body     = _body()
        delivery = request.env['cargo.delivery'].sudo().browse(delivery_id)
        if not delivery.exists():
            return _ok({'error': ERR_NOT_FOUND, 'message': 'Delivery not found.'}, HTTP_404)

        new_status = body.get('status')
        if not new_status:
            return _ok({'error': ERR_VALIDATION, 'message': 'status is required.'}, HTTP_400)

        # Update live location if provided
        loc_vals = {}
        if body.get('lat'):
            loc_vals['driver_lat'] = float(body['lat'])
        if body.get('lng'):
            loc_vals['driver_lng'] = float(body['lng'])
        if body.get('eta'):
            loc_vals['eta_minutes'] = int(body['eta'])
        if loc_vals:
            delivery.write(loc_vals)

        try:
            delivery.advance_status(new_status)
        except ValueError as exc:
            return _ok({'error': ERR_VALIDATION, 'message': str(exc)}, HTTP_400)

        return _ok(delivery.to_tracking_dict())
