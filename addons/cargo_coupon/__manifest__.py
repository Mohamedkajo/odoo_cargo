# -*- coding: utf-8 -*-
{
    'name': 'Cargo Coupon',
    'version': '18.0.1.0.0',
    'summary': 'Coupon codes and promotional discounts for Cargo Marketplace',
    'description': """
Manages promo codes, percentage/fixed discounts, usage limits, and expiry.

Models:
  * cargo.coupon — coupon definition
  * cargo.coupon.usage — per-user redemption record

REST endpoints:
  POST /api/coupons/validate   — check code validity and return discount
  POST /api/coupons/apply      — apply coupon to current cart
""",
    'author': 'Cargo Marketplace',
    'category': 'Cargo/Coupon',
    'depends': ['cargo_cart'],
    'data': [
        'security/ir.model.access.csv',
        'views/cargo_coupon_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
