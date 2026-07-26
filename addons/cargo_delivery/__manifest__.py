# -*- coding: utf-8 -*-
{
    'name': 'Cargo Delivery',
    'version': '18.0.1.0.0',
    'summary': 'Driver assignment, OTP handshake, and live delivery tracking for Cargo',
    'description': """
Owns the delivery lifecycle for each order: driver assignment, pickup/delivery
OTP codes, live location relay, and status transitions from picked-up to delivered.

Models:
  * cargo.delivery — one record per order; links order ↔ driver

REST endpoints:
  GET   /api/orders/:id/tracking   — live tracking for customer
  GET   /api/deliveries/:id        — delivery detail for admin/driver
  PATCH /api/deliveries/:id/status — advance delivery status (driver app)
""",
    'author': 'Cargo Marketplace',
    'category': 'Cargo/Delivery',
    'depends': ['cargo_order', 'cargo_driver'],
    'data': [
        'security/ir.model.access.csv',
        'views/cargo_delivery_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
