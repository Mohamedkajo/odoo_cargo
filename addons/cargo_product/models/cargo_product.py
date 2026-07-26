# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo.product — Marketplace product listing.

cargo.product.category is defined in cargo_category and referenced here
via a Many2one FK.  There is NO category model defined in this file.

Flutter Product.fromJson contract:
  id, name, description, price, originalPrice, image, storeName, storeId,
  rating, reviewCount, discountPercent, tags, isAvailable, categoryName
"""
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class CargoProduct(models.Model):
    _name = 'cargo.product'
    _description = 'Cargo Product'
    _order = 'is_featured desc, rating desc, name'
    _rec_name = 'name'

    name        = fields.Char('Name', required=True, index=True, translate=True)
    description = fields.Text('Description', translate=True)

    # ── Pricing ───────────────────────────────────────────────────────────────
    price          = fields.Float('Price (EGP)',    required=True, digits=(10, 2))
    original_price = fields.Float('Original Price', digits=(10, 2))
    discount_percent = fields.Float(
        'Discount %', compute='_compute_discount_percent', store=True, digits=(5, 1),
    )

    @api.depends('price', 'original_price')
    def _compute_discount_percent(self):
        for p in self:
            if p.original_price and p.original_price > p.price > 0:
                p.discount_percent = round(
                    (p.original_price - p.price) / p.original_price * 100, 1
                )
            else:
                p.discount_percent = 0.0

    # ── Images ────────────────────────────────────────────────────────────────
    image       = fields.Char('Image URL')
    gallery_ids = fields.One2many('cargo.product.image', 'product_id', 'Gallery')

    # ── Store link (FK to cargo.store, installed by cargo_store) ──────────────
    store_id   = fields.Many2one('cargo.store', 'Store', ondelete='cascade', index=True)
    store_name = fields.Char(related='store_id.name', store=True, readonly=True)

    # ── Category (FK to cargo.product.category, owned by cargo_category) ──────
    category_id   = fields.Many2one('cargo.product.category', 'Category', ondelete='set null', index=True)
    category_name = fields.Char(related='category_id.name', store=True, readonly=True)

    # ── Rating ────────────────────────────────────────────────────────────────
    rating       = fields.Float('Rating', default=4.0, digits=(3, 1))
    review_count = fields.Integer('Reviews', default=0)

    # ── Status ────────────────────────────────────────────────────────────────
    is_available = fields.Boolean('Available', default=True, index=True)
    is_featured  = fields.Boolean('Featured',  default=False, index=True)
    active       = fields.Boolean('Active',    default=True)

    # ── Tags ──────────────────────────────────────────────────────────────────
    tag_ids = fields.Many2many(
        'cargo.product.tag',
        'cargo_product_tag_rel', 'product_id', 'tag_id',
        string='Tags',
    )

    # ── Variants / Add-ons ────────────────────────────────────────────────────
    variant_ids = fields.One2many('cargo.product.variant', 'product_id', 'Variants')
    addon_ids   = fields.One2many('cargo.product.addon',   'product_id', 'Add-ons')

    # ── Flash Sale ────────────────────────────────────────────────────────────
    is_flash_sale    = fields.Boolean('Flash Sale', default=False, index=True)
    flash_sale_price = fields.Float('Flash Sale Price', digits=(10, 2))
    flash_sale_end   = fields.Datetime('Flash Sale Ends At')

    # ── Flutter serialisation ─────────────────────────────────────────────────

    def to_product_dict(self):
        """Return dict matching Flutter Product.fromJson() contract."""
        self.ensure_one()
        return {
            'id':              self.id,
            'name':            self.name or '',
            'description':     self.description,
            'price':           self.price,
            'originalPrice':   self.original_price or self.price,
            'image':           self.image,
            'storeName':       self.store_name,
            'storeId':         self.store_id.id if self.store_id else None,
            'rating':          self.rating,
            'reviewCount':     self.review_count,
            'discountPercent': self.discount_percent,
            'tags':            [t.name for t in self.tag_ids],
            'isAvailable':     self.is_available,
            'categoryName':    self.category_name,
        }

    def to_product_detail_dict(self):
        """Extended dict for GET /api/products/:id — includes gallery, variants, addons."""
        self.ensure_one()
        d = self.to_product_dict()
        gallery = [g.image_url for g in self.gallery_ids if g.image_url]
        if self.image and self.image not in gallery:
            gallery.insert(0, self.image)
        d.update({
            'gallery':  gallery,
            'variants': [v.to_dict() for v in self.variant_ids],
            'addons':   [a.to_dict() for a in self.addon_ids],
        })
        return d


class CargoProductImage(models.Model):
    _name = 'cargo.product.image'
    _description = 'Cargo Product Gallery Image'
    _order = 'sequence'

    product_id = fields.Many2one('cargo.product', required=True, ondelete='cascade')
    image_url  = fields.Char('URL', required=True)
    sequence   = fields.Integer(default=10)


class CargoProductVariant(models.Model):
    _name = 'cargo.product.variant'
    _description = 'Cargo Product Variant'
    _order = 'name'

    product_id  = fields.Many2one('cargo.product', required=True, ondelete='cascade')
    name        = fields.Char('Variant Name', required=True)
    options     = fields.Char('Options (JSON array)')
    price_delta = fields.Float('Price Δ (EGP)', digits=(10, 2))

    def to_dict(self):
        import json as _json
        self.ensure_one()
        try:
            opts = _json.loads(self.options or '[]')
        except Exception:
            opts = []
        return {'name': self.name, 'options': opts, 'priceDelta': self.price_delta}


class CargoProductAddon(models.Model):
    _name = 'cargo.product.addon'
    _description = 'Cargo Product Add-on'
    _order = 'name'

    product_id  = fields.Many2one('cargo.product', required=True, ondelete='cascade')
    name        = fields.Char('Add-on Name', required=True)
    price       = fields.Float('Price (EGP)', digits=(10, 2))
    is_required = fields.Boolean('Required', default=False)

    def to_dict(self):
        self.ensure_one()
        return {'name': self.name, 'price': self.price, 'isRequired': self.is_required}


class CargoProductTag(models.Model):
    _name = 'cargo.product.tag'
    _description = 'Cargo Product Tag'
    _rec_name = 'name'

    name = fields.Char('Tag', required=True)
    product_ids = fields.Many2many(
        'cargo.product',
        'cargo_product_tag_rel', 'tag_id', 'product_id',
    )
