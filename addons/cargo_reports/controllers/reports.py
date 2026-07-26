# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""CargoReportsController — Admin analytics endpoints.

All ORM queries use native Odoo models:
  sale.order (with cargo_status) instead of cargo.order
  product.template instead of cargo.product
  res.users instead of cargo.driver
"""
import json
import logging
from datetime import datetime, timedelta

from odoo import http
from odoo.http import request

from odoo.addons.cargo_base.constants import HTTP_200
from odoo.addons.cargo_api.controllers.base import CargoBaseController
from odoo.addons.cargo_api.utils.decorators import require_cargo_auth

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

        # sale.order with cargo_status = Cargo delivery orders
        orders    = env['sale.order'].sudo().search([('cargo_status', '!=', False)])
        stores    = env['cargo.store'].sudo().search([('active', '=', True)])
        customers = env['res.users'].sudo().search([('cargo_role', '=', 'customer')])
        drivers   = env['res.users'].sudo().search([('cargo_role', '=', 'driver')])

        delivered = orders.filtered(lambda o: o.cargo_status == 'delivered')
        cancelled = orders.filtered(lambda o: o.cargo_status == 'cancelled')
        revenue   = sum(o.amount_total for o in delivered)

        # Total wallet funds held by customers
        total_wallet = sum(
            u.cargo_wallet_balance
            for u in customers
            if hasattr(u, 'cargo_wallet_balance')
        )

        return _ok({
            'totalOrders':      len(orders),
            'deliveredOrders':  len(delivered),
            'cancelledOrders':  len(cancelled),
            'totalRevenue':     round(revenue, 2),
            'totalStores':      len(stores),
            'totalCustomers':   len(customers),
            'totalDrivers':     len(drivers),
            'totalWalletFunds': round(total_wallet, 2),
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

        stats = request.env['cargo.reports'].sudo().get_order_stats(days=days)
        daily = request.env['cargo.reports'].sudo().get_daily_revenue(days=days)
        return _ok({'stats': stats, 'series': daily})

    @http.route('/api/admin/reports/stores', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth('admin')
    def store_performance(self, **kw):
        """GET /api/admin/reports/stores — revenue per store."""
        try:
            days = int(request.httprequest.args.get('days', 30))
        except (TypeError, ValueError):
            days = 30
        data = request.env['cargo.reports'].sudo().get_store_performance(days=days)
        return _ok(data)

    @http.route('/api/admin/reports/products', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth('admin')
    def top_products(self, **kw):
        """GET /api/admin/reports/products — top-selling products."""
        try:
            days  = int(request.httprequest.args.get('days', 30))
            limit = int(request.httprequest.args.get('limit', 10))
        except (TypeError, ValueError):
            days, limit = 30, 10
        data = request.env['cargo.reports'].sudo().get_top_products(limit=limit, days=days)
        return _ok(data)

    @http.route('/api/admin/reports/drivers', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth('admin')
    def driver_performance(self, **kw):
        """GET /api/admin/reports/drivers — deliveries + earnings per driver."""
        try:
            days = int(request.httprequest.args.get('days', 30))
        except (TypeError, ValueError):
            days = 30
        data = request.env['cargo.reports'].sudo().get_driver_performance(days=days)
        return _ok(data)
