# -*- coding: utf-8 -*-
{
    'name': 'Cargo Driver',
    'version': '18.0.1.0.0',
    'summary': 'Delivery driver profile — extends res.users with vehicle and GPS fields',
    'description': """
Driver-specific domain module.  Extends the native res.users model with
driver profile fields: vehicle information, live GPS position, online/offline
status, and aggregate performance metrics.

No custom cargo.driver model — res.users with cargo_role='driver' IS the driver.
All driver fields are prefixed with cargo_driver_ for clarity.

Filter drivers via:
  self.env['res.users'].search([('cargo_role', '=', 'driver')])

Native model extended:
  * res.users — vehicle info, GPS location, online status, performance metrics

REST endpoints:
  GET   /api/driver/profile
  PATCH /api/driver/profile
  POST  /api/driver/status      — go online / offline
  PATCH /api/driver/location    — update GPS coordinates
  GET   /api/driver/earnings    — today's earnings summary
""",
    'author': 'Cargo Marketplace',
    'category': 'Cargo/Driver',
    'depends': ['cargo_auth'],
    'data': [
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'views/cargo_driver_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
