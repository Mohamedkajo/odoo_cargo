# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
product.category extension — Cargo marketplace fields.

Adds emoji icon, URL slug, and store count to Odoo's built-in
product categories so the Flutter app can render the category grid.
"""

import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CargoProductCategory(models.Model):
    """Extend product.category with Cargo marketplace fields."""

    _inherit = 'product.category'

    # ── Cargo display fields ──────────────────────────────────────────────────
    cargo_icon = fields.Char(
        string='Icon (Emoji)',
        help='Emoji or icon code shown in the Flutter category grid, e.g. ☕',
    )
    cargo_slug = fields.Char(
        string='Slug',
        index=True,
        help='URL-friendly identifier used in API responses.',
    )
    cargo_is_active = fields.Boolean(
        string='Active on Marketplace',
        default=True,
        index=True,
        help='When False this category is hidden from the Flutter app.',
    )
    cargo_sort_order = fields.Integer(
        string='Sort Order',
        default=10,
        help='Lower numbers appear first in the category list.',
    )

    # ── Computed ──────────────────────────────────────────────────────────────
    cargo_store_count = fields.Integer(
        string='Stores',
        compute='_compute_cargo_store_count',
        help='Number of active stores in this category.',
    )

    # ── SQL constraints ───────────────────────────────────────────────────────
    _sql_constraints = [
        (
            'cargo_slug_unique',
            'UNIQUE(cargo_slug)',
            'Category slug must be unique across the platform.',
        ),
    ]

    # ── Validation ────────────────────────────────────────────────────────────

    @api.constrains('cargo_slug')
    def _check_cargo_slug(self):
        slug_pattern = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
        for cat in self:
            if cat.cargo_slug and not slug_pattern.match(cat.cargo_slug):
                raise ValidationError(
                    f"Slug '{cat.cargo_slug}' is invalid. "
                    "Use lowercase letters, digits and hyphens only (e.g. 'fast-food')."
                )

    # ── ORM overrides ─────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name') and not vals.get('cargo_slug'):
                vals['cargo_slug'] = self._cargo_slugify(vals['name'])
        return super().create(vals_list)

    # ── Computes ──────────────────────────────────────────────────────────────

    def _compute_cargo_store_count(self):
        """Count active cargo.store records in this category."""
        Store = self.env.get('cargo.store')
        if Store is None:
            for cat in self:
                cat.cargo_store_count = 0
            return
        for cat in self:
            cat.cargo_store_count = Store.sudo().search_count([
                ('category_id', '=', cat.id),
                ('is_deleted', '=', False),
            ])

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _cargo_slugify(name: str) -> str:
        """Convert a display name to a URL-friendly slug."""
        slug = name.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug).strip('-')
        return slug or 'category'

    # ── API serialisation ─────────────────────────────────────────────────────

    def cargo_to_api_dict(self) -> dict:
        """Return a dict matching the Flutter Category model."""
        self.ensure_one()
        return {
            'id':         self.id,
            'name':       self.name or '',
            'slug':       self.cargo_slug or '',
            'icon':       self.cargo_icon or '',
            'storeCount': self.cargo_store_count,
            'sortOrder':  self.cargo_sort_order,
        }
