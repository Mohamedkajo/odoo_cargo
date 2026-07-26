# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
Cargo Base — Installation / upgrade / uninstall hooks.

pre_init_hook  : run before the module is installed (schema checks, etc.)
post_init_hook : run after the module is installed (seed data, config params)
uninstall_hook : run before the module is uninstalled (cleanup)
"""

import logging
import secrets

from odoo.release import version_info

_logger = logging.getLogger(__name__)


# ── Default configuration parameters ─────────────────────────────────────────

_CONFIG_DEFAULTS = {
    'cargo.jwt.secret':                    None,       # generated on install
    'cargo.jwt.access_expiry_seconds':     '86400',    # 24 h
    'cargo.jwt.refresh_expiry_seconds':    '2592000',  # 30 days
    'cargo.rate_limit.requests_per_minute':'60',
    'cargo.commission.default_rate':       '10.0',     # 10%
    'cargo.otp.expiry_minutes':            '10',
    'cargo.media.max_image_size_mb':       '5',
    'cargo.support.email':                 'support@cargo.marketplace',
    'cargo.support.phone':                 '+201000000000',
    'cargo.default_currency':              'EGP',
    'cargo.default_country_code':          'EG',
}


def pre_init_hook(env):
    """
    Run before module installation.
    Verifies minimum Odoo version and PostgreSQL extensions.
    """
    _logger.info('[cargo_base] pre_init_hook — verifying environment …')

    # Confirm we are on Odoo 18+
    major = version_info[0]
    if major < 18:
        raise EnvironmentError(
            f'Cargo Marketplace requires Odoo 18 or later. '
            f'Detected version: {major}.'
        )

    _logger.info('[cargo_base] pre_init_hook — environment OK (Odoo %s)', major)


def post_init_hook(env):
    """
    Run after module installation.
    Seeds ir.config_parameter entries and generates the JWT secret.
    """
    _logger.info('[cargo_base] post_init_hook — seeding configuration parameters …')

    ICP = env['ir.config_parameter'].sudo()

    for key, default_value in _CONFIG_DEFAULTS.items():
        existing = ICP.get_param(key)
        if not existing:
            value = default_value
            if key == 'cargo.jwt.secret':
                # Generate a cryptographically secure 64-byte secret
                value = secrets.token_hex(64)
                _logger.info('[cargo_base] Generated JWT secret for key: %s', key)
            ICP.set_param(key, value)
            _logger.info('[cargo_base] Set config param: %s', key)
        else:
            _logger.info('[cargo_base] Config param already set, skipping: %s', key)

    _logger.info('[cargo_base] post_init_hook — complete.')


def uninstall_hook(env):
    """
    Run before module uninstallation.
    Removes Cargo-specific configuration parameters.
    Leaves native Odoo data untouched.
    """
    _logger.warning(
        '[cargo_base] uninstall_hook — removing Cargo configuration parameters. '
        'This will break all other Cargo modules if they are still installed.'
    )

    ICP = env['ir.config_parameter'].sudo()
    for key in _CONFIG_DEFAULTS:
        param = ICP.search([('key', '=', key)])
        if param:
            param.unlink()
            _logger.info('[cargo_base] Removed config param: %s', key)

    _logger.warning('[cargo_base] uninstall_hook — complete.')
