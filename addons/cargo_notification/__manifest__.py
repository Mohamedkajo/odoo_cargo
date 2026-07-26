# -*- coding: utf-8 -*-
{
    'name': 'Cargo Notification',
    'version': '18.0.1.0.0',
    'summary': 'In-app push notifications with Odoo chatter integration',
    'description': '''
Manages cargo.notification records for in-app and push notifications.

Inherits mail.thread to get Odoo chatter on every notification record
(useful for tracking broadcast history and admin notes).

Notification targets:
  * Single user (user_id set)
  * Role group (target_role set: customer/vendor/driver/admin)
  * Broadcast to all (broadcast=True)

order_id FK → sale.order  (for order-status notifications)

REST endpoints:
  GET   /api/notifications           — list unread notifications for current user
  POST  /api/notifications/:id/read  — mark as read
  GET   /api/notifications/count     — unread count
    ''',
    'author': 'Cargo Marketplace',
    'category': 'Cargo/Notification',
    'depends': ['cargo_order', 'mail'],
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
