# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo_product — marketplace product layer on top of product.template.

cargo_base adds the core cargo fields (rating, is_available, is_featured,
discount_percent, effective_price, cargo_to_api_dict).

cargo_store adds cargo_store_id + injects storeId/storeName into the API dict.

This module adds the food-delivery-specific fields:
  • Flash sale pricing and scheduling
  • Image URL field (URL-based, supplements native binary images)
  • Relation to cargo.product.addon  (food add-ons: extras, toppings)
  • Relation to cargo.product.variant (simplified size/flavour variants)

No cargo.product custom model — product.template IS the product.

Flutter Product.fromJson contract:
  id, name, description, price, originalPrice, image,
  storeName, storeId, rating, reviewCount, discountPercent,
  tags, isAvailable, categoryName

Extended by cargo_to_api_detail_dict:
  + addons, variants, flashSalePrice, flashSaleEnd
"""
import logging
from datetime import datetime

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class CargoProductTemplateExtension(models.Model):
    """Extend product.template with flash sale, image URL and food sub-models."""

    _inherit = 'product.template'

    # ── URL-based image (supplements native binary image) ─────────────────────
    cargo_image_url = fields.Char(
        string='Image URL',
        help='External or CDN image URL.  Used in API responses instead of '
             'the Odoo binary image when set.',
    )

    # ── Flash sale ────────────────────────────────────────────────────────────
    cargo_is_flash_sale    = fields.Boolean('Flash Sale', default=False, index=True)
    cargo_flash_sale_price = fields.Monetary(
        'Flash Sale Price',
        currency_field='currency_id',
    )
    cargo_flash_sale_end   = fields.Datetime('Flash Sale Ends At')

    # ── Food-specific sub-models ──────────────────────────────────────────────
    cargo_addon_ids = fields.One2many(
        'cargo.product.addon',
        'product_tmpl_id',
        string='Add-ons',
        help='Optional extras the customer can add to this item (toppings, sauces …).',
    )
    cargo_variant_ids = fields.One2many(
        'cargo.product.variant',
        'product_tmpl_id',
        string='Variants',
        help='Simplified size / flavour variants with a price delta.',
    )

    # ── API dict override ─────────────────────────────────────────────────────

    def cargo_to_api_dict(self) -> dict:
        """Extend the base dict with image URL and flash sale indicator."""
        d = super().cargo_to_api_dict()
        # Prefer explicit URL over the Odoo binary endpoint
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url', 'http://localhost:8069'
        )
        d['image'] = self.cargo_image_url or (
            f'{base_url}/web/image/product.template/{self.id}/image_512'
            if self.image_512 else None
        )
        d['isFlashSale'] = self.cargo_is_flash_sale
        return d

    def cargo_to_api_detail_dict(self) -> dict:
        """Extended dict for GET /api/products/:id — includes variants and add-ons."""
        self.ensure_one()
        d = self.cargo_to_api_dict()
        d['addons']   = [a.to_dict() for a in self.cargo_addon_ids]
        d['variants'] = [v.to_dict() for v in self.cargo_variant_ids]
        if self.cargo_is_flash_sale:
            d['flashSalePrice'] = self.cargo_flash_sale_price or d['price']
            d['flashSaleEnd']   = (
                self.cargo_flash_sale_end.isoformat()
                if self.cargo_flash_sale_end else None
            )
        return d


class CargoProductAddon(models.Model):
    """Optional extras the customer can add to a product (toppings, sauces …)."""

    _name = 'cargo.product.addon'
    _description = 'Cargo Product Add-on'
    _order = 'name'

    product_tmpl_id = fields.Many2one(
        'product.template', 'Product',
        required=True, ondelete='cascade', index=True,
    )
    name        = fields.Char('Add-on Name', required=True)
    price       = fields.Float('Price (EGP)', digits=(10, 2), default=0.0)
    is_required = fields.Boolean('Required', default=False)

    def to_dict(self) -> dict:
        self.ensure_one()
        return {
            'name':       self.name,
            'price':      self.price,
            'isRequired': self.is_required,
        }


class CargoProductVariant(models.Model):
    """
    Simplified food variant (Small / Medium / Large with a price delta).

    Not to be confused with Odoo's native product.product / product.attribute
    system.  For food delivery, variants are presentation-only; no separate
    SKU or stock record is created.
    """

    _name = 'cargo.product.variant'
    _description = 'Cargo Product Variant'
    _order = 'name'

    product_tmpl_id = fields.Many2one(
        'product.template', 'Product',
        required=True, ondelete='cascade', index=True,
    )
    name        = fields.Char('Variant Name', required=True)
    options     = fields.Char('Options (JSON array)',
                              help='e.g. ["Small","Medium","Large"]')
    price_delta = fields.Float('Price Δ (EGP)', digits=(10, 2), default=0.0)

    def to_dict(self) -> dict:
        import json as _json
        self.ensure_one()
        try:
            opts = _json.loads(self.options or '[]')
        except Exception:
            opts = []
        return {
            'name':       self.name,
            'options':    opts,
            'priceDelta': self.price_delta,
        }
