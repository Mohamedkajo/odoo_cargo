# -*- coding: utf-8 -*-
"""CargoInventoryController — Vendor stock management endpoints."""
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


class CargoInventoryController(CargoBaseController):

    @http.route('/api/vendor/inventory', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth('vendor', 'admin')
    def vendor_inventory(self, **kw):
        """GET /api/vendor/inventory — stock list for the vendor's stores."""
        user      = request.cargo_user
        store_ids = request.env['cargo.store'].sudo().search(
            [('vendor_id', '=', user.id)]
        ).ids
        if not store_ids:
            return _ok({'data': [], 'total': 0})

        inv_lines = request.env['cargo.inventory'].sudo().search(
            [('store_id', 'in', store_ids)]
        )
        return _ok({'data': [i.to_inventory_dict() for i in inv_lines], 'total': len(inv_lines)})

    @http.route('/api/vendor/inventory/<int:inv_id>', auth='none', methods=['PATCH'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth('vendor', 'admin')
    def update_inventory(self, inv_id, **kw):
        """PATCH /api/vendor/inventory/:id  body: { quantity?, delta?, alertQty? }"""
        user = request.cargo_user
        inv  = request.env['cargo.inventory'].sudo().browse(inv_id)
        if not inv.exists():
            return _ok({'error': ERR_NOT_FOUND, 'message': 'Inventory record not found.'}, HTTP_404)
        # Ownership check
        if inv.store_id.vendor_id.id != user.id:
            return _ok({'error': 'ERR_FORBIDDEN', 'message': 'Access denied.'}, 403)

        body = _body()
        if 'delta' in body:
            try:
                inv.adjust(int(body['delta']))
            except (TypeError, ValueError):
                return _ok({'error': ERR_VALIDATION, 'message': 'delta must be an integer.'}, HTTP_400)
        elif 'quantity' in body:
            try:
                inv.write({'quantity': max(0, int(body['quantity']))})
            except (TypeError, ValueError):
                return _ok({'error': ERR_VALIDATION, 'message': 'quantity must be an integer.'}, HTTP_400)
        if 'alertQty' in body:
            try:
                inv.write({'alert_qty': max(0, int(body['alertQty']))})
            except (TypeError, ValueError):
                pass
        return _ok(inv.to_inventory_dict())
