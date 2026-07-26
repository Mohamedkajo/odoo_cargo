# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
CargoCartController — Shopping cart REST endpoints.

Cart lines reference product.template (native Odoo model) via cargo.cart.line.product_id.
When a product from a different store is added, the cart is cleared first to
enforce single-store ordering (common in food delivery apps).

Routes:
  GET    /api/cart              — get current user's cart
  POST   /api/cart/items        — add item to cart
  PATCH  /api/cart/items/:id    — update quantity
  DELETE /api/cart/items/:id    — remove item
  DELETE /api/cart              — clear entire cart
  POST   /api/cart/coupon       — apply coupon
  DELETE /api/cart/coupon       — remove coupon
"""
import json
import logging

from odoo import http
from odoo.http import request

from odoo.addons.cargo_base.constants import HTTP_200, HTTP_201, HTTP_400, HTTP_404, ERR_VALIDATION, ERR_NOT_FOUND
from odoo.addons.cargo_api.controllers.base import CargoBaseController
from odoo.addons.cargo_api.utils.decorators import require_cargo_auth

_logger = logging.getLogger(__name__)


def _ok(data, status=HTTP_200):
    return request.make_response(
        json.dumps(data), status=status,
        headers=[('Content-Type', 'application/json')],
    )


def _err(code, msg, status=HTTP_400):
    return _ok({'error': code, 'message': msg}, status)


def _json_body():
    try:
        return json.loads(request.httprequest.get_data(as_text=True) or '{}')
    except Exception:
        return {}


class CargoCartController(CargoBaseController):

    @http.route('/api/cart', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth()
    def cargo_get_cart(self, **kwargs):
        """GET /api/cart — return the current user's cart."""
        user = request.cargo_user
        cart = request.env['cargo.cart'].sudo().get_or_create_for_user(user.id)
        return _ok(cart.to_cart_dict())

    @http.route('/api/cart/items', auth='none', methods=['POST'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth()
    def cargo_add_to_cart(self, **kwargs):
        """POST /api/cart/items — add a product.template item to the cart."""
        user    = request.cargo_user
        body    = _json_body()
        prod_id = body.get('productId')
        qty     = int(body.get('quantity', 1))
        if not prod_id or qty < 1:
            return _err(ERR_VALIDATION, 'productId and quantity >= 1 are required.')

        product = request.env['product.template'].sudo().browse(int(prod_id))
        if not product.exists() or not product.cargo_store_id:
            return _err(ERR_NOT_FOUND, 'Product not found.', HTTP_404)

        cart = request.env['cargo.cart'].sudo().get_or_create_for_user(user.id)

        # Enforce single-store cart
        if cart.store_id and cart.store_id.id != product.cargo_store_id.id:
            # Different store: clear cart first
            cart.clear()

        # Check for existing line with same product
        existing = cart.line_ids.filtered(lambda l: l.product_id.id == product.id)
        if existing:
            existing[:1].write({'quantity': existing[:1].quantity + qty})
        else:
            cart.sudo().write({
                'store_id':   product.cargo_store_id.id,
                'store_name': product.cargo_store_id.name,
                'line_ids': [(0, 0, {
                    'product_id': product.id,
                    'name':       product.name,
                    'price':      product.cargo_effective_price or product.list_price,
                    'quantity':   qty,
                    'image':      product.cargo_image_url,
                    'store_id':   product.cargo_store_id.id,
                    'store_name': product.cargo_store_id.name,
                })],
            })

        return _ok(cart.to_cart_dict(), HTTP_201)

    @http.route('/api/cart/items/<int:line_id>', auth='none', methods=['PATCH'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth()
    def cargo_update_cart_item(self, line_id, **kwargs):
        """PATCH /api/cart/items/:id — update item quantity."""
        user = request.cargo_user
        body = _json_body()
        qty  = body.get('quantity')
        if qty is None or int(qty) < 1:
            return _err(ERR_VALIDATION, 'quantity must be >= 1.')

        cart = request.env['cargo.cart'].sudo().search([('user_id', '=', user.id)], limit=1)
        if not cart:
            return _err(ERR_NOT_FOUND, 'Cart not found.', HTTP_404)

        line = cart.line_ids.filtered(lambda l: l.id == line_id)
        if not line:
            return _err(ERR_NOT_FOUND, 'Cart item not found.', HTTP_404)

        line[:1].write({'quantity': int(qty)})
        return _ok(cart.to_cart_dict())

    @http.route('/api/cart/items/<int:line_id>', auth='none', methods=['DELETE'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth()
    def cargo_remove_cart_item(self, line_id, **kwargs):
        """DELETE /api/cart/items/:id — remove an item from the cart."""
        user = request.cargo_user
        cart = request.env['cargo.cart'].sudo().search([('user_id', '=', user.id)], limit=1)
        if not cart:
            return _err(ERR_NOT_FOUND, 'Cart not found.', HTTP_404)

        line = cart.line_ids.filtered(lambda l: l.id == line_id)
        if line:
            line.unlink()
        return _ok(cart.to_cart_dict())

    @http.route('/api/cart', auth='none', methods=['DELETE'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth()
    def cargo_clear_cart(self, **kwargs):
        """DELETE /api/cart — clear the entire cart."""
        user = request.cargo_user
        cart = request.env['cargo.cart'].sudo().search([('user_id', '=', user.id)], limit=1)
        if cart:
            cart.clear()
        return _ok({'message': 'Cart cleared.'})

    @http.route('/api/cart/coupon', auth='none', methods=['POST'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth()
    def cargo_apply_coupon(self, **kwargs):
        """POST /api/cart/coupon — { "code": "SUMMER10" }"""
        user = request.cargo_user
        body = _json_body()
        code = (body.get('code') or '').strip().upper()
        if not code:
            return _err(ERR_VALIDATION, 'Coupon code is required.')

        cart = request.env['cargo.cart'].sudo().get_or_create_for_user(user.id)
        subtotal = sum(l.price * l.quantity for l in cart.line_ids)

        try:
            result = request.env['cargo.coupon'].sudo().validate_and_apply(
                code, subtotal, user.id, cart.store_id.id if cart.store_id else None,
            )
        except Exception as exc:
            return _err('ERR_COUPON', str(exc))

        cart.write({
            'coupon_code':   code,
            'discount':      result['discount'],
            'delivery_fee':  0.0 if result['deliveryWaived'] else cart.delivery_fee,
        })
        return _ok(cart.to_cart_dict())

    @http.route('/api/cart/coupon', auth='none', methods=['DELETE'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth()
    def cargo_remove_coupon(self, **kwargs):
        """DELETE /api/cart/coupon — remove applied coupon."""
        user = request.cargo_user
        cart = request.env['cargo.cart'].sudo().search([('user_id', '=', user.id)], limit=1)
        if cart:
            cart.write({'coupon_code': False, 'discount': 0.0})
        return _ok(cart.to_cart_dict() if cart else {})
