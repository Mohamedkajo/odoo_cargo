# -*- coding: utf-8 -*-
{
    'name': 'Cargo Product',
    'version': '18.0.1.0.0',
    'summary': 'Marketplace product layer on native product.template — Cargo',
    'description': """
Extends the native product.template model with food-delivery-specific fields
and provides the product-browsing REST API.

No custom cargo.product model.  product.template IS the marketplace product.
cargo_base adds core cargo fields; cargo_store adds cargo_store_id;
this module adds flash sale scheduling, image URL and food sub-models.

Models owned (custom — no native equivalent):
  * cargo.product.addon   — optional extras (toppings, sauces)
  * cargo.product.variant — simplified size/flavour variants with price delta

Native model extended:
  * product.template — flash sale fields, cargo_image_url, addon/variant relations

REST endpoints:
  GET /api/products
  GET /api/products/trending
  GET /api/products/:id
  GET /api/flash-sales
""",
    'author': 'Cargo Marketplace',
    'category': 'Cargo/Product',
    'depends': ['cargo_api', 'cargo_category', 'cargo_store'],
    'data': [
        'security/ir.model.access.csv',
        'data/cargo_product_data.xml',
        'views/cargo_product_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
