# -*- coding: utf-8 -*-
{
    'name': 'Cargo Driver',
    'version': '18.0.1.0.0',
    'summary': 'Delivery driver profiles, location tracking, and status for Cargo',
    'description': """
Driver-specific domain module. Owns the cargo.driver profile and all
driver-facing REST endpoints.

Models:
  * cargo.driver — driver profile (vehicle, location, online status, rating)

REST endpoints:
  GET   /api/driver/profile
  PATCH /api/driver/profile
  POST  /api/driver/status      — go online / offline
  PATCH /api/driver/location    — update GPS coordinates
  GET   /api/driver/earnings    — today's earnings summary
""",
    'author': 'Cargo Marketplace',
    'category': 'Cargo/Driver',
    'depends': ['cargo_auth'],
    'data': [
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'views/cargo_driver_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
