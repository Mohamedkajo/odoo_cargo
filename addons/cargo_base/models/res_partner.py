# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
res.partner extension — Cargo fields.

Every platform participant (customer, vendor, driver) is a res.partner.
This module adds the `cargo_role` discriminator and shared cargo fields
without duplicating any native Odoo contact data.
"""

from odoo import api, fields, models
from ..constants import CARGO_ROLES


class CargoResPartner(models.Model):
    """Extend res.partner with Cargo marketplace fields."""

    _inherit = 'res.partner'

    # ── Role ─────────────────────────────────────────────────────────────────
    cargo_role = fields.Selection(
        selection=CARGO_ROLES,
        string='Cargo Role',
        index=True,
        tracking=True,
        help='Identifies this partner as a Cargo customer, vendor, or driver.',
    )

    # ── Loyalty & Wallet (denormalised for fast API reads) ────────────────────
    cargo_loyalty_points = fields.Integer(
        string='Loyalty Points',
        default=0,
        help='Accumulated loyalty points. Managed by cargo_wallet module.',
    )

    # ── Computed helpers ──────────────────────────────────────────────────────
    cargo_is_cargo_user = fields.Boolean(
        string='Is Cargo User',
        compute='_compute_cargo_is_cargo_user',
        store=True,
        index=True,
        help='True when this partner has a Cargo role assigned.',
    )
    cargo_full_address = fields.Char(
        string='Full Address',
        compute='_compute_cargo_full_address',
        help='Single-line formatted delivery address.',
    )
    cargo_display_name = fields.Char(
        string='Cargo Display Name',
        compute='_compute_cargo_display_name',
        help='Short name for API responses.',
    )

    # ── Constraints ───────────────────────────────────────────────────────────
    _sql_constraints = [
        (
            'cargo_loyalty_points_positive',
            'CHECK (cargo_loyalty_points >= 0)',
            'Loyalty points cannot be negative.',
        ),
    ]

    # ── Computes ──────────────────────────────────────────────────────────────

    @api.depends('cargo_role')
    def _compute_cargo_is_cargo_user(self):
        for partner in self:
            partner.cargo_is_cargo_user = bool(partner.cargo_role)

    @api.depends('street', 'street2', 'city', 'zip', 'country_id', 'state_id')
    def _compute_cargo_full_address(self):
        for partner in self:
            parts = filter(None, [
                partner.street,
                partner.street2,
                partner.city,
                partner.zip,
                partner.state_id.name if partner.state_id else None,
                partner.country_id.name if partner.country_id else None,
            ])
            partner.cargo_full_address = ', '.join(parts)

    @api.depends('name', 'cargo_role')
    def _compute_cargo_display_name(self):
        for partner in self:
            partner.cargo_display_name = partner.name or ''

    # ── API serialisation ─────────────────────────────────────────────────────

    def cargo_to_api_dict(self) -> dict:
        """
        Return a dict shaped exactly as the Flutter User model expects.
        Called by cargo_api controllers — keeps serialisation logic here,
        not in the controller layer.
        """
        self.ensure_one()
        return {
            'id':             self.id,
            'name':           self.name or '',
            'email':          self.email or '',
            'phone':          self.phone or '',
            'avatar':         self._cargo_avatar_url(),
            'role':           self.cargo_role or '',
            'loyaltyPoints':  self.cargo_loyalty_points,
            'address':        self.cargo_full_address or '',
        }

    def _cargo_avatar_url(self) -> str:
        """Build the public image URL for this partner's avatar."""
        if not self.image_128:
            return ''
        base = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url', 'http://localhost:8069'
        )
        return f'{base}/web/image/res.partner/{self.id}/image_128'
