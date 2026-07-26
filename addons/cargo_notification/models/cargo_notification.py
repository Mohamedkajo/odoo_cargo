# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo.notification — In-app push notification records.

Inherits mail.thread so admins can log notes on any notification record
and see the Odoo chatter.  Actual push delivery is handled by the
notification controller (FCM/APNs via vendor device tokens).

Target resolution:
  * user_id set → notification for a specific user
  * broadcast = True → for all users or a role group
"""
import json
import logging

from odoo import api, fields, models

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

    # ── Delivery helper ───────────────────────────────────────────────────────

    @api.model
    def send_to_user(self, user, title: str, body: str,
                     notif_type='system', payload=None, order=None):
        """Create and mark a notification as sent for a single user."""
        record = self.sudo().create({
            'title':    title,
            'body':     body,
            'type':     notif_type,
            'user_id':  user.id,
            'payload':  json.dumps(payload or {}),
            'order_id': order.id if order else False,
            'is_sent':  True,
            'sent_at':  fields.Datetime.now(),
        })
        device_token = getattr(user, 'cargo_device_token', None)
        if device_token:
            _logger.info(
                'cargo.notification: push to user=%s token=%s title=%r',
                user.id, device_token[:8] + '…', title,
            )
            # TODO: integrate FCM / APNs SDK here
        return record

    @api.model
    def broadcast_notification(self, title: str, body: str,
                                notif_type='system', payload=None, role=None):
        """Broadcast a notification to all users, or to users matching role."""
        domain = [('active', '=', True)]
        if role:
            domain.append(('cargo_role', '=', role))
        users = self.env['res.users'].sudo().search(domain)
        notifs = []
        for user in users:
            notifs.append({
                'title':      title,
                'body':       body,
                'type':       notif_type,
                'user_id':    user.id,
                'payload':    json.dumps(payload or {}),
                'broadcast':  True,
                'target_role': role or False,
                'is_sent':    True,
                'sent_at':    fields.Datetime.now(),
            })
        if notifs:
            self.sudo().create(notifs)
        _logger.info('cargo.notification: broadcast to %d users (role=%s)', len(notifs), role)
