# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
CargoOrderController — Order management endpoints for the Flutter Customer App.

All order operations run against sale.order (native Odoo model) extended by
cargo_base with cargo_status, and by cargo_order with delivery address,
payment method, discount and coupon code.

Routes:
  GET  /api/orders              — list my orders (sale.order records)
  POST /api/orders              — place order from cart
  GET  /api/orders/:orderId     — order detail + timeline
  POST /api/orders/:orderId/cancel   — cancel order
  GET  /api/orders/:orderId/tracking — live tracking data
"""
import json
import logging

from odoo import http
from odoo.http import request

from odoo.addons.cargo_base.constants import (
    HTTP_200, HTTP_201, HTTP_400, HTTP_403, HTTP_404,
    ERR_VALIDATION, ERR_NOT_FOUND, ERR_PERMISSION,
    ORDER_STATUS_CONFIRMED,
)
from odoo.addons.cargo_api.controllers.base import CargoBaseController
from odoo.addons.cargo_api.utils.decorators import require_cargo_auth

_logger = logging.getLogger(__name__)

# Domain fragment that identifies Cargo orders (as opposed to regular sales orders)
_CARGO_ORDER_DOMAIN = [('cargo_status', '!=', False)]


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


def _ok(data, status=HTTP_200):
    return request.make_response(
        json.dumps(data),
        status=status,
        headers=[('Content-Type', 'application/json')],
    )


def _err(code, msg, status):
    return _ok({'error': code, 'message': msg}, status)


class CargoOrderController(CargoBaseController):

    @http.route(
        '/api/orders',
        auth='none', methods=['GET'],
        type='http', csrf=False, save_session=False,
    )
    @require_cargo_auth()
    def cargo_list_orders(self, **kwargs):
        """GET /api/orders — list this customer's orders, newest first."""
        user          = request.cargo_user
        limit, offset = _page_params()
        domain = _CARGO_ORDER_DOMAIN + [('partner_id', '=', user.partner_id.id)]

        orders = request.env['sale.order'].sudo().search(
            domain, order='id desc', limit=limit, offset=offset,
        )
        total = request.env['sale.order'].sudo().search_count(domain)
        return _ok({'data': [o.cargo_to_api_dict() for o in orders], 'total': total})

    @http.route(
        '/api/orders',
        auth='none', methods=['POST'],
        type='http', csrf=False, save_session=False,
    )
    @require_cargo_auth()
    def cargo_place_order(self, **kwargs):
        """
        POST /api/orders

        Body: { paymentMethod, deliveryAddress }
        Reads the current cart, creates a sale.order, clears the cart.
        """
        user             = request.cargo_user
        body             = _json_body()
        payment_method   = body.get('paymentMethod', 'cash')
        delivery_address = (body.get('deliveryAddress') or '').strip()

        if not delivery_address:
            return _err(ERR_VALIDATION, 'deliveryAddress is required.', HTTP_400)

        # Load cart
        cart = request.env['cargo.cart'].sudo().search(
            [('user_id', '=', user.id)], limit=1,
        )
        if not cart or not cart.line_ids:
            return _err(ERR_VALIDATION, 'Cart is empty.', HTTP_400)

        # Build sale.order
        order_vals = {
            'partner_id':           user.partner_id.id,
            'cargo_status':         ORDER_STATUS_CONFIRMED,
            'cargo_store_id':       cart.store_id.id if cart.store_id else False,
            'cargo_delivery_fee':   cart.delivery_fee or 15.0,
            'cargo_discount':       cart.discount or 0.0,
            'cargo_payment_method': payment_method,
            'cargo_delivery_address': delivery_address,
            'cargo_coupon_code':    cart.coupon_code or False,
        }
        order = request.env['sale.order'].sudo().create(order_vals)

        # Create order lines from cart lines
        for cart_line in cart.line_ids:
            # product.template → get the default product.product (first variant)
            tmpl = cart_line.product_id  # product.template
            product = tmpl.product_variant_ids[:1] if tmpl else None
            if not product:
                continue
            order.sudo().write({
                'order_line': [(0, 0, {
                    'product_id':      product.id,
                    'name':            cart_line.name or product.name,
                    'product_uom_qty': cart_line.quantity,
                    'price_unit':      cart_line.price,
                    'product_uom':     product.uom_id.id,
                })]
            })

        # Clear the cart
        cart.clear()

        return _ok(order.cargo_to_api_dict(), HTTP_201)

    @http.route(
        '/api/orders/<int:order_id>',
        auth='none', methods=['GET'],
        type='http', csrf=False, save_session=False,
    )
    @require_cargo_auth()
    def cargo_get_order(self, order_id, **kwargs):
        """GET /api/orders/:orderId"""
        user  = request.cargo_user
        order = request.env['sale.order'].sudo().browse(order_id)
        if not order.exists() or not order.cargo_status:
            return _err(ERR_NOT_FOUND, 'Order not found.', HTTP_404)
        if order.partner_id.id != user.partner_id.id:
            return _err(ERR_PERMISSION, 'Access denied.', HTTP_403)
        return _ok(order.cargo_to_api_detail_dict())

    @http.route(
        '/api/orders/<int:order_id>/cancel',
        auth='none', methods=['POST'],
        type='http', csrf=False, save_session=False,
    )
    @require_cargo_auth()
    def cargo_cancel_order(self, order_id, **kwargs):
        """POST /api/orders/:orderId/cancel"""
        user  = request.cargo_user
        order = request.env['sale.order'].sudo().browse(order_id)
        if not order.exists() or not order.cargo_status:
            return _err(ERR_NOT_FOUND, 'Order not found.', HTTP_404)
        if order.partner_id.id != user.partner_id.id:
            return _err(ERR_PERMISSION, 'Access denied.', HTTP_403)
        try:
            order.cargo_transition_status('cancelled')
        except Exception as exc:
            return _err('ERR_CANCEL', str(exc), HTTP_400)
        return _ok(order.cargo_to_api_dict())

    @http.route(
        '/api/orders/<int:order_id>/tracking',
        auth='none', methods=['GET'],
        type='http', csrf=False, save_session=False,
    )
    @require_cargo_auth()
    def cargo_order_tracking(self, order_id, **kwargs):
        """GET /api/orders/:orderId/tracking"""
        user  = request.cargo_user
        order = request.env['sale.order'].sudo().browse(order_id)
        if not order.exists() or not order.cargo_status:
            return _err(ERR_NOT_FOUND, 'Order not found.', HTTP_404)
        if order.partner_id.id != user.partner_id.id:
            return _err(ERR_PERMISSION, 'Access denied.', HTTP_403)

        # Look up driver GPS if available
        driver_lat, driver_lng = None, None
        driver_user = None
        if order.cargo_driver_id:
            driver_user = request.env['res.users'].sudo().browse(order.cargo_driver_id)
            if driver_user.exists():
                driver_lat = driver_user.cargo_driver_current_lat or None
                driver_lng = driver_user.cargo_driver_current_lng or None

        tracking = {
            'orderId':         order.id,
            'status':          order.cargo_status,
            'eta':             f'{order.cargo_estimated_time} Min' if order.cargo_estimated_time else '30 Min',
            'driverName':      order.cargo_driver_name or None,
            'driverPhone':     order.cargo_driver_phone or None,
            'driverAvatar':    None,
            'driverRating':    order.cargo_driver_rating or 0.0,
            'driverLat':       driver_lat,
            'driverLng':       driver_lng,
            'storeAddress':    order.cargo_store_id.address if order.cargo_store_id else None,
            'deliveryAddress': order.cargo_delivery_address,
            'timeline':        order.cargo_to_api_detail_dict().get('timeline', []),
        }
        return _ok(tracking)
