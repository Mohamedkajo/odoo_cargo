# -*- coding: utf-8 -*-
{
    'name':     'Cargo Website Integration',
    'version':  '18.0.1.0.0',
    'summary':  'Odoo-managed content for the Cargo React website',
    'description': """
Cargo Website Integration
=========================
Adds Odoo backend management for all dynamic content consumed by the
Cargo React + Vite company website:

* Website configuration (platform metadata, social links, app-store URLs)
* Hero/promo banners (sequenced, date-range activated)
* Flash sales (timed discount campaigns)
* Blog posts & categories
* FAQ items & categories
* Careers / job listings
* Contact form submissions
* Public coupon listing endpoint

All data is exposed as JSON REST APIs under /api/* so the React website
continues to work unchanged — only the data source moves into Odoo.
""",
    'author':   'Cargo Marketplace',
    'category': 'Cargo/Website',
    'depends':  ['cargo_base', 'cargo_api', 'cargo_coupon', 'cargo_store'],
    'data': [
        'security/ir.model.access.csv',
        'views/cargo_website_config_views.xml',
        'views/cargo_website_banner_views.xml',
        'views/cargo_website_flash_sale_views.xml',
        'views/cargo_website_blog_views.xml',
        'views/cargo_website_faq_views.xml',
        'views/cargo_website_job_views.xml',
        'views/cargo_website_contact_views.xml',
        'views/menus.xml',
        'data/cargo_website_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
