# -*- coding: utf-8 -*-
{
    'name': 'Cargo Notification',
    'version': '18.0.1.0.0',
    'summary': 'In-app notifications for the Cargo Marketplace Flutter app',
    'description': '''
        Provides:
        - cargo.notification model
        - GET  /api/notifications            — list user notifications
        - POST /api/notifications/:id/read   — mark notification as read
        - POST /api/notifications/read-all   — mark all as read
    ''',
    'author': 'Cargo Marketplace',
    'category': 'Cargo/Notification',
    'depends': ['cargo_auth'],
    'data': [
        'security/ir.model.access.csv',
        'views/cargo_notification_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
