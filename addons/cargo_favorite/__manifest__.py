# -*- coding: utf-8 -*-
{
    'name': 'Cargo Favorites',
    'version': '18.0.1.0.0',
    'summary': 'Favorites (wishlisted stores and products) for the Cargo Flutter app',
    'description': '''
        Provides:
        - cargo.favorite model (store or product favorites per user)
        - GET  /api/favorites          — list my favorites
        - POST /api/favorites/toggle   — add/remove from favorites
    ''',
    'author': 'Cargo Marketplace',
    'category': 'Cargo/Favorite',
    'depends': ['cargo_auth', 'cargo_product', 'cargo_store'],
    'data': [
        'security/ir.model.access.csv',
        'security/record_rules.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
