# -*- coding: utf-8 -*-
{
    'name': 'Cargo Delivery',
    'version': '18.0.1.0.0',
    'summary': 'Delivery task lifecycle: assignment, pickup, GPS tracking, OTP confirmation',
    'description': '''
Owns the cargo.delivery model which links a sale.order to an assigned driver (res.users).

Lifecycle: assigned → picked_up → on_the_way → delivered (or failed)
OTP flow: pickup OTP (vendor → driver) + delivery OTP (driver → customer)

Models (owned):
  * cargo.delivery — delivery task record

Native models referenced:
  * sale.order  (order_id FK — the order being delivered)
  * res.users   (driver_id FK — driver with cargo_role='driver')

REST endpoints:
  GET  /api/delivery/active     — active deliveries for the current driver
  POST /api/delivery/:id/status — advance delivery status
  POST /api/delivery/:id/location — update driver GPS
    ''',
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
