# -*- coding: utf-8 -*-
{
    'name': 'Cargo Auth',
    'version': '18.0.1.0.0',
    'summary': 'Authentication endpoints for all Cargo Flutter apps',
    'description': '''
        Provides REST API endpoints for customer authentication:
        - POST /api/auth/register    (customer registration)
        - POST /api/auth/login       (login → JWT access + refresh tokens)
        - POST /api/auth/refresh     (rotate tokens)
        - POST /api/auth/logout      (revoke refresh token)
        - GET  /api/users/profile    (current user profile)
        - PATCH /api/users/profile   (update profile)
        - PATCH /api/users/password  (change password)
        - POST  /api/users/avatar    (upload avatar)

        All responses match the existing Flutter Customer App JSON contract
        exactly, so zero Flutter code changes are required.
    ''',
    'author': 'Cargo Marketplace',
    'category': 'Cargo/Auth',
    'depends': ['cargo_api'],
    'data': [
        'security/ir.model.access.csv',
        'data/cargo_auth_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
