# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.

{
    'name': 'Cargo Base',
    'version': '18.0.1.0.0',
    'category': 'Cargo/Base',
    'summary': 'Foundation module for the Cargo multi-vendor marketplace platform',
    'description': """
Cargo Base
==========
Core foundation for the Cargo Marketplace platform built on Odoo 18 Community.

This module provides:
- Extended native Odoo models (res.partner, product.template, product.category, sale.order)
- Shared constants, exceptions and utility functions
- JWT authentication foundation
- Audit logging infrastructure
- Base security groups, ACLs and record rule framework
- Common API response helpers
- Input validation utilities
- Platform configuration parameters
- Base menus and settings UI
- Installation and upgrade hooks
- Unit tests

All other Cargo modules depend on this module.
""",
    'author': 'Cargo Marketplace',
    'website': 'https://cargo.marketplace',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'product',
        'sale',
        'sale_management',
        'stock',
        'account',
        'web',
    ],
    'data': [
        # Security — loaded first
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        # Data
        'data/cargo_base_data.xml',
        # Views
        'views/cargo_audit_log_views.xml',
        'views/cargo_settings_views.xml',
        'views/res_partner_views.xml',
        'views/res_users_views.xml',
        'views/product_template_views.xml',
        'views/product_category_views.xml',
        'views/sale_order_views.xml',
        # Menus — loaded last
        'views/menus.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'pre_init_hook': 'pre_init_hook',
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'images': ['static/description/icon.png'],
}
