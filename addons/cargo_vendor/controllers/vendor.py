# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
CargoVendorController — Vendor profile and registration REST endpoints.

Vendor data lives on res.partner (extended by cargo_vendor with cargo_vendor_*
fields).  Each res.users has a partner_id; vendor users have cargo_role='vendor'.

Routes:
  GET   /api/vendor/profile   — current vendor's profile
  PATCH /api/vendor/profile   — update business details
  GET   /api/vendor/stats     — sales statistics for the vendor's stores
  POST  /api/vendor/register  — submit vendor application
"""
import json
import logging

from odoo import http
from odoo.http import request

from cargo_base.constants import HTTP_200, HTTP_201, HTTP_400, HTTP_403, HTTP_404, ERR_PERMISSION
from cargo_api.controllers.base import CargoBaseController
from cargo_api.utils.decorators import require_cargo_auth

_logger = logging.getLogger(__name__)


def _ok(data, status=HTTP_200):
    return request.make_response(
        json.dumps(data),
        status=status,
        headers=[('Content-Type', 'application/json')],
    )


def _err(code, msg, status):
    return _ok({'error': code, 'message': msg}, status)


def _json_body():
    try:
        return json.loads(request.httprequest.get_data(as_text=True) or '{}')
    except Exception:
        return {}


class CargoVendorController(CargoBaseController):

    @http.route('/api/vendor/profile', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth(roles=['vendor'])
    def cargo_vendor_profile(self, **kwargs):
        """GET /api/vendor/profile — vendor profile from res.partner."""
        user    = request.cargo_user
        partner = user.partner_id
        return _ok({
            'id':             user.id,
            'name':           user.name,
            'email':          user.login,
            'phone':          partner.phone,
            'businessName':   partner.cargo_vendor_business_name,
            'taxNumber':      partner.cargo_vendor_tax_number,
            'commissionRate': partner.cargo_vendor_commission_rate,
            'isApproved':     partner.cargo_vendor_is_approved,
            'storeCount':     partner.cargo_vendor_store_count,
        })

    @http.route('/api/vendor/profile', auth='none', methods=['PATCH'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth(roles=['vendor'])
    def cargo_vendor_update_profile(self, **kwargs):
        """PATCH /api/vendor/profile — update vendor business details."""
        user    = request.cargo_user
        partner = user.partner_id
        body    = _json_body()

        updatable = {
            'businessName':  'cargo_vendor_business_name',
            'taxNumber':     'cargo_vendor_tax_number',
            'bankAccount':   'cargo_vendor_bank_account',
            'phone':         'phone',
        }
        vals = {}
        for app_key, odoo_field in updatable.items():
            if app_key in body:
                vals[odoo_field] = body[app_key]

        if vals:
            partner.sudo().write(vals)
        return _ok({'message': 'Profile updated.', 'updated': list(vals.keys())})

    @http.route('/api/vendor/stats', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth(roles=['vendor'])
    def cargo_vendor_stats(self, **kwargs):
        """GET /api/vendor/stats — aggregated order stats for the vendor's stores."""
        user   = request.cargo_user
        stores = request.env['cargo.store'].sudo().search([('vendor_id', '=', user.id)])
        store_ids = stores.ids

        orders = request.env['sale.order'].sudo().search([
            ('cargo_store_id', 'in', store_ids),
            ('cargo_status', 'not in', ['cancelled']),
        ])

        total_orders   = len(orders)
        total_revenue  = sum(o.amount_total for o in orders)
        pending_orders = len(orders.filtered(lambda o: o.cargo_status not in [
            'delivered', 'cancelled'
        ]))

        return _ok({
            'totalOrders':   total_orders,
            'totalRevenue':  total_revenue,
            'pendingOrders': pending_orders,
            'storeCount':    len(stores),
        })

    @http.route('/api/vendor/register', auth='none', methods=['POST'],
                type='http', csrf=False, save_session=False)
    def cargo_vendor_register(self, **kwargs):
        """POST /api/vendor/register — submit a vendor application (no auth required)."""
        body = _json_body()
        required = ['name', 'email', 'password', 'businessName']
        missing  = [f for f in required if not body.get(f)]
        if missing:
            return _err('ERR_VALIDATION',
                        f'Missing fields: {", ".join(missing)}', HTTP_400)

        # Create user (inactive until admin approves)
        try:
            user = request.env['res.users'].sudo().create({
                'name':          body['name'],
                'login':         body['email'],
                'password':      body['password'],
                'cargo_role':    'vendor',
                'active':        False,   # approved by admin
                'groups_id':     [(4, request.env.ref('base.group_user').id)],
            })
            user.partner_id.sudo().write({
                'email':                        body['email'],
                'phone':                        body.get('phone', ''),
                'cargo_vendor_business_name':   body['businessName'],
                'cargo_vendor_tax_number':      body.get('taxNumber', ''),
                'cargo_vendor_is_approved':     False,
                'cargo_role':                   'vendor',
            })
        except Exception as exc:
            _logger.exception('Vendor registration failed')
            return _err('ERR_REGISTER', str(exc), HTTP_400)

        return _ok({'message': 'Application submitted. Pending admin approval.'}, HTTP_201)
