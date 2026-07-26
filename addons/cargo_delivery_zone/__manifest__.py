# -*- coding: utf-8 -*-
{
    'name': 'Cargo Delivery Zone',
    'version': '18.0.1.0.0',
    'summary': 'Geographic delivery zones and fee configuration for Cargo Marketplace',
    'description': """
Defines delivery coverage areas (zones) with per-zone delivery fees,
minimum order amounts, and store assignments.

Models:
  * cargo.delivery.zone — named zone with city, fees, and linked stores

REST endpoints:
  GET  /api/delivery-zones           — list active zones
  POST /api/delivery-zones/check     — find zone for given coordinates
""",
    'author': 'Cargo Marketplace',
    'category': 'Cargo/Delivery',
    'depends': ['cargo_store'],
    'data': [
        'security/ir.model.access.csv',
        'data/cargo_delivery_zone_data.xml',
        'views/cargo_delivery_zone_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
