# -*- coding: utf-8 -*-
{
    'name': 'Cargo Order',
    'version': '18.0.1.0.0',
    'summary': 'Delivery orders for the Cargo Marketplace Flutter app',
    'description': '''
        Provides:
        - cargo.order model (customer delivery orders)
        - cargo.order.line model (order line items)
        - GET  /api/orders               — list my orders
        - POST /api/orders               — place order from cart
        - GET  /api/orders/:id           — order detail
        - POST /api/orders/:id/cancel    — cancel order
        - GET  /api/orders/:id/tracking  — live tracking
    ''',
    'author': 'Cargo Marketplace',
    'category': 'Cargo/Order',
    'depends': ['cargo_cart'],
    'data': [
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'data/cargo_order_sequence.xml',
        'views/cargo_order_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
