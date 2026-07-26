# -*- coding: utf-8 -*-
{
    'name': 'Cargo Vendor',
    'version': '18.0.1.0.0',
    'summary': 'Vendor profile management — extends res.partner with business fields',
    'description': """
Vendor-specific business domain.  Extends the native res.partner model with
vendor registration, approval workflow, commission settings and business details.

No custom cargo.vendor model — res.partner (and its linked res.users) is the
vendor entity.  All vendor fields are prefixed with cargo_vendor_ to avoid
conflicts with native Odoo fields.

Native model extended:
  * res.partner — vendor business fields, approval workflow, commission rate

REST endpoints:
  GET   /api/vendor/profile
  PATCH /api/vendor/profile
  GET   /api/vendor/stats
  POST  /api/vendor/register
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
