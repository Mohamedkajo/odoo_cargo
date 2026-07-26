# -*- coding: utf-8 -*-
{
    'name': 'Cargo Store',
    'version': '18.0.1.0.0',
    'summary': 'Vendor store profiles and store-listing API for the Cargo Marketplace',
    'description': """
Single-responsibility module that owns the vendor store model and all
store-browsing REST endpoints.

Also extends product.template with cargo_store_id so marketplace products
can be associated with a store (cargo_base could not do this because cargo.store
was not yet defined).

Models (owned):
  * cargo.store     — vendor store / restaurant profile
  * cargo.store.tag — descriptive tags (Halal, Free Delivery, Trending …)

Native model extended:
  * product.template — adds cargo_store_id Many2one FK

REST endpoints:
  GET /api/stores
  GET /api/stores/featured
  GET /api/stores/nearby
  GET /api/stores/online
  GET /api/stores/:id
  GET /api/stores/:id/products    (queries product.template)
  GET /api/stores/:id/categories  (derives product.category via product.template)

Note: GET /api/categories is owned by cargo_category.
""",
    'author': 'Cargo Marketplace',
    'category': 'Cargo/Store',
    'depends': ['cargo_api', 'cargo_auth', 'cargo_category'],
    'data': [
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'data/cargo_store_data.xml',
        'views/cargo_store_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
