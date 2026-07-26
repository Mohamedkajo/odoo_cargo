# -*- coding: utf-8 -*-
{
    'name': 'Cargo Dashboard',
    'version': '18.0.1.0.0',
    'summary': 'Odoo backend dashboard overview for the Cargo Marketplace admin',
    'description': """
Provides a unified Odoo backend dashboard that tiles together key metrics
and quick-action buttons from all other Cargo modules.

No new models or REST endpoints. Depends on cargo_reports for the
analytics views embedded in the dashboard tiles.
""",
    'author': 'Cargo Marketplace',
    'category': 'Cargo/Dashboard',
    'depends': ['cargo_reports'],
    'data': [
        'security/ir.model.access.csv',
        'views/cargo_dashboard_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
