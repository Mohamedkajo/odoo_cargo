# -*- coding: utf-8 -*-
{
    'name': 'Cargo Notification',
    'version': '18.0.1.0.0',
    'summary': 'Push notifications via FCM for drivers and customers on order events',
    'description': '''
Manages cargo.notification records for in-app and push notifications.

Actual push delivery uses Firebase Cloud Messaging (FCM) Legacy HTTP API
(stdlib urllib only — no extra pip packages required).

Notification triggers:
  * Customer — on every order status change (preparing, ready, collecting,
    delivering, otp_check, delivered, cancelled)
  * Driver   — on delivery assignment (cargo.delivery created)
               on order ready for pickup (cargo_status → ready)

All FCM calls are fail-safe: errors are logged but never re-raised so
a broken server key never crashes an order flow.

FCM server key is stored in ir.config_parameter (cargo.fcm.server_key)
and is configurable from Cargo Settings → Push Notifications.

Notification targets:
  * Single user (user_id set)
  * Role group (target_role set: customer/vendor/driver/admin)
  * Broadcast to all (broadcast=True)

REST endpoints:
  GET   /api/notifications           — list unread notifications for current user
  POST  /api/notifications/:id/read  — mark as read
  GET   /api/notifications/count     — unread count
    ''',
    'author': 'Cargo Marketplace',
    'category': 'Cargo/Notification',
    'depends': ['cargo_order', 'cargo_delivery', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/cargo_notification_views.xml',
        'views/menus.xml',
        'data/cargo_notification_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
