# -*- coding: utf-8 -*-
{
    'name': 'Cargo Cart',
    'version': '18.0.1.0.0',
    'summary': 'Shopping cart for the Cargo Marketplace Flutter app',
    'description': '''
        Provides:
        - cargo.cart model (one cart per customer)
        - cargo.cart.line model (cart line items)
        - GET  /api/cart                  — get current cart
        - POST /api/cart/items            — add item
        - PATCH /api/cart/items/:itemId   — update quantity
        - DELETE /api/cart/items/:itemId  — remove item
        - DELETE /api/cart                — clear cart
    ''',
    'author': 'Cargo Marketplace',
    'category': 'Cargo/Cart',
    'depends': ['cargo_auth', 'cargo_product', 'cargo_store'],
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
