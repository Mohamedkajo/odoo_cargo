# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo_category — owns every category model used across the Cargo platform.

cargo.store.category
    Top-level marketplace navigation tabs shown on the Flutter home screen
    (Food, Grocery, Pharmacy, Sweets, Coffee …).  No FK to cargo.store —
    this is a global classification browsed before a store is chosen.

product.category (native Odoo — extended in cargo_base)
    Menu sections within a single store's catalogue (Burgers, Drinks, Salads …).
    cargo_base adds cargo_icon, cargo_slug, cargo_is_active, cargo_sort_order.
    cargo_category creates the seed records and provides the menu entry.
    No separate cargo.product.category model is needed; we inherit the native tree.
"""

from odoo import fields, models


class CargoStoreCategory(models.Model):
    """Global marketplace category used to filter stores on the home screen."""

    _name = 'cargo.store.category'
    _description = 'Cargo Store Category'
    _order = 'sequence, name'
    _rec_name = 'name'

    name     = fields.Char('Name',      required=True, translate=True)
    icon     = fields.Char('Icon',      help='Emoji or icon identifier shown in the Flutter tab bar')
    image    = fields.Char('Image URL', help='Optional banner / illustration URL')
    sequence = fields.Integer('Sequence', default=10)
    active   = fields.Boolean('Active', default=True)

    # Note: the reverse store_ids One2many is intentionally NOT defined here.
    # cargo.store already has category_id pointing here; adding store_ids would
    # require cargo_category to depend on cargo_store (circular) or defer setup.
    # Access stores from a category via: env['cargo.store'].search([('category_id','=',id)])

    def to_category_dict(self):
        """Minimal dict for the Flutter GET /api/categories response."""
        self.ensure_one()
        return {
            'id':    self.id,
            'name':  self.name or '',
            'icon':  self.icon or None,
            'image': self.image or None,
        }
