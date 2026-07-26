# -*- coding: utf-8 -*-
{
    'name': 'Cargo Vendor',
    'version': '18.0.1.0.0',
    'summary': 'Vendor profile management for the Cargo Marketplace',
    'description': """
Vendor-specific business domain. Owns the cargo.vendor profile model
that extends res.users with vendor registration, approval, commission
settings, and business details.

Models:
  * cargo.vendor — vendor profile (business info, approval, commission rate)

REST endpoints:
  GET  /api/vendor/profile
  PATCH /api/vendor/profile
  GET  /api/vendor/stats
  POST /api/vendor/register
""",
    'author': 'Cargo Marketplace',
    'category': 'Cargo/Vendor',
    'depends': ['cargo_auth', 'cargo_store'],
    'data': [
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'views/cargo_vendor_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
