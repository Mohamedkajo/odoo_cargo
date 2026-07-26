# -*- coding: utf-8 -*-
"""
cargo.marketplace.settings — Singleton settings record for the platform.

Uses the standard Odoo singleton pattern: only one record is ever created.
All settings are read via get_settings() class method.
"""
from odoo import api, fields, models


class CargoMarketplaceSettings(models.Model):
    _name = 'cargo.marketplace.settings'
    _description = 'Cargo Marketplace Settings'
    _rec_name = 'platform_name'

    # ── Identity ──────────────────────────────────────────────────────────────
    platform_name = fields.Char('Platform Name', default='Cargo Marketplace', required=True)
    platform_logo = fields.Char('Logo URL')
    tagline       = fields.Char('Tagline')

    # ── Support ───────────────────────────────────────────────────────────────
    support_email = fields.Char('Support Email')
    support_phone = fields.Char('Support Phone')
    support_url   = fields.Char('Support URL')

    # ── Fees & Commission ─────────────────────────────────────────────────────
    default_commission_rate  = fields.Float('Default Commission (%)', default=15.0, digits=(5, 2))
    default_delivery_fee     = fields.Float('Default Delivery Fee (EGP)', default=15.0, digits=(8, 2))
    min_order_amount         = fields.Float('Platform Min Order (EGP)', default=50.0, digits=(8, 2))
    max_wallet_topup         = fields.Float('Max Wallet Top-up (EGP)', default=10000.0, digits=(10, 2))

    # ── Feature Flags ─────────────────────────────────────────────────────────
    maintenance_mode = fields.Boolean('Maintenance Mode', default=False)
    allow_wallet     = fields.Boolean('Enable Wallet', default=True)
    allow_coupons    = fields.Boolean('Enable Coupons', default=True)
    allow_reviews    = fields.Boolean('Enable Reviews', default=True)

    # ── Legal ─────────────────────────────────────────────────────────────────
    terms_url    = fields.Char('Terms & Conditions URL')
    privacy_url  = fields.Char('Privacy Policy URL')

    @api.model
    def get_settings(self):
        """Return the singleton settings record, creating it if needed."""
        settings = self.search([], limit=1)
        if not settings:
            settings = self.create({})
        return settings

    def to_public_dict(self):
        """Safe public subset for GET /api/settings (no sensitive data)."""
        self.ensure_one()
        return {
            'platformName':      self.platform_name,
            'platformLogo':      self.platform_logo,
            'tagline':           self.tagline,
            'supportEmail':      self.support_email,
            'supportPhone':      self.support_phone,
            'defaultDeliveryFee': self.default_delivery_fee,
            'minOrderAmount':    self.min_order_amount,
            'maintenanceMode':   self.maintenance_mode,
            'walletEnabled':     self.allow_wallet,
            'couponsEnabled':    self.allow_coupons,
            'reviewsEnabled':    self.allow_reviews,
            'termsUrl':          self.terms_url,
            'privacyUrl':        self.privacy_url,
        }
