# -*- coding: utf-8 -*-
{
    'name': 'Cargo Reports',
    'version': '18.0.1.0.0',
    'summary': 'Analytics, revenue reports, and admin statistics for Cargo Marketplace',
    'description': """
Analytics and reporting domain. Provides:
  * Odoo backend pivot/graph views over orders, revenue, and top stores
  * Admin REST endpoint for dashboard statistics

No new persistent models — all data is aggregated from existing records.

REST endpoints:
  GET /api/admin/reports/summary   — key platform metrics
  GET /api/admin/reports/orders    — orders grouped by date/status
""",
    'author': 'Cargo Marketplace',
    'category': 'Cargo/Reports',
    'depends': ['cargo_order', 'cargo_wallet', 'cargo_store'],
    'data': [
        'security/ir.model.access.csv',
        'views/cargo_reports_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
