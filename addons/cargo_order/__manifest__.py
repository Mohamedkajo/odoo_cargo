# -*- coding: utf-8 -*-
{
    'name': 'Cargo Order',
    'version': '18.0.1.0.0',
    'summary': 'Delivery orders — extends sale.order with Cargo delivery workflow',
    'description': '''
Extends the native sale.order model with delivery-specific fields:
  • cargo_delivery_address  — customer delivery address
  • cargo_payment_method    — cash / card / wallet
  • cargo_discount          — coupon / promo discount (EGP)
  • cargo_coupon_code       — applied coupon code reference
  • cargo_driver_name/phone/rating — denormalised driver info

No custom cargo.order model.  sale.order (with cargo_status from cargo_base,
cargo_store_id from cargo_store, and delivery fields from this module) IS the
Cargo delivery order.

The order creation flow reads the customer's cargo.cart, creates a sale.order
and sale.order.line records, then clears the cart.

REST endpoints:
  GET  /api/orders               — list my orders
  POST /api/orders               — place order from cart
  GET  /api/orders/:id           — order detail + status timeline
  POST /api/orders/:id/cancel    — cancel order
  GET  /api/orders/:id/tracking  — live tracking data
    ''',
    'author': 'Cargo Marketplace',
    'category': 'Cargo/Order',
    'depends': ['cargo_cart'],
    'data': [
        'security/ir.model.access.csv',
        'views/cargo_order_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
