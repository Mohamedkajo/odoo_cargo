# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo.reports — Pre-aggregated report queries against native Odoo models.

All queries run against sale.order (native), product.template (native),
cargo.store and res.users (driver) — no custom order or product models.

The controller calls these model methods and returns JSON to the dashboard.
"""
import logging
from datetime import datetime, timedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class CargoReports(models.AbstractModel):
    _name = 'cargo.reports'
    _description = 'Cargo Reporting Engine'

    # ── Order statistics ──────────────────────────────────────────────────────

    @api.model
    def get_order_stats(self, store_ids=None, days=30) -> dict:
        """
        Aggregate order stats for the given store_ids over the last N days.

        Returns:
          totalOrders, totalRevenue, avgOrderValue, deliveredCount, cancelledCount
        """
        since  = datetime.utcnow() - timedelta(days=days)
        domain = [
            ('cargo_status', '!=', False),
            ('date_order',   '>=', since),
        ]
        if store_ids:
            domain.append(('cargo_store_id', 'in', store_ids))

        orders       = self.env['sale.order'].sudo().search(domain)
        delivered    = orders.filtered(lambda o: o.cargo_status == 'delivered')
        cancelled    = orders.filtered(lambda o: o.cargo_status == 'cancelled')
        total_rev    = sum(o.amount_total for o in delivered)
        avg_val      = total_rev / len(delivered) if delivered else 0.0

        return {
            'totalOrders':     len(orders),
            'totalRevenue':    round(total_rev, 2),
            'avgOrderValue':   round(avg_val, 2),
            'deliveredCount':  len(delivered),
            'cancelledCount':  len(cancelled),
            'periodDays':      days,
        }

    @api.model
    def get_daily_revenue(self, store_ids=None, days=30) -> list:
        """Daily revenue breakdown for the last N days."""
        since  = datetime.utcnow() - timedelta(days=days)
        domain = [
            ('cargo_status', '=', 'delivered'),
            ('date_order',   '>=', since),
        ]
        if store_ids:
            domain.append(('cargo_store_id', 'in', store_ids))

        orders = self.env['sale.order'].sudo().search(domain, order='date_order asc')
        revenue_by_day = {}
        for order in orders:
            day = order.date_order.strftime('%Y-%m-%d')
            revenue_by_day[day] = revenue_by_day.get(day, 0.0) + order.amount_total

        return [{'date': k, 'revenue': round(v, 2)} for k, v in sorted(revenue_by_day.items())]

    # ── Product performance ───────────────────────────────────────────────────

    @api.model
    def get_top_products(self, store_ids=None, limit=10, days=30) -> list:
        """Top-selling products (by quantity sold) in the last N days."""
        since  = datetime.utcnow() - timedelta(days=days)
        domain = [
            ('order_id.cargo_status', '=', 'delivered'),
            ('order_id.date_order',   '>=', since),
        ]
        if store_ids:
            domain.append(('order_id.cargo_store_id', 'in', store_ids))

        lines = self.env['sale.order.line'].sudo().search(domain)
        product_stats = {}
        for line in lines:
            pid  = line.product_id.product_tmpl_id.id
            name = line.product_id.product_tmpl_id.name
            if pid not in product_stats:
                product_stats[pid] = {'productId': pid, 'name': name, 'totalQty': 0, 'totalRevenue': 0.0}
            product_stats[pid]['totalQty']     += int(line.product_uom_qty)
            product_stats[pid]['totalRevenue'] += line.price_subtotal

        ranked = sorted(product_stats.values(), key=lambda x: x['totalQty'], reverse=True)
        return ranked[:limit]

    # ── Store performance ─────────────────────────────────────────────────────

    @api.model
    def get_store_performance(self, days=30) -> list:
        """Revenue and order count per store for the last N days."""
        since  = datetime.utcnow() - timedelta(days=days)
        domain = [
            ('cargo_status', '=', 'delivered'),
            ('date_order',   '>=', since),
            ('cargo_store_id', '!=', False),
        ]
        orders = self.env['sale.order'].sudo().search(domain)
        store_stats = {}
        for order in orders:
            sid  = order.cargo_store_id.id
            name = order.cargo_store_id.name
            if sid not in store_stats:
                store_stats[sid] = {
                    'storeId': sid, 'storeName': name,
                    'orderCount': 0, 'revenue': 0.0,
                }
            store_stats[sid]['orderCount'] += 1
            store_stats[sid]['revenue']    += order.amount_total

        return sorted(store_stats.values(), key=lambda x: x['revenue'], reverse=True)

    # ── Driver performance ────────────────────────────────────────────────────

    @api.model
    def get_driver_performance(self, days=30) -> list:
        """Driver stats: deliveries and earnings for the last N days."""
        since = datetime.utcnow() - timedelta(days=days)
        deliveries = self.env['cargo.delivery'].sudo().search([
            ('status',       '=', 'delivered'),
            ('delivered_at', '>=', since),
            ('driver_id',    '!=', False),
        ])
        driver_stats = {}
        for d in deliveries:
            uid  = d.driver_id.id
            name = d.driver_id.name
            if uid not in driver_stats:
                driver_stats[uid] = {
                    'driverId': uid, 'driverName': name,
                    'deliveries': 0, 'earnings': 0.0,
                }
            driver_stats[uid]['deliveries'] += 1
            driver_stats[uid]['earnings']   += d.order_id.cargo_delivery_fee or 0

        return sorted(driver_stats.values(), key=lambda x: x['deliveries'], reverse=True)
