# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo.website.config — Singleton platform configuration.

Stores global settings consumed by GET /api/website/config:
app-store URLs, social links, support contacts, SEO defaults.
"""
from odoo import fields, models


class CargoWebsiteConfig(models.Model):
    _name        = 'cargo.website.config'
    _description = 'Cargo Website Configuration'
    _rec_name    = 'platform_name'

    # ── Identity ──────────────────────────────────────────────────────────────
    platform_name = fields.Char('Platform Name', default='Cargo', required=True)
    tagline       = fields.Char('Tagline')
    logo_url      = fields.Char('Logo URL')
    favicon_url   = fields.Char('Favicon URL')

    # ── App store links ───────────────────────────────────────────────────────
    app_store_url  = fields.Char('App Store URL (iOS)')
    play_store_url = fields.Char('Play Store URL (Android)')

    # ── Support contacts ──────────────────────────────────────────────────────
    support_email = fields.Char('Support Email')
    support_phone = fields.Char('Support Phone')
    support_url   = fields.Char('Support URL')
    office_address = fields.Text('Office Address')

    # ── Social links ──────────────────────────────────────────────────────────
    facebook_url  = fields.Char('Facebook URL')
    instagram_url = fields.Char('Instagram URL')
    twitter_url   = fields.Char('Twitter / X URL')
    linkedin_url  = fields.Char('LinkedIn URL')
    youtube_url   = fields.Char('YouTube URL')

    # ── SEO defaults ──────────────────────────────────────────────────────────
    meta_title       = fields.Char('Default Meta Title')
    meta_description = fields.Char('Default Meta Description')
    meta_keywords    = fields.Char('Default Meta Keywords')
    og_image_url     = fields.Char('Default OG Image URL')

    # ── Maintenance ───────────────────────────────────────────────────────────
    maintenance_mode    = fields.Boolean('Maintenance Mode', default=False)
    maintenance_message = fields.Text('Maintenance Message')

    def to_config_dict(self) -> dict:
        self.ensure_one()
        return {
            'platformName':      self.platform_name,
            'tagline':           self.tagline or '',
            'logoUrl':           self.logo_url or '',
            'faviconUrl':        self.favicon_url or '',
            'appStoreUrl':       self.app_store_url or '',
            'playStoreUrl':      self.play_store_url or '',
            'support': {
                'email':   self.support_email or '',
                'phone':   self.support_phone or '',
                'url':     self.support_url or '',
                'address': self.office_address or '',
            },
            'social': {
                'facebook':  self.facebook_url or '',
                'instagram': self.instagram_url or '',
                'twitter':   self.twitter_url or '',
                'linkedin':  self.linkedin_url or '',
                'youtube':   self.youtube_url or '',
            },
            'seo': {
                'title':       self.meta_title or '',
                'description': self.meta_description or '',
                'keywords':    self.meta_keywords or '',
                'ogImage':     self.og_image_url or '',
            },
            'maintenanceMode':    self.maintenance_mode,
            'maintenanceMessage': self.maintenance_message or '',
        }
