# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
res.users extension — Cargo fields.

Adds Flutter push notification token storage, role relay from partner,
and unread notification count to every Odoo user.
"""

from odoo import api, fields, models
from ..constants import CARGO_ROLES


class CargoResUsers(models.Model):
    """Extend res.users with Cargo marketplace fields."""

    _inherit = 'res.users'

    # ── Role (relayed from partner for convenience) ───────────────────────────
    cargo_role = fields.Selection(
        selection=CARGO_ROLES,
        string='Cargo Role',
        related='partner_id.cargo_role',
        store=True,
        readonly=False,
        tracking=True,
    )

    # ── Push notification token (FCM / APNs) ──────────────────────────────────
    cargo_device_token = fields.Char(
        string='Device Token',
        copy=False,
        help='Firebase Cloud Messaging token for push notifications.',
    )

    # ── Unread notifications count (denormalised for performance) ─────────────
    cargo_unread_count = fields.Integer(
        string='Unread Notifications',
        compute='_compute_cargo_unread_count',
        help='Number of unread cargo.notification records for this user.',
    )

    # ── Self-service field access (Odoo 18: classmethod API) ─────────────────
    # Odoo 17+ replaced the class-level SELF_READABLE_FIELDS / SELF_WRITEABLE_FIELDS
    # sets with classmethods.  Using the old sets raises AttributeError on install.

    @classmethod
    def _get_self_readable_fields(cls):
        return super()._get_self_readable_fields() | {
            'cargo_role',
            'cargo_device_token',
            'cargo_unread_count',
        }

    @classmethod
    def _get_self_writeable_fields(cls):
        return super()._get_self_writeable_fields() | {
            'cargo_device_token',
        }

    # ── Computes ──────────────────────────────────────────────────────────────

    def _compute_cargo_unread_count(self):
        """Count unread notifications — cargo.notification is defined in cargo_notification."""
        Notif = self.env.get('cargo.notification')
        if Notif is None:
            # cargo_notification not installed yet
            for user in self:
                user.cargo_unread_count = 0
            return
        for user in self:
            user.cargo_unread_count = Notif.sudo().search_count([
                ('user_id', '=', user.id),
                ('is_read', '=', False),
            ])

    # ── Helpers ───────────────────────────────────────────────────────────────

    def cargo_has_role(self, role: str) -> bool:
        """Return True if this user has the given Cargo role."""
        self.ensure_one()
        return self.cargo_role == role

    def cargo_to_api_dict(self) -> dict:
        """
        Return a dict shaped exactly as the Flutter User model expects.
        Delegates to the partner's serialiser and adds auth fields.
        """
        self.ensure_one()
        data = self.partner_id.cargo_to_api_dict()
        data['walletBalance'] = 0.0   # populated by cargo_wallet module
        data['unreadCount']   = self.cargo_unread_count
        return data
