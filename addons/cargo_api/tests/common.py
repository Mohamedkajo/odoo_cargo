# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
Shared test infrastructure for cargo_api tests.

Provides:
  - CargoApiTestCase: TransactionCase subclass with pre-created users
    and JWT helpers for writing controller integration tests.
  - Helper methods: _make_customer(), _make_vendor(), _make_driver()
  - JWT helpers: _make_access_token(), _make_refresh_token()
  - HTTP mock helpers: _make_request_headers()
"""

from odoo.tests.common import TransactionCase


class CargoApiTestCase(TransactionCase):
    """
    Base test case for cargo_api tests.

    Sets up test users for each Cargo role and provides JWT generation
    helpers based on the seeded cargo.jwt.secret.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Cache JWT secret once per class
        cls._jwt_secret = None

    def setUp(self):
        super().setUp()
        self._jwt_secret = (
            self.env['ir.config_parameter'].sudo()
            .get_param('cargo.jwt.secret', '')
        )

    # ── User factories ────────────────────────────────────────────────────────

    def _make_cargo_user(self, name, email, role, **partner_vals):
        """Create a new res.users with the given cargo role."""
        group_map = {
            'customer':       'cargo_base.cargo_group_customer',
            'vendor':         'cargo_base.cargo_group_vendor',
            'vendor_manager': 'cargo_base.cargo_group_vendor_manager',
            'driver':         'cargo_base.cargo_group_driver',
            'operations':     'cargo_base.cargo_group_operations',
            'finance':        'cargo_base.cargo_group_finance',
            'admin':          'cargo_base.cargo_group_admin',
            'super_admin':    'cargo_base.cargo_group_super_admin',
        }
        group_ref = group_map.get(role)
        groups = [(4, self.env.ref(group_ref).id)] if group_ref else []

        user = self.env['res.users'].sudo().create({
            'name':    name,
            'email':   email,
            'login':   email,
            'groups_id': groups,
            'partner_id': self.env['res.partner'].sudo().create({
                'name':        name,
                'email':       email,
                'cargo_role':  role,
                **partner_vals,
            }).id,
        })
        return user

    def _make_customer(self, name='Test Customer', email=None):
        email = email or f'{name.lower().replace(" ", "_")}@test.cargo'
        return self._make_cargo_user(name, email, 'customer')

    def _make_vendor(self, name='Test Vendor', email=None):
        email = email or f'{name.lower().replace(" ", "_")}@test.cargo'
        return self._make_cargo_user(name, email, 'vendor')

    def _make_driver(self, name='Test Driver', email=None):
        email = email or f'{name.lower().replace(" ", "_")}@test.cargo'
        return self._make_cargo_user(name, email, 'driver')

    def _make_admin(self, name='Test Admin', email=None):
        email = email or f'{name.lower().replace(" ", "_")}@test.cargo'
        return self._make_cargo_user(name, email, 'admin')

    # ── JWT helpers ───────────────────────────────────────────────────────────

    def _get_jwt_secret(self):
        """Return the cargo JWT secret, failing loudly if not configured."""
        secret = self._jwt_secret
        self.assertTrue(secret, 'cargo.jwt.secret must be set for JWT tests.')
        return secret

    def _make_access_token(self, user):
        """Generate a valid access token for the given user."""
        from cargo_base.utils.jwt_utils import generate_access_token
        secret = self._get_jwt_secret()
        role   = user.partner_id.cargo_role or 'customer'
        return generate_access_token(user.id, role, secret)

    def _make_refresh_token(self, user):
        """Generate a valid refresh token for the given user."""
        from cargo_base.utils.jwt_utils import generate_refresh_token
        secret = self._get_jwt_secret()
        return generate_refresh_token(user.id, secret)

    def _bearer_headers(self, user):
        """Return a dict with the Authorization: Bearer header for a user."""
        return {'Authorization': f'Bearer {self._make_access_token(user)}'}

    # ── cargo.api.token helpers ───────────────────────────────────────────────

    def _store_refresh_token(self, user, refresh_token=None, **kwargs):
        """
        Store a hashed refresh token in cargo.api.token.
        Returns the token record.
        """
        from cargo_base.utils.jwt_utils import hash_token, generate_refresh_token
        import time
        if refresh_token is None:
            refresh_token = self._make_refresh_token(user)

        expires_in = int(
            self.env['ir.config_parameter'].sudo()
            .get_param('cargo.jwt.refresh_expiry_seconds', '2592000')
        )
        return self.env['cargo.api.token'].sudo().create({
            'user_id':    user.id,
            'token_hash': hash_token(refresh_token),
            'expires_at': fields_datetime_from_epoch(time.time() + expires_in),
            **kwargs,
        })


def fields_datetime_from_epoch(epoch_seconds):
    """Convert a Unix timestamp to an Odoo Datetime string."""
    import datetime
    dt = datetime.datetime.utcfromtimestamp(epoch_seconds)
    return dt.strftime('%Y-%m-%d %H:%M:%S')
