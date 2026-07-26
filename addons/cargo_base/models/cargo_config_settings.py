# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
Cargo configuration settings.

Extends res.config.settings with a dedicated "Cargo" tab so administrators
can manage all platform parameters from Odoo's native Settings screen.
"""

from odoo import api, fields, models


class CargoConfigSettings(models.TransientModel):
    """Extend Odoo settings with Cargo-specific configuration."""

    _inherit = 'res.config.settings'

    # ── JWT ───────────────────────────────────────────────────────────────────
    cargo_jwt_secret = fields.Char(
        string='JWT Secret',
        config_parameter='cargo.jwt.secret',
        help='HMAC-SHA256 secret used to sign JWT tokens. '
             'Changing this invalidates all active sessions.',
    )
    cargo_jwt_access_expiry = fields.Integer(
        string='Access Token Expiry (seconds)',
        config_parameter='cargo.jwt.access_expiry_seconds',
        default=86400,
        help='Access token lifetime in seconds. Default: 86400 (24 hours).',
    )
    cargo_jwt_refresh_expiry = fields.Integer(
        string='Refresh Token Expiry (seconds)',
        config_parameter='cargo.jwt.refresh_expiry_seconds',
        default=2592000,
        help='Refresh token lifetime in seconds. Default: 2592000 (30 days).',
    )

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    cargo_rate_limit_rpm = fields.Integer(
        string='API Rate Limit (req/min)',
        config_parameter='cargo.rate_limit.requests_per_minute',
        default=60,
        help='Maximum API requests per minute per IP address.',
    )

    # ── Commission ────────────────────────────────────────────────────────────
    cargo_commission_default = fields.Float(
        string='Default Commission Rate (%)',
        config_parameter='cargo.commission.default_rate',
        digits=(5, 2),
        default=10.0,
        help='Default platform commission applied to each order.',
    )

    # ── OTP ───────────────────────────────────────────────────────────────────
    cargo_otp_expiry_minutes = fields.Integer(
        string='OTP Expiry (minutes)',
        config_parameter='cargo.otp.expiry_minutes',
        default=10,
        help='How long a delivery OTP remains valid.',
    )

    # ── Media ─────────────────────────────────────────────────────────────────
    cargo_max_image_mb = fields.Integer(
        string='Max Image Size (MB)',
        config_parameter='cargo.media.max_image_size_mb',
        default=5,
        help='Maximum allowed upload size for product and store images.',
    )

    # ── Support ───────────────────────────────────────────────────────────────
    cargo_support_email = fields.Char(
        string='Support Email',
        config_parameter='cargo.support.email',
        help='Customer-facing support email address.',
    )
    cargo_support_phone = fields.Char(
        string='Support Phone',
        config_parameter='cargo.support.phone',
        help='Customer-facing support phone number.',
    )

    # ── Locale ────────────────────────────────────────────────────────────────
    cargo_default_currency = fields.Char(
        string='Default Currency',
        config_parameter='cargo.default_currency',
        default='EGP',
        help='ISO currency code for the marketplace (e.g. EGP).',
    )
    cargo_default_country = fields.Char(
        string='Default Country Code',
        config_parameter='cargo.default_country_code',
        default='EG',
        help='ISO 3166-1 alpha-2 country code (e.g. EG for Egypt).',
    )
