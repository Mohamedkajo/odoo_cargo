# -*- coding: utf-8 -*-
{
    'name': 'Cargo Category',
    'version': '18.0.1.0.0',
    'summary': 'Global marketplace categories and per-store menu sections for Cargo',
    'description': """
Single-responsibility module that owns all category models:

  * cargo.store.category  — top-level marketplace tabs (Food, Grocery, Pharmacy …)
  * cargo.product.category — menu sections within a store (Burgers, Drinks, Sides …)

Other modules that need categories depend on this one; they never define
their own category models.

REST endpoints:
  GET /api/categories   — list all active store categories
""",
    'author': 'Cargo Marketplace',
    'category': 'Cargo/Category',
    'depends': ['cargo_base'],
    'data': [
        'security/ir.model.access.csv',
        'data/cargo_category_data.xml',
        'views/cargo_category_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
