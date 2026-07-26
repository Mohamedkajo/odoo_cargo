# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo.notification — In-app push notification records.

Inherits mail.thread so admins can log notes on any notification record
and see the Odoo chatter.  Actual push delivery is done via FCM Legacy HTTP
using cargo_notification/utils/fcm.py.

Target resolution:
  * user_id set → notification for a specific user
  * broadcast = True → for all users or a role group
"""
import json
import logging

from odoo import api, fields, models

from ..utils import fcm as fcm_util

_logger = logging.getLogger(__name__)

NOTIFICATION_TYPES = [
    ('order_update',  'Order Update'),
    ('promo',         'Promotion / Offer'),
    ('system',        'System'),
    ('driver_update', 'Driver Update'),
    ('chat',          'Chat Message'),
]


class CargoNotification(models.Model):
    _name = 'cargo.notification'
    _description = 'Cargo Notification'
    _order = 'create_date desc'
    _inherit = ['mail.thread']          # ← chatter integration

    # ── Content ───────────────────────────────────────────────────────────────
    title   = fields.Char('Title',   required=True, tracking=True)
    body    = fields.Text('Body',    required=True)
    type    = fields.Selection(NOTIFICATION_TYPES, 'Type', default='system', index=True)
    payload = fields.Text('Data Payload (JSON)',
                          help='Arbitrary JSON data forwarded to the app.')

    # ── Target ────────────────────────────────────────────────────────────────
    user_id = fields.Many2one(
        'res.users', 'Target User',
        ondelete='cascade', index=True,
        help='Leave empty for broadcast notifications.',
    )
    target_role = fields.Selection(
        [('customer', 'Customers'), ('vendor', 'Vendors'),
         ('driver', 'Drivers'),    ('admin', 'Admins')],
        string='Target Role',
        help='When set and user_id is empty, notification targets all users with this role.',
    )
    broadcast = fields.Boolean(
        'Broadcast to All',
        default=False,
        help='Send to every user regardless of role filter.',
    )

    # ── Reference to related order ────────────────────────────────────────────
    order_id = fields.Many2one(
        'sale.order', 'Related Order',
        ondelete='set null', index=True,
        domain=[('cargo_status', '!=', False)],
    )

    # ── Delivery status ───────────────────────────────────────────────────────
    is_sent = fields.Boolean('Sent', default=False, tracking=True)
    is_read = fields.Boolean('Read by User', default=False)
    sent_at = fields.Datetime('Sent At')

    # ── API serialisation ─────────────────────────────────────────────────────

    def to_notification_dict(self) -> dict:
        self.ensure_one()
        try:
            data = json.loads(self.payload or '{}')
        except Exception:
            data = {}
        return {
            'id':      self.id,
            'title':   self.title,
            'body':    self.body,
            'type':    self.type,
            'data':    data,
            'isRead':  self.is_read,
            'orderId': self.order_id.id if self.order_id else None,
            'sentAt':  self.sent_at.isoformat() if self.sent_at else None,
        }

    # ── FCM push dispatch ────────────────────────────────────────────────────

    def send_push(self) -> bool:
        """
        Dispatch this notification record via FCM to ``user_id.cargo_device_token``.

        Marks ``is_sent = True`` and records ``sent_at`` regardless of whether
        FCM accepted the message (the notification record always exists for the
        in-app inbox; the push is best-effort).

        Returns True if FCM accepted the push, False otherwise.
        """
        self.ensure_one()
        device_token = self.user_id.cargo_device_token if self.user_id else None

        # Always mark as sent (the in-app record IS the notification)
        if not self.is_sent:
            self.sudo().write({
                'is_sent': True,
                'sent_at': fields.Datetime.now(),
            })

        if not device_token:
            return False

        try:
            data = json.loads(self.payload or '{}')
        except Exception:
            data = {}

        return fcm_util.send_push(
            self.env,
            device_token=device_token,
            title=self.title,
            body=self.body,
            data={
                'notificationId': str(self.id),
                'type':           self.type or 'system',
                'orderId':        str(self.order_id.id) if self.order_id else '',
                **data,
            },
        )

    # ── Delivery helpers ─────────────────────────────────────────────────────

    @api.model
    def send_to_user(self, user, title: str, body: str,
                     notif_type='system', payload=None, order=None):
        """
        Create a notification record for ``user`` and dispatch it via FCM.

        This is the primary entry-point for programmatic notifications (order
        status changes, driver assignment, etc.).
        """
        record = self.sudo().create({
            'title':    title,
            'body':     body,
            'type':     notif_type,
            'user_id':  user.id,
            'payload':  json.dumps(payload or {}),
            'order_id': order.id if order else False,
            'is_sent':  False,   # send_push() will set True
        })
        record.send_push()
        return record

    @api.model
    def broadcast_notification(self, title: str, body: str,
                                notif_type='system', payload=None, role=None):
        """Broadcast a notification to all users, or to users matching role."""
        domain = [('active', '=', True)]
        if role:
            domain.append(('cargo_role', '=', role))
        users = self.env['res.users'].sudo().search(domain)

        notif_vals = []
        for user in users:
            notif_vals.append({
                'title':       title,
                'body':        body,
                'type':        notif_type,
                'user_id':     user.id,
                'payload':     json.dumps(payload or {}),
                'broadcast':   True,
                'target_role': role or False,
                'is_sent':     False,
            })

        if not notif_vals:
            return

        records = self.sudo().create(notif_vals)

        # Dispatch FCM for each user with a registered device token
        device_tokens = [
            u.cargo_device_token for u in users if u.cargo_device_token
        ]
        if device_tokens:
            fcm_util.send_multicast(
                self.env,
                device_tokens=device_tokens,
                title=title,
                body=body,
                data={'type': notif_type, **(payload or {})},
            )

        # Mark all as sent
        records.sudo().write({
            'is_sent': True,
            'sent_at': fields.Datetime.now(),
        })

        _logger.info(
            'cargo.notification: broadcast to %d users (role=%s), '
            'FCM tokens found: %d',
            len(notif_vals), role, len(device_tokens),
        )
