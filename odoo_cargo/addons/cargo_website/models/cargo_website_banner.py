# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo.website.banner — Hero and promotional banners.

Consumed by GET /api/website/config (included in banners array).
Supports date-range activation and audience targeting.
"""
from odoo import fields, models

BANNER_TARGETS = [
    ('all',      'Everyone'),
    ('customer', 'Customers'),
    ('driver',   'Drivers'),
    ('vendor',   'Vendors'),
]


class CargoWebsiteBanner(models.Model):
    _name        = 'cargo.website.banner'
    _description = 'Cargo Website Banner'
    _order       = 'sequence, id'

    name      = fields.Char('Banner Name', required=True)
    sequence  = fields.Integer('Sequence', default=10)
    is_active = fields.Boolean('Active', default=True)

    # ── Content ───────────────────────────────────────────────────────────────
    title     = fields.Char('Title',    required=True)
    subtitle  = fields.Char('Subtitle')
    image_url = fields.Char('Image URL', required=True)
    cta_text  = fields.Char('Button Text')
    cta_link  = fields.Char('Button Link')

    # ── Targeting & scheduling ────────────────────────────────────────────────
    target      = fields.Selection(BANNER_TARGETS, 'Audience', default='all')
    valid_from  = fields.Date('Valid From')
    valid_until = fields.Date('Valid Until')

    def to_banner_dict(self) -> dict:
        self.ensure_one()
        return {
            'id':         self.id,
            'title':      self.title,
            'subtitle':   self.subtitle or '',
            'imageUrl':   self.image_url,
            'ctaText':    self.cta_text or '',
            'ctaLink':    self.cta_link or '',
            'target':     self.target,
            'validFrom':  str(self.valid_from)  if self.valid_from  else None,
            'validUntil': str(self.valid_until) if self.valid_until else None,
        }
