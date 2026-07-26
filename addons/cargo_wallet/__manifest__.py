# -*- coding: utf-8 -*-
{
    'name': 'Cargo Wallet',
    'version': '18.0.1.0.0',
    'summary': 'Digital wallet for the Cargo Marketplace platform',
    'description': '''
        Provides:
        - cargo.wallet model (one per user, EGP balance)
        - cargo.wallet.transaction model (transaction history)
        - GET  /api/wallet                   — wallet balance
        - GET  /api/wallet/transactions      — transaction history
        - POST /api/wallet/topup             — top up wallet
    ''',
    'author': 'Cargo Marketplace',
    'category': 'Cargo/Wallet',
    'depends': ['cargo_auth'],
    'data': [
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'views/cargo_wallet_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
