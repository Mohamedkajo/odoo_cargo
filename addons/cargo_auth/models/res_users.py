# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
res.users extension for Cargo Auth.

Adds:
  - cargo_avatar_url  : publicly-accessible avatar URL (computed from partner image)
  - cargo_to_auth_dict(): serialises the user to the JSON shape the Flutter app expects
"""

import logging

from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    # ── Avatar URL ────────────────────────────────────────────────────────────
    # Computed public URL for the partner's image, returned in auth responses.
    # The actual image is stored on the partner's `image_128` field.
    cargo_avatar_url = fields.Char(
        string='Avatar URL',
        compute='_compute_cargo_avatar_url',
        store=False,
    )

    @api.depends('partner_id.image_128')
    def _compute_cargo_avatar_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', '')
        for user in self:
            if user.partner_id.image_128:
                user.cargo_avatar_url = f'{base_url}/web/image/res.partner/{user.partner_id.id}/image_128'
            else:
                user.cargo_avatar_url = None

    # ── Public dict ───────────────────────────────────────────────────────────

    def cargo_to_auth_dict(self):
        """
        Return a dict matching the Flutter Customer App's User.fromJson() contract:

        {
          "id":            int,
          "name":          str,
          "email":         str,
          "phone":         str | null,
          "avatar":        str | null,
          "role":          str,       // "customer" | "driver" | "vendor" | "admin"
          "loyaltyPoints": int,
          "walletBalance": float,
          "createdAt":     str,       // ISO 8601
        }

        walletBalance is populated by cargo_wallet once that module is installed;
        falls back to 0.0 so cargo_auth can stand alone.
        """
        self.ensure_one()
        partner = self.partner_id

        # Wallet balance — filled by cargo_wallet module via _get_cargo_wallet_balance()
        wallet_balance = 0.0
        if hasattr(self, '_get_cargo_wallet_balance'):
            try:
                wallet_balance = float(self._get_cargo_wallet_balance())
            except Exception:
                wallet_balance = 0.0

        return {
            'id':            self.id,
            'name':          self.name or '',
            'email':         self.email or self.login or '',
            'phone':         partner.phone or partner.mobile or None,
            'avatar':        self.cargo_avatar_url or None,
            'role':          self.cargo_role or 'customer',
            'loyaltyPoints': int(partner.cargo_loyalty_points or 0),
            'walletBalance': wallet_balance,
            'createdAt':     self.create_date.isoformat() if self.create_date else None,
        }
