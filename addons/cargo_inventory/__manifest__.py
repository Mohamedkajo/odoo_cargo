# -*- coding: utf-8 -*-
{
    'name': 'Cargo Inventory',
    'version': '18.0.1.0.0',
    'summary': 'Stock-level tracking per product per store for Cargo Marketplace',
    'description': """
Tracks real-time stock quantities for each product at each store location.
Automatically updates cargo.product.is_available when stock reaches zero.

Models:
  * cargo.inventory — stock entry (product × store × quantity)

REST endpoints:
  GET   /api/vendor/inventory          — vendor's stock list
  PATCH /api/vendor/inventory/:id      — adjust stock quantity
  POST  /api/vendor/inventory/restock  — bulk restock
""",
    'author': 'Cargo Marketplace',
    'category': 'Cargo/Inventory',
    'depends': ['cargo_product', 'cargo_store'],
    'data': [
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'views/cargo_inventory_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
