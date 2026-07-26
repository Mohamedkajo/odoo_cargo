# -*- coding: utf-8 -*-
{
    'name': 'Cargo Marketplace',
    'version': '18.0.1.0.0',
    'summary': 'Meta-module: installs and configures the full Cargo Marketplace platform',
    'description': """
Convenience meta-module that declares all other Cargo modules as
dependencies so a single install brings up the complete platform.

Also owns:
  * cargo.marketplace.settings — singleton with platform-wide configuration
    (commission rate, support email/phone, maintenance mode, etc.)

REST endpoints:
  GET /api/settings   — public platform config (name, support, fees)
""",
    'author': 'Cargo Marketplace',
    'category': 'Cargo/Marketplace',
    'depends': [
        'cargo_base',
        'cargo_api',
        'cargo_auth',
        'cargo_category',
        'cargo_store',
        'cargo_vendor',
        'cargo_driver',
        'cargo_product',
        'cargo_inventory',
        'cargo_cart',
        'cargo_order',
        'cargo_delivery',
        'cargo_delivery_zone',
        'cargo_wallet',
        'cargo_coupon',
        'cargo_review',
        'cargo_notification',
        'cargo_reports',
        'cargo_dashboard',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/cargo_marketplace_data.xml',
        'views/cargo_marketplace_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
