# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo.notification — In-app notification for Cargo Marketplace users.

Flutter contract:
  GET /api/notifications → [{ id, title, body, type, isRead, createdAt }]
  POST /api/notifications/:id/read → { id, isRead: true }
"""
import logging

from odoo import api, fields, models
from cargo_base.constants import NOTIFICATION_TYPES

_logger = logging.getLogger(__name__)


class CargoNotification(models.Model):
    _name = 'cargo.notification'
    _description = 'Cargo In-App Notification'
    _order = 'id desc'
    _rec_name = 'title'

    user_id = fields.Many2one(
        'res.users', 'User',
        required=True, ondelete='cascade', index=True,
    )
    title = fields.Char('Title', required=True)
    body  = fields.Text('Body')
    type  = fields.Selection(
        NOTIFICATION_TYPES,
        string='Type',
        default='system',
        required=True,
    )
    is_read    = fields.Boolean('Read', default=False, index=True)
    created_at = fields.Datetime('Created At', default=fields.Datetime.now, readonly=True)
    read_at    = fields.Datetime('Read At', readonly=True)

    # Optional reference to related object
    related_model = fields.Char('Related Model')
    related_id    = fields.Integer('Related Record ID')

    def action_mark_read(self):
        """Mark this notification (or batch) as read."""
        self.filtered(lambda n: not n.is_read).write({
            'is_read': True,
            'read_at': fields.Datetime.now(),
        })

    def to_notification_dict(self):
        self.ensure_one()
        return {
            'id':        self.id,
            'title':     self.title or '',
            'body':      self.body or '',
            'type':      self.type or 'system',
            'isRead':    self.is_read,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
        }

    @api.model
    def send_to_user(self, user_id, title, body, notif_type='system',
                     related_model=None, related_id=None):
        """
        Create a notification for a given user.
        Used by other modules (order updates, wallet credits, promos).
        """
        notif = self.sudo().create({
            'user_id':       user_id,
            'title':         title,
            'body':          body,
            'type':          notif_type,
            'related_model': related_model,
            'related_id':    related_id or 0,
        })
        return notif
