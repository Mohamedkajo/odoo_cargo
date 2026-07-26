# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo_category — owns every category model used across the Cargo platform.

cargo.store.category
    Top-level marketplace navigation tabs shown on the Flutter home screen
    (Food, Grocery, Pharmacy, Sweets, Coffee …).  No FK to cargo.store —
    this is a global classification.

cargo.product.category
    Menu sections inside a single store (Burgers, Drinks, Salads …).
    Not linked directly to a store; the connection is via cargo.product.store_id,
    which lets the same generic category name appear in multiple stores.
"""

from odoo import api, fields, models


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

    # Reverse relation — populated once cargo_store is installed
    store_ids = fields.One2many(
        'cargo.store', 'category_id',
        string='Stores',
        help='Populated by cargo_store; read-only from this module.',
    )

    def to_category_dict(self):
        """Minimal dict for the Flutter GET /api/categories response."""
        self.ensure_one()
        return {
            'id':    self.id,
            'name':  self.name or '',
            'icon':  self.icon or None,
            'image': self.image or None,
        }


class CargoProductCategory(models.Model):
    """
    Menu section within a store's catalogue.

    Intentionally has NO direct FK to cargo.store — the store ↔ category
    relationship is established via cargo.product (each product has both
    store_id and category_id).  This keeps cargo_category free of a
    dependency on cargo_store and avoids a circular import.
    """

    _name = 'cargo.product.category'
    _description = 'Cargo Product Category (store menu section)'
    _order = 'sequence, name'
    _rec_name = 'name'

    name     = fields.Char('Name',      required=True, translate=True)
    icon     = fields.Char('Icon',      help='Emoji or icon identifier')
    image    = fields.Char('Image URL')
    sequence = fields.Integer('Sequence', default=10)
    active   = fields.Boolean('Active', default=True)

    # Reverse relation — populated once cargo_product is installed
    product_ids = fields.One2many(
        'cargo.product', 'category_id',
        string='Products',
        help='Populated by cargo_product; read-only from this module.',
    )

    def to_category_dict(self):
        self.ensure_one()
        return {
            'id':    self.id,
            'name':  self.name or '',
            'icon':  self.icon or None,
            'image': self.image or None,
        }
