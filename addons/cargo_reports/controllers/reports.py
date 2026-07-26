# -*- coding: utf-8 -*-
"""CargoReportsController — Admin analytics endpoints."""
import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta

from odoo import http
from odoo.http import request

from cargo_base.constants import HTTP_200
from cargo_api.controllers.base import CargoBaseController
from cargo_api.utils.decorators import require_cargo_auth

_logger = logging.getLogger(__name__)


def _ok(data, status=HTTP_200):
    return request.make_response(
        json.dumps(data), status=status,
        headers=[('Content-Type', 'application/json')],
    )


class CargoReportsController(CargoBaseController):

    @http.route('/api/admin/reports/summary', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth('admin')
    def admin_summary(self, **kw):
        """GET /api/admin/reports/summary — key platform metrics."""
        env = request.env

        orders       = env['cargo.order'].sudo().search([])
        stores       = env['cargo.store'].sudo().search([('active', '=', True)])
        users        = env['res.users'].sudo().search([('cargo_role', '=', 'customer')])
        wallets      = env['cargo.wallet'].sudo().search([]) if 'cargo.wallet' in env else []
        total_wallet = sum(w.balance for w in wallets) if wallets else 0.0

        delivered  = [o for o in orders if o.status == 'delivered']
        cancelled  = [o for o in orders if o.status == 'cancelled']
        revenue    = sum(o.total for o in delivered)

        return _ok({
            'totalOrders':      len(orders),
            'deliveredOrders':  len(delivered),
            'cancelledOrders':  len(cancelled),
            'totalRevenue':     revenue,
            'totalStores':      len(stores),
            'totalCustomers':   len(users),
            'totalWalletFunds': total_wallet,
        })

    @http.route('/api/admin/reports/orders', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth('admin')
    def orders_by_date(self, **kw):
        """GET /api/admin/reports/orders?days=30 — orders grouped by day."""
        try:
            days = int(request.httprequest.args.get('days', 30))
        except (TypeError, ValueError):
            days = 30

        cutoff = datetime.utcnow() - timedelta(days=days)
        orders = request.env['cargo.order'].sudo().search(
            [('create_date', '>=', cutoff.isoformat())]
        )

        by_day = defaultdict(lambda: {'count': 0, 'revenue': 0.0})
        for o in orders:
            day = o.create_date.strftime('%Y-%m-%d') if o.create_date else 'unknown'
            by_day[day]['count'] += 1
            if o.status == 'delivered':
                by_day[day]['revenue'] += o.total

        series = sorted(
            [{'date': d, **v} for d, v in by_day.items()],
            key=lambda x: x['date'],
        )
        return _ok({'days': days, 'series': series})
