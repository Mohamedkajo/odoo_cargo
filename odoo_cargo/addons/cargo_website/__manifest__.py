# -*- coding: utf-8 -*-
{
    'name':     'Cargo Website',
    'version':  '18.0.2.0.0',
    'summary':  'Full Odoo-powered website for the Cargo marketplace (QWeb frontend + JSON APIs)',
    'description': """
Cargo Website
=============
Reproduces the Cargo company website as a native Odoo 18 Community website with:

* All 13 pages served via Odoo HTTP controllers + QWeb templates
* Same design, branding, colors (#7C3AED purple), typography (Inter), and layout
* Dynamic data connected to existing Cargo backend modules
* Responsive navbar + footer matching the React site exactly
* Odoo backend management for all CMS content

Pages:
  Home · About · Services · Marketplace · Promotions · Blog · FAQ
  Careers · Contact · Download App · Privacy Policy · Terms · 404

JSON APIs (under /api/*) are also preserved for the React website.
""",
    'author':   'Cargo Marketplace',
    'category': 'Cargo/Website',
    'depends':  [
        'web',
        'website',
        'cargo_base',
        'cargo_api',
        'cargo_coupon',
        'cargo_store',
        'cargo_category',
    ],
    'data': [
        'security/ir.model.access.csv',
        # Backend admin views
        'views/cargo_website_config_views.xml',
        'views/cargo_website_banner_views.xml',
        'views/cargo_website_flash_sale_views.xml',
        'views/cargo_website_blog_views.xml',
        'views/cargo_website_faq_views.xml',
        'views/cargo_website_job_views.xml',
        'views/cargo_website_contact_views.xml',
        'views/menus.xml',
        'data/cargo_website_data.xml',
        # QWeb website templates
        'templates/layout.xml',
        'templates/home.xml',
        'templates/about.xml',
        'templates/services.xml',
        'templates/marketplace.xml',
        'templates/promotions.xml',
        'templates/blog.xml',
        'templates/faq.xml',
        'templates/careers.xml',
        'templates/contact.xml',
        'templates/download.xml',
        'templates/legal.xml',
        'templates/errors.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'cargo_website/static/src/css/cargo_website.css',
            'cargo_website/static/src/js/cargo_website.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
