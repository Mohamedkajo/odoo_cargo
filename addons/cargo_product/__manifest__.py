# -*- coding: utf-8 -*-
{
    'name': 'Cargo Product',
    'version': '18.0.1.0.0',
    'summary': 'Product catalogue and flash sales for the Cargo Marketplace',
    'description': """
Single-responsibility module that owns every product-related model and
the public product-browsing REST API.

Models:
  * cargo.product         — marketplace product listing
  * cargo.product.variant — size/colour variants per product
  * cargo.product.addon   — add-on extras per product
  * cargo.product.image   — gallery images per product
  * cargo.product.tag     — product-level tags

Note: cargo.product.category is owned by cargo_category (to avoid circular
      imports with cargo_store).  This module references that model via FK.

REST endpoints:
  GET /api/products
  GET /api/products/trending
  GET /api/products/:id
  GET /api/flash-sales
""",
    'author': 'Cargo Marketplace',
    'category': 'Cargo/Product',
    'depends': ['cargo_api', 'cargo_category'],
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
