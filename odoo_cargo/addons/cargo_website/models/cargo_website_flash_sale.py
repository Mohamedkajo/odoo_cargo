# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo.website.flash.sale — Timed discount campaigns.

Consumed by GET /api/flash-sales.
The React website displays these on the home page and promotions page
with countdown timers.
"""
from odoo import fields, models


class CargoWebsiteFlashSale(models.Model):
    _name        = 'cargo.website.flash.sale'
    _description = 'Cargo Flash Sale'
    _order       = 'valid_until, sequence'

    name      = fields.Char('Campaign Name', required=True)
    sequence  = fields.Integer('Sequence', default=10)
    is_active = fields.Boolean('Active', default=True)

    # ── Display ───────────────────────────────────────────────────────────────
    title            = fields.Char('Display Title', required=True)
    subtitle         = fields.Char('Subtitle')
    image_url        = fields.Char('Image URL')
    discount_percent = fields.Float('Discount (%)', digits=(5, 2))
    discount_label   = fields.Char('Discount Label',
                                   help='e.g. "Up to 30% off" — overrides auto label')

    # ── Scope ─────────────────────────────────────────────────────────────────
    store_id    = fields.Many2one('cargo.store', 'Restricted to Store',
                                  ondelete='set null',
                                  help='Leave empty to apply to all stores.')
    coupon_code = fields.Char('Promo Code', help='Optional coupon code to show with this sale.')

    # ── Schedule ──────────────────────────────────────────────────────────────
    valid_from  = fields.Datetime('Starts At')
    valid_until = fields.Datetime('Ends At', required=True)

    def to_flash_sale_dict(self) -> dict:
        self.ensure_one()
        return {
            'id':              self.id,
            'title':           self.title,
            'subtitle':        self.subtitle or '',
            'imageUrl':        self.image_url or '',
            'discountPercent': self.discount_percent,
            'discountLabel':   self.discount_label or f'Up to {int(self.discount_percent)}% off',
            'store': {
                'id':   self.store_id.id,
                'name': self.store_id.name,
            } if self.store_id else None,
            'couponCode': self.coupon_code or '',
            'validFrom':  self.valid_from.isoformat()  if self.valid_from  else None,
            'validUntil': self.valid_until.isoformat() if self.valid_until else None,
        }
