# -*- coding: utf-8 -*-
{
    'name': 'Cargo Review',
    'version': '18.0.1.0.0',
    'summary': 'Customer reviews for stores and products — auto-refreshes rating aggregates',
    'description': '''
Manages cargo.review records which link to native Odoo models:
  product_id → product.template (marketplace product)
  order_id   → sale.order       (the completed order)
  store_id   → cargo.store

After each review, rating aggregates are refreshed on the target
store (cargo.store.rating) or product (product.template.cargo_rating).

Also defines the cargo.rating.mixin abstract model that stores and products
can inherit to get _refresh_cargo_rating().
    ''',
    'author': 'Cargo Marketplace',
    'category': 'Cargo/Review',
    'depends': ['cargo_order'],
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
