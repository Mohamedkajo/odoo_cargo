# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
CargoOrderController — Order management endpoints for the Flutter Customer App.

Routes:
  GET  /api/orders              — list my orders
  POST /api/orders              — place order from cart
  GET  /api/orders/:orderId     — order detail + timeline
  POST /api/orders/:orderId/cancel   — cancel order
  GET  /api/orders/:orderId/tracking — live tracking data
"""
import json
import logging

from odoo import fields as odoo_fields
from odoo import http
from odoo.http import request

from cargo_base.constants import (
    HTTP_200, HTTP_201, HTTP_400, HTTP_403, HTTP_404,
    ERR_VALIDATION, ERR_NOT_FOUND, ERR_PERMISSION,
)
from cargo_api.controllers.base import CargoBaseController
from cargo_api.utils.decorators import require_cargo_auth

_logger = logging.getLogger(__name__)


def _json_body():
    try:
        raw = request.httprequest.get_data(as_text=True)
        return json.loads(raw) if raw else {}
    except Exception:
        return {}


def _page_params():
    try:
        limit  = max(1, min(int(request.httprequest.args.get('limit', 20)), 100))
        offset = max(0, int(request.httprequest.args.get('offset', 0)))
    except (TypeError, ValueError):
        limit, offset = 20, 0
    return limit, offset


class CargoOrderController(CargoBaseController):

    @http.route(
        '/api/orders',
        auth='none',
        methods=['GET'],
        type='http',
        csrf=False,
        save_session=False,
    )
    @require_cargo_auth()
    def cargo_list_orders(self, **kwargs):
        """GET /api/orders — list this user's orders, newest first."""
        user = request.cargo_user
        limit, offset = _page_params()

        orders = request.env['cargo.order'].sudo().search(
            [('user_id', '=', user.id)],
            order='id desc',
            limit=limit,
            offset=offset,
        )
        total = request.env['cargo.order'].sudo().search_count([('user_id', '=', user.id)])

        data = [o.to_order_dict() for o in orders]
        return request.make_response(
            json.dumps({'data': data, 'total': total}),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )

    @http.route(
        '/api/orders',
        auth='none',
        methods=['POST'],
        type='http',
        csrf=False,
        save_session=False,
    )
    @require_cargo_auth()
    def cargo_place_order(self, **kwargs):
        """
        POST /api/orders

        Body: { paymentMethod, deliveryAddress }
        Reads the current cart, creates an order, clears the cart.
        """
        user = request.cargo_user
        body = _json_body()

        payment_method   = body.get('paymentMethod', 'cash')
        delivery_address = (body.get('deliveryAddress') or '').strip()

        if not delivery_address:
            return request.make_response(
                json.dumps({'error': ERR_VALIDATION, 'message': 'deliveryAddress is required.'}),
                status=HTTP_400,
                headers=[('Content-Type', 'application/json')],
            )

        # Load cart
        cart = request.env['cargo.cart'].sudo().search([('user_id', '=', user.id)], limit=1)
        if not cart or not cart.line_ids:
            return request.make_response(
                json.dumps({'error': ERR_VALIDATION, 'message': 'Cart is empty.'}),
                status=HTTP_400,
                headers=[('Content-Type', 'application/json')],
            )

        subtotal     = sum(l.price * l.quantity for l in cart.line_ids)
        delivery_fee = cart.delivery_fee or 15.0
        discount     = cart.discount or 0.0
        total        = subtotal + delivery_fee - discount

        # Create order
        order = request.env['cargo.order'].sudo().create({
            'user_id':          user.id,
            'store_id':         cart.store_id.id if cart.store_id else False,
            'store_name':       cart.store_name or (cart.store_id.name if cart.store_id else None),
            'store_image':      cart.store_id.image if cart.store_id else None,
            'subtotal':         subtotal,
            'delivery_fee':     delivery_fee,
            'discount':         discount,
            'total':            total,
            'payment_method':   payment_method,
            'delivery_address': delivery_address,
            'item_count':       len(cart.line_ids),
            'coupon_code':      cart.coupon_code,
        })

        # Create order lines from cart lines
        for line in cart.line_ids:
            request.env['cargo.order.line'].sudo().create({
                'order_id':   order.id,
                'product_id': line.product_id.id if line.product_id else False,
                'name':       line.name,
                'image':      line.image,
                'price':      line.price,
                'quantity':   line.quantity,
            })

        # Clear the cart
        cart.clear()

        return request.make_response(
            json.dumps(order.to_order_dict()),
            status=HTTP_201,
            headers=[('Content-Type', 'application/json')],
        )

    @http.route(
        '/api/orders/<int:order_id>',
        auth='none',
        methods=['GET'],
        type='http',
        csrf=False,
        save_session=False,
    )
    @require_cargo_auth()
    def cargo_get_order(self, order_id, **kwargs):
        """GET /api/orders/:orderId"""
        user = request.cargo_user
        order = request.env['cargo.order'].sudo().browse(order_id)
        if not order.exists():
            return request.make_response(
                json.dumps({'error': ERR_NOT_FOUND, 'message': 'Order not found.'}),
                status=HTTP_404,
                headers=[('Content-Type', 'application/json')],
            )
        if order.user_id.id != user.id:
            return request.make_response(
                json.dumps({'error': ERR_PERMISSION, 'message': 'Access denied.'}),
                status=HTTP_403,
                headers=[('Content-Type', 'application/json')],
            )
        return request.make_response(
            json.dumps(order.to_order_detail_dict()),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )

    @http.route(
        '/api/orders/<int:order_id>/cancel',
        auth='none',
        methods=['POST'],
        type='http',
        csrf=False,
        save_session=False,
    )
    @require_cargo_auth()
    def cargo_cancel_order(self, order_id, **kwargs):
        """POST /api/orders/:orderId/cancel"""
        user = request.cargo_user
        order = request.env['cargo.order'].sudo().browse(order_id)
        if not order.exists():
            return request.make_response(
                json.dumps({'error': ERR_NOT_FOUND, 'message': 'Order not found.'}),
                status=HTTP_404,
                headers=[('Content-Type', 'application/json')],
            )
        if order.user_id.id != user.id:
            return request.make_response(
                json.dumps({'error': ERR_PERMISSION, 'message': 'Access denied.'}),
                status=HTTP_403,
                headers=[('Content-Type', 'application/json')],
            )
        try:
            order.action_cancel()
        except Exception as exc:
            return request.make_response(
                json.dumps({'error': 'ERR_CANCEL', 'message': str(exc)}),
                status=HTTP_400,
                headers=[('Content-Type', 'application/json')],
            )
        return request.make_response(
            json.dumps(order.to_order_dict()),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )

    @http.route(
        '/api/orders/<int:order_id>/tracking',
        auth='none',
        methods=['GET'],
        type='http',
        csrf=False,
        save_session=False,
    )
    @require_cargo_auth()
    def cargo_order_tracking(self, order_id, **kwargs):
        """GET /api/orders/:orderId/tracking"""
        user = request.cargo_user
        order = request.env['cargo.order'].sudo().browse(order_id)
        if not order.exists():
            return request.make_response(
                json.dumps({'error': ERR_NOT_FOUND, 'message': 'Order not found.'}),
                status=HTTP_404,
                headers=[('Content-Type', 'application/json')],
            )
        if order.user_id.id != user.id:
            return request.make_response(
                json.dumps({'error': ERR_PERMISSION, 'message': 'Access denied.'}),
                status=HTTP_403,
                headers=[('Content-Type', 'application/json')],
            )

        tracking = {
            'orderId':         order.id,
            'status':          order.status,
            'eta':             order.estimated_time or '15 Min',
            'driverName':      order.driver_name or None,
            'driverPhone':     order.driver_phone or None,
            'driverAvatar':    None,
            'driverRating':    order.driver_rating or 0.0,
            'driverLat':       None,
            'driverLng':       None,
            'storeAddress':    order.store_id.address if order.store_id else None,
            'deliveryAddress': order.delivery_address,
            'timeline':        order.to_order_detail_dict().get('timeline', []),
        }
        return request.make_response(
            json.dumps(tracking),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )
