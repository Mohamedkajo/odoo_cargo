# -*- coding: utf-8 -*-
{
    'name': 'Cargo Review',
    'version': '18.0.1.0.0',
    'summary': 'Customer reviews and ratings for stores and products on Cargo',
    'description': """
Manages star ratings (1–5) and text reviews for both stores and products.
On save, the module recomputes the aggregate rating and review count on
the target store or product record.

Models:
  * cargo.review — review for a store or product

REST endpoints:
  GET  /api/stores/:id/reviews
  POST /api/stores/:id/reviews
  GET  /api/products/:id/reviews
  POST /api/products/:id/reviews
""",
    'author': 'Cargo Marketplace',
    'category': 'Cargo/Review',
    'depends': ['cargo_auth', 'cargo_store', 'cargo_product'],
    'data': [
        'security/ir.model.access.csv',
        'views/cargo_review_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
