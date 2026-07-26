# -*- coding: utf-8 -*-
"""CargoCouponController — Coupon validation and application endpoints."""
import json
import logging

from odoo import http
from odoo.http import request

from odoo.addons.cargo_base.constants import HTTP_200, HTTP_400, HTTP_404, ERR_VALIDATION, ERR_NOT_FOUND
from odoo.addons.cargo_api.controllers.base import CargoBaseController
from odoo.addons.cargo_api.utils.decorators import require_cargo_auth

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


class CargoCouponController(CargoBaseController):

    @http.route('/api/coupons/validate', auth='none', methods=['POST'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth()
    def validate_coupon(self, **kw):
        """POST /api/coupons/validate  body: { code, cartTotal, storeId? }"""
        user = request.cargo_user
        body = _body()
        code = (body.get('code') or '').strip().upper()
        if not code:
            return _ok({'error': ERR_VALIDATION, 'message': 'code is required.'}, HTTP_400)
        try:
            cart_total = float(body.get('cartTotal', 0))
        except (TypeError, ValueError):
            return _ok({'error': ERR_VALIDATION, 'message': 'cartTotal must be a number.'}, HTTP_400)

        coupon = request.env['cargo.coupon'].sudo().search([('code', '=', code)], limit=1)
        if not coupon:
            return _ok({'error': ERR_NOT_FOUND, 'message': 'Coupon code not found.'}, HTTP_404)

        result = coupon.validate_for_cart(
            user_id=user.id,
            cart_subtotal=cart_total,
            store_id=body.get('storeId'),
        )
        return _ok(result)

    @http.route('/api/coupons/apply', auth='none', methods=['POST'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth()
    def apply_coupon(self, **kw):
        """POST /api/coupons/apply  body: { code, cartTotal, storeId? }"""
        user = request.cargo_user
        body = _body()
        code = (body.get('code') or '').strip().upper()
        if not code:
            return _ok({'error': ERR_VALIDATION, 'message': 'code is required.'}, HTTP_400)

        coupon = request.env['cargo.coupon'].sudo().search([('code', '=', code)], limit=1)
        if not coupon:
            return _ok({'error': ERR_NOT_FOUND, 'message': 'Coupon code not found.'}, HTTP_404)

        try:
            cart_total = float(body.get('cartTotal', 0))
        except (TypeError, ValueError):
            return _ok({'error': ERR_VALIDATION, 'message': 'cartTotal must be a number.'}, HTTP_400)

        result = coupon.validate_for_cart(user.id, cart_total, body.get('storeId'))
        if not result['valid']:
            return _ok({'error': ERR_VALIDATION, 'message': result['reason']}, HTTP_400)

        # Record application (full redemption happens at order creation)
        return _ok({
            'applied':         True,
            'couponCode':      coupon.code,
            'discountType':    coupon.type,
            'discountValue':   coupon.discount_value,
            'discountAmount':  result['discountAmount'],
        })
