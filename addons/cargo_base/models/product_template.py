# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
product.template extension — Cargo marketplace fields.

Adds discount pricing, tags, featured/trending flags, and rating fields
to every product in the system. Store association (`cargo_store_id`) is
added by the cargo_store module after cargo.store is defined.
"""

from odoo import api, fields, models


class CargoProductTemplate(models.Model):
    """Extend product.template with Cargo marketplace fields."""

    _inherit = 'product.template'

    # ── Pricing (Cargo-specific) ──────────────────────────────────────────────
    cargo_original_price = fields.Monetary(
        string='Original Price',
        currency_field='currency_id',
        help='Price before discount. Leave 0 if no discount applies.',
    )
    cargo_discount_percent = fields.Float(
        string='Discount %',
        digits=(5, 2),
        default=0.0,
        help='Discount percentage applied to list_price.',
    )
    cargo_effective_price = fields.Monetary(
        string='Effective Price',
        currency_field='currency_id',
        compute='_compute_cargo_effective_price',
        store=True,
        help='list_price after discount is applied.',
    )

    # ── Discoverability flags ─────────────────────────────────────────────────
    cargo_is_featured = fields.Boolean(
        string='Featured',
        default=False,
        index=True,
        help='Show in featured sections on the home screen.',
    )
    cargo_is_trending = fields.Boolean(
        string='Trending',
        default=False,
        index=True,
        help='Show in trending products carousel.',
    )
    cargo_is_available = fields.Boolean(
        string='Available',
        default=True,
        index=True,
        help='Whether the product is currently available for purchase.',
    )

    # ── Tags ─────────────────────────────────────────────────────────────────
    cargo_tags = fields.Char(
        string='Cargo Tags',
        help='Comma-separated tags for search and filtering (e.g. "halal,spicy").',
    )

    # ── Ratings (aggregate, updated by cargo_review module) ───────────────────
    cargo_rating = fields.Float(
        string='Rating',
        digits=(3, 2),
        default=0.0,
        help='Average customer rating (0.0–5.0). Updated by cargo_review.',
    )
    cargo_review_count = fields.Integer(
        string='Reviews',
        default=0,
        help='Total number of approved reviews. Updated by cargo_review.',
    )

    # ── SQL constraints ───────────────────────────────────────────────────────
    _sql_constraints = [
        (
            'cargo_discount_percent_range',
            'CHECK (cargo_discount_percent >= 0 AND cargo_discount_percent <= 100)',
            'Discount percentage must be between 0 and 100.',
        ),
        (
            'cargo_rating_range',
            'CHECK (cargo_rating >= 0 AND cargo_rating <= 5)',
            'Product rating must be between 0 and 5.',
        ),
        (
            'cargo_review_count_positive',
            'CHECK (cargo_review_count >= 0)',
            'Review count cannot be negative.',
        ),
    ]

    # ── Computes ──────────────────────────────────────────────────────────────

    @api.depends('list_price', 'cargo_discount_percent')
    def _compute_cargo_effective_price(self):
        for product in self:
            if product.cargo_discount_percent > 0:
                discount = product.list_price * (product.cargo_discount_percent / 100.0)
                product.cargo_effective_price = round(product.list_price - discount, 2)
            else:
                product.cargo_effective_price = product.list_price

    # ── API serialisation ─────────────────────────────────────────────────────

    def cargo_to_api_dict(self) -> dict:
        """
        Return a dict matching the Flutter Product model.
        store_id / storeName are populated by cargo_store module via super().
        """
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url', 'http://localhost:8069'
        )
        image_url = (
            f'{base_url}/web/image/product.template/{self.id}/image_512'
            if self.image_512 else ''
        )
        tags = [t.strip() for t in (self.cargo_tags or '').split(',') if t.strip()]

        return {
            'id':              self.id,
            'name':            self.name or '',
            'description':     self.description_sale or '',
            'price':           self.cargo_effective_price,
            'originalPrice':   self.cargo_original_price or self.list_price,
            'image':           image_url,
            'storeId':         None,    # overridden by cargo_store
            'storeName':       '',      # overridden by cargo_store
            'rating':          self.cargo_rating,
            'reviewCount':     self.cargo_review_count,
            'discountPercent': int(self.cargo_discount_percent),
            'tags':            tags,
            'isAvailable':     self.cargo_is_available,
            'categoryName':    self.categ_id.name if self.categ_id else '',
        }
