# -*- coding: utf-8 -*-
"""CargoVendorController — Vendor profile and registration endpoints."""
import json
import logging

from odoo import http
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


class CargoVendorController(CargoBaseController):

    @http.route('/api/vendor/register', auth='none', methods=['POST'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth()
    def vendor_register(self, **kw):
        """POST /api/vendor/register — create a vendor profile for the current user."""
        user = request.cargo_user
        body = _body()
        business_name = (body.get('businessName') or '').strip()
        if not business_name:
            return _ok({'error': ERR_VALIDATION, 'message': 'businessName is required.'}, HTTP_400)

        existing = request.env['cargo.vendor'].sudo().search(
            [('user_id', '=', user.id)], limit=1
        )
        if existing:
            return _ok(existing.to_vendor_dict())

        vendor = request.env['cargo.vendor'].sudo().create({
            'user_id':       user.id,
            'business_name': business_name,
            'tax_number':    body.get('taxNumber'),
            'bank_account':  body.get('bankAccount'),
        })
        return _ok(vendor.to_vendor_dict(), HTTP_201)

    @http.route('/api/vendor/profile', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth('vendor', 'admin')
    def vendor_get_profile(self, **kw):
        """GET /api/vendor/profile"""
        user   = request.cargo_user
        vendor = request.env['cargo.vendor'].sudo().search(
            [('user_id', '=', user.id)], limit=1
        )
        if not vendor:
            return _ok({'error': ERR_NOT_FOUND, 'message': 'Vendor profile not found.'}, HTTP_404)
        return _ok(vendor.to_vendor_dict())

    @http.route('/api/vendor/profile', auth='none', methods=['PATCH'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth('vendor', 'admin')
    def vendor_update_profile(self, **kw):
        """PATCH /api/vendor/profile"""
        user   = request.cargo_user
        vendor = request.env['cargo.vendor'].sudo().search(
            [('user_id', '=', user.id)], limit=1
        )
        if not vendor:
            return _ok({'error': ERR_NOT_FOUND, 'message': 'Vendor profile not found.'}, HTTP_404)
        body = _body()
        vals = {}
        if 'businessName' in body:
            vals['business_name'] = body['businessName']
        if 'taxNumber' in body:
            vals['tax_number'] = body['taxNumber']
        if 'bankAccount' in body:
            vals['bank_account'] = body['bankAccount']
        if vals:
            vendor.write(vals)
        return _ok(vendor.to_vendor_dict())

    @http.route('/api/vendor/stats', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth('vendor', 'admin')
    def vendor_stats(self, **kw):
        """GET /api/vendor/stats — basic order and revenue stats for the vendor."""
        user   = request.cargo_user
        vendor = request.env['cargo.vendor'].sudo().search(
            [('user_id', '=', user.id)], limit=1
        )
        store_ids = vendor.store_ids.ids if vendor else []
        orders = request.env['cargo.order'].sudo().search(
            [('store_id', 'in', store_ids)]
        ) if store_ids else request.env['cargo.order'].sudo().browse([])
        revenue = sum(o.total for o in orders)
        return _ok({
            'storeCount':  len(store_ids),
            'orderCount':  len(orders),
            'totalRevenue': revenue,
        })
