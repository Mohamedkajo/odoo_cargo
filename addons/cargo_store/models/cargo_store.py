# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo.store — Vendor store / restaurant profile.

This module also owns cargo.store.tag.
Product categories are owned by cargo_category (cargo.store.category for
home-screen tabs, product.category for per-store menu sections).

Flutter Store.fromJson contract:
  id, name, slug, image, logo, categoryName, categoryIcon, rating, reviewCount,
  deliveryTime, deliveryFee, minOrder, isOpen, isFeatured, isVerified, isTrending,
  isOnline, description, address, phone, distance, tags
"""
import logging
import math
import re
import unicodedata

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


def _slugify(value):
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode()
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return re.sub(r'[\s_-]+', '-', value)


class CargoStore(models.Model):
    _name = 'cargo.store'
    _description = 'Cargo Vendor Store'
    _order = 'is_featured desc, rating desc, name'
    _rec_name = 'name'

    # ── Identity ──────────────────────────────────────────────────────────────
    name = fields.Char('Store Name', required=True, index=True)
    slug = fields.Char('URL Slug', index=True, store=True,
                       compute='_compute_slug', help='Auto-generated URL-safe identifier')
    description = fields.Text('Description')
    address     = fields.Char('Address')
    phone       = fields.Char('Phone')
    email       = fields.Char('Email')

    # ── Images ────────────────────────────────────────────────────────────────
    image = fields.Char('Cover Image URL')
    logo  = fields.Char('Logo URL')

    # ── Category (from cargo_category) ───────────────────────────────────────
    category_id = fields.Many2one(
        'cargo.store.category', 'Store Category',
        ondelete='set null', index=True,
    )
    category_name = fields.Char(related='category_id.name', store=True, readonly=True)
    category_icon = fields.Char(related='category_id.icon', store=True, readonly=True)

    # ── Rating ────────────────────────────────────────────────────────────────
    rating       = fields.Float('Rating', default=4.0, digits=(3, 1))
    review_count = fields.Integer('Review Count', default=0)

    # ── Delivery ──────────────────────────────────────────────────────────────
    delivery_time = fields.Integer('Delivery Time (min)', default=30)
    delivery_fee  = fields.Float('Delivery Fee (EGP)', default=15.0, digits=(8, 2))
    min_order     = fields.Float('Min Order (EGP)',    default=0.0,  digits=(8, 2))

    # ── Status Flags ──────────────────────────────────────────────────────────
    is_open     = fields.Boolean('Open',                default=True)
    is_featured = fields.Boolean('Featured',            default=False, index=True)
    is_verified = fields.Boolean('Verified',            default=False)
    is_trending = fields.Boolean('Trending',            default=False, index=True)
    is_online   = fields.Boolean('Accepts Online Orders', default=True, index=True)
    active      = fields.Boolean('Active',              default=True)

    # ── Tags ──────────────────────────────────────────────────────────────────
    tag_ids = fields.Many2many(
        'cargo.store.tag',
        'cargo_store_tag_rel', 'store_id', 'tag_id',
        string='Tags',
    )

    # ── Location ──────────────────────────────────────────────────────────────
    latitude  = fields.Float('Latitude',  digits=(10, 7))
    longitude = fields.Float('Longitude', digits=(10, 7))

    # ── Vendor link (res.users with cargo_role='vendor') ─────────────────────
    vendor_id = fields.Many2one(
        'res.users', 'Vendor User',
        domain=[('cargo_role', '=', 'vendor')],
        ondelete='set null', index=True,
    )

    # ── Products (native product.template with cargo_store_id FK) ────────────
    product_ids = fields.One2many(
        'product.template', 'cargo_store_id',
        string='Products',
        help='All product.template records that belong to this store.',
    )

    # ── Slug compute ──────────────────────────────────────────────────────────

    @api.depends('name')
    def _compute_slug(self):
        for store in self:
            store.slug = _slugify(store.name) if store.name else False

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record.slug:
                clash = self.search(
                    [('slug', '=', record.slug), ('id', '!=', record.id)], limit=1
                )
                if clash:
                    record.slug = f'{record.slug}-{record.id}'
        return records

    # ── Flutter serialisation ─────────────────────────────────────────────────

    def to_store_dict(self, lat=None, lng=None):
        """Return a dict matching Flutter's Store.fromJson() contract."""
        self.ensure_one()
        distance = None
        if lat is not None and lng is not None and self.latitude and self.longitude:
            dlat = math.radians(lat - self.latitude)
            dlng = math.radians(lng - self.longitude)
            a = (math.sin(dlat / 2) ** 2
                 + math.cos(math.radians(self.latitude))
                 * math.cos(math.radians(lat))
                 * math.sin(dlng / 2) ** 2)
            distance = round(6371 * 2 * math.asin(math.sqrt(a)), 1)

        return {
            'id':            self.id,
            'name':          self.name or '',
            'slug':          self.slug or '',
            'image':         self.image,
            'logo':          self.logo,
            'categoryName':  self.category_name,
            'categoryIcon':  self.category_icon,
            'rating':        self.rating,
            'reviewCount':   self.review_count,
            'deliveryTime':  self.delivery_time,
            'deliveryFee':   self.delivery_fee,
            'minOrder':      self.min_order,
            'isOpen':        self.is_open,
            'isFeatured':    self.is_featured,
            'isVerified':    self.is_verified,
            'isTrending':    self.is_trending,
            'isOnline':      self.is_online,
            'description':   self.description,
            'address':       self.address,
            'phone':         self.phone,
            'distance':      distance,
            'tags':          [t.name for t in self.tag_ids],
        }


class CargoStoreTag(models.Model):
    """Descriptive store tags: Halal, Free Delivery, New, Trending …"""

    _name = 'cargo.store.tag'
    _description = 'Cargo Store Tag'
    _rec_name = 'name'

    name = fields.Char('Tag', required=True)
    store_ids = fields.Many2many(
        'cargo.store',
        'cargo_store_tag_rel', 'tag_id', 'store_id',
        string='Stores',
    )
