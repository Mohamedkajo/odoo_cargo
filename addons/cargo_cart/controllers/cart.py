# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
CargoCartController — Shopping cart endpoints for the Flutter Customer App.

Routes:
  GET    /api/cart                  — get current cart
  DELETE /api/cart                  — clear entire cart
  POST   /api/cart/items            — add item to cart
  PATCH  /api/cart/items/:itemId    — update item quantity
  DELETE /api/cart/items/:itemId    — remove item from cart
"""
import json
import logging

from odoo import http
from odoo.http import request

from cargo_base.constants import HTTP_200, HTTP_201, HTTP_400, HTTP_404, ERR_VALIDATION, ERR_NOT_FOUND
from cargo_api.controllers.base import CargoBaseController
from cargo_api.utils.decorators import require_cargo_auth

_logger = logging.getLogger(__name__)


def _json_body():
    try:
        raw = request.httprequest.get_data(as_text=True)
        return json.loads(raw) if raw else {}
    except Exception:
        return {}


class CargoCartController(CargoBaseController):

    @http.route(
        '/api/cart',
        auth='none',
        methods=['GET'],
        type='http',
        csrf=False,
        save_session=False,
    )
    @require_cargo_auth()
    def cargo_get_cart(self, **kwargs):
        """GET /api/cart — get the current user's cart."""
        user = request.cargo_user
        cart = request.env['cargo.cart'].sudo().get_or_create_for_user(user.id)
        return request.make_response(
            json.dumps(cart.to_cart_dict()),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )

    @http.route(
        '/api/cart',
        auth='none',
        methods=['DELETE'],
        type='http',
        csrf=False,
        save_session=False,
    )
    @require_cargo_auth()
    def cargo_clear_cart(self, **kwargs):
        """DELETE /api/cart — clear all items from the cart."""
        user = request.cargo_user
        cart = request.env['cargo.cart'].sudo().get_or_create_for_user(user.id)
        cart.clear()
        return request.make_response(
            json.dumps(cart.to_cart_dict()),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )

    @http.route(
        '/api/cart/items',
        auth='none',
        methods=['POST'],
        type='http',
        csrf=False,
        save_session=False,
    )
    @require_cargo_auth()
    def cargo_add_to_cart(self, **kwargs):
        """
        POST /api/cart/items

        Body: { productId, quantity, specialInstructions? }
        """
        user = request.cargo_user
        body = _json_body()

        product_id = body.get('productId')
        quantity   = body.get('quantity', 1)

        if not product_id:
            return request.make_response(
                json.dumps({'error': ERR_VALIDATION, 'message': 'productId is required.'}),
                status=HTTP_400,
                headers=[('Content-Type', 'application/json')],
            )
        try:
            quantity = max(1, int(quantity))
        except (ValueError, TypeError):
            quantity = 1

        # Load product
        product = request.env['cargo.product'].sudo().browse(int(product_id))
        if not product.exists() or not product.is_available:
            return request.make_response(
                json.dumps({'error': ERR_NOT_FOUND, 'message': 'Product not found or unavailable.'}),
                status=HTTP_404,
                headers=[('Content-Type', 'application/json')],
            )

        cart = request.env['cargo.cart'].sudo().get_or_create_for_user(user.id)

        # Check if same product already in cart
        existing_line = cart.line_ids.filtered(lambda l: l.product_id.id == product.id)
        if existing_line:
            existing_line[0].write({'quantity': existing_line[0].quantity + quantity})
        else:
            request.env['cargo.cart.line'].sudo().create({
                'cart_id':               cart.id,
                'product_id':            product.id,
                'name':                  product.name,
                'image':                 product.image,
                'price':                 product.price,
                'quantity':              quantity,
                'store_id':              product.store_id.id if product.store_id else False,
                'store_name':            product.store_name,
                'special_instructions':  body.get('specialInstructions'),
            })
            # Update cart's store reference
            if product.store_id:
                cart.write({
                    'store_id':   product.store_id.id,
                    'store_name': product.store_name,
                })

        # Reload
        cart.invalidate_recordset()
        return request.make_response(
            json.dumps(cart.to_cart_dict()),
            status=HTTP_201,
            headers=[('Content-Type', 'application/json')],
        )

    @http.route(
        '/api/cart/items/<int:item_id>',
        auth='none',
        methods=['PATCH'],
        type='http',
        csrf=False,
        save_session=False,
    )
    @require_cargo_auth()
    def cargo_update_cart_item(self, item_id, **kwargs):
        """
        PATCH /api/cart/items/:itemId

        Body: { quantity }  — if quantity <= 0 item is removed
        """
        user = request.cargo_user
        body = _json_body()

        try:
            quantity = int(body.get('quantity', 1))
        except (ValueError, TypeError):
            quantity = 1

        cart = request.env['cargo.cart'].sudo().get_or_create_for_user(user.id)
        line = request.env['cargo.cart.line'].sudo().browse(item_id)

        if not line.exists() or line.cart_id.id != cart.id:
            return request.make_response(
                json.dumps({'error': ERR_NOT_FOUND, 'message': 'Cart item not found.'}),
                status=HTTP_404,
                headers=[('Content-Type', 'application/json')],
            )

        if quantity <= 0:
            line.unlink()
        else:
            line.write({'quantity': quantity})

        cart.invalidate_recordset()
        return request.make_response(
            json.dumps(cart.to_cart_dict()),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )

    @http.route(
        '/api/cart/items/<int:item_id>',
        auth='none',
        methods=['DELETE'],
        type='http',
        csrf=False,
        save_session=False,
    )
    @require_cargo_auth()
    def cargo_remove_cart_item(self, item_id, **kwargs):
        """DELETE /api/cart/items/:itemId"""
        user = request.cargo_user
        cart = request.env['cargo.cart'].sudo().get_or_create_for_user(user.id)
        line = request.env['cargo.cart.line'].sudo().browse(item_id)

        if not line.exists() or line.cart_id.id != cart.id:
            return request.make_response(
                json.dumps({'error': ERR_NOT_FOUND, 'message': 'Cart item not found.'}),
                status=HTTP_404,
                headers=[('Content-Type', 'application/json')],
            )

        line.unlink()
        cart.invalidate_recordset()
        return request.make_response(
            json.dumps(cart.to_cart_dict()),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )
