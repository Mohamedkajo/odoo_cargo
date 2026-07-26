# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo.api.token — Refresh token storage and revocation.

Access tokens are short-lived JWTs (default 24 h) and are stateless —
they are NOT stored in the database.  Only refresh tokens (long-lived,
default 30 d) are persisted here so they can be individually revoked.

When a refresh token is used to obtain a new access token, its
``last_used_at`` timestamp is updated.  Revoking a token sets
``is_revoked = True`` and keeps the row for audit purposes until the
scheduled cleanup cron removes expired entries.
"""

import logging

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CargoApiToken(models.Model):
    """Persisted refresh-token store for JWT revocation and audit."""

    _name        = 'cargo.api.token'
    _description = 'Cargo API Refresh Token'
    _order       = 'created_at desc'
    _log_access  = False   # no write_uid / write_date tracking columns

    # ── Identity ─────────────────────────────────────────────────────────────

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
        required=True,
        ondelete='cascade',
        index=True,
    )
    token_hash = fields.Char(
        string='Token Hash',
        required=True,
        index=True,
        copy=False,
        help='SHA-256 of the raw refresh token.  The raw token is never stored.',
    )

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    expires_at = fields.Datetime(
        string='Expires At',
        required=True,
        copy=False,
    )
    is_revoked = fields.Boolean(
        string='Revoked',
        default=False,
        index=True,
        copy=False,
        help='True when this token has been explicitly revoked before expiry.',
    )
    is_expired = fields.Boolean(
        string='Expired',
        compute='_compute_is_expired',
        store=False,
    )
    is_valid = fields.Boolean(
        string='Valid',
        compute='_compute_is_valid',
        store=False,
        help='True when the token is not revoked and has not expired.',
    )

    # ── Context ───────────────────────────────────────────────────────────────

    ip_address = fields.Char(
        string='IP Address',
        copy=False,
    )
    user_agent = fields.Char(
        string='User Agent',
        copy=False,
    )
    device_info = fields.Char(
        string='Device Info',
        copy=False,
        help='Device name or identifier reported by the client.',
    )

    # ── Timestamps ────────────────────────────────────────────────────────────

    created_at = fields.Datetime(
        string='Issued At',
        default=fields.Datetime.now,
        required=True,
        copy=False,
    )
    last_used_at = fields.Datetime(
        string='Last Used At',
        copy=False,
    )

    # ── SQL constraints ───────────────────────────────────────────────────────

    _sql_constraints = [
        ('token_hash_unique', 'UNIQUE(token_hash)',
         'A token with this hash already exists.'),
    ]

    # ── Computes ──────────────────────────────────────────────────────────────

    @api.depends('expires_at')
    def _compute_is_expired(self):
        now = fields.Datetime.now()
        for rec in self:
            rec.is_expired = bool(rec.expires_at and rec.expires_at < now)

    @api.depends('is_revoked', 'expires_at')
    def _compute_is_valid(self):
        now = fields.Datetime.now()
        for rec in self:
            rec.is_valid = (
                not rec.is_revoked
                and bool(rec.expires_at)
                and rec.expires_at > now
            )

    # ── Computed display_name ─────────────────────────────────────────────────

    display_name = fields.Char(
        string='Name',
        compute='_compute_display_name',
        store=False,
    )

    def _compute_display_name(self):
        for rec in self:
            user_name = rec.user_id.name or f'uid:{rec.user_id.id}'
            device    = rec.device_info or rec.ip_address or 'unknown device'
            status    = 'revoked' if rec.is_revoked else ('expired' if rec.is_expired else 'valid')
            rec.display_name = f'Token #{rec.id} — {user_name} — {device} [{status}]'

    # ── Actions ───────────────────────────────────────────────────────────────

    def action_revoke(self):
        """Mark these tokens as revoked."""
        valid = self.filtered(lambda t: not t.is_revoked)
        if not valid:
            raise ValidationError('Selected token(s) are already revoked.')
        valid.write({'is_revoked': True})
        _logger.info('Revoked %d API token(s) for users: %s',
                     len(valid), valid.mapped('user_id.name'))
        return True

    @api.model
    def cargo_revoke_all_for_user(self, user_id):
        """
        Revoke all active refresh tokens for a given user.
        Called on password change, logout-all, or account suspension.
        """
        tokens = self.sudo().search([
            ('user_id', '=', user_id),
            ('is_revoked', '=', False),
        ])
        if tokens:
            tokens.write({'is_revoked': True})
            _logger.info('Revoked %d token(s) for user_id=%d.', len(tokens), user_id)

    @api.model
    def cargo_cleanup_expired(self):
        """
        Delete expired AND revoked tokens older than 7 days.
        Called by ir.cron once per day.
        """
        cutoff = fields.Datetime.subtract(fields.Datetime.now(), days=7)
        old_tokens = self.sudo().search([
            ('expires_at', '<', cutoff),
        ])
        count = len(old_tokens)
        old_tokens.unlink()
        _logger.info('cargo.api.token cleanup: removed %d expired token(s).', count)
        return count

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('token_hash'):
                raise ValidationError('token_hash is required.')
            if len(vals['token_hash']) < 32:
                raise ValidationError('token_hash must be at least 32 characters (SHA-256).')
        return super().create(vals_list)
