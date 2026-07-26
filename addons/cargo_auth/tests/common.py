# -*- coding: utf-8 -*-
"""
Common test infrastructure for cargo_auth tests.
"""
import json

from odoo.tests.common import HttpCase


class CargoAuthTestCase(HttpCase):
    """
    Base class for cargo_auth HTTP tests.

    Provides helpers for calling the auth REST endpoints
    and asserting response shapes.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base_url = '/api'

    # ── HTTP helpers ───────────────────────────────────────────────────────────

    def _post(self, path, body=None, token=None):
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        return self.url_open(
            self.base_url + path,
            data=json.dumps(body or {}).encode(),
            headers=headers,
        )

    def _get(self, path, token=None):
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        return self.url_open(self.base_url + path, headers=headers)

    def _patch(self, path, body=None, token=None):
        import urllib.request
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        # url_open doesn't support PATCH, use urllib directly
        url = self.base_url + path
        data = json.dumps(body or {}).encode()
        req = urllib.request.Request(
            self.env['ir.config_parameter'].sudo().get_param('web.base.url', '') + url,
            data=data,
            headers=headers,
            method='PATCH',
        )
        import urllib.error
        try:
            with urllib.request.urlopen(req) as resp:
                return resp
        except urllib.error.HTTPError as e:
            return e

    # ── Fixtures ───────────────────────────────────────────────────────────────

    def create_test_user(self, suffix=''):
        """Create a test customer user and return the res.users record."""
        email = f'test{suffix}@cargo.test'
        existing = self.env['res.users'].sudo().search(
            [('login', '=', email)], limit=1
        )
        if existing:
            return existing

        user = self.env['res.users'].sudo().create({
            'name':       f'Test User {suffix}',
            'login':      email,
            'email':      email,
            'password':   'TestPass123!',
            'cargo_role': 'customer',
            'groups_id':  [(4, self.env.ref('cargo_base.cargo_group_customer').id)],
        })
        return user

    def register_via_api(self, suffix=''):
        """Register a new user via the API and return (response_dict, token)."""
        body = {
            'name':     f'API User {suffix}',
            'email':    f'api{suffix}@cargo.test',
            'password': 'ApiPass123!',
            'phone':    '+201001234567',
        }
        resp = self._post('/auth/register', body)
        data = json.loads(resp.read())
        return data, data.get('token')

    def login_via_api(self, email, password):
        """Login via the API and return (response_dict, token)."""
        resp = self._post('/auth/login', {'email': email, 'password': password})
        data = json.loads(resp.read())
        return data, data.get('token')

    def assert_user_dict(self, user_dict):
        """Assert that a dict matches the Flutter User.fromJson() contract."""
        required = ['id', 'name', 'email', 'role', 'loyaltyPoints', 'walletBalance']
        for key in required:
            self.assertIn(key, user_dict, f'Missing field: {key}')
        self.assertIsInstance(user_dict['id'], int)
        self.assertIsInstance(user_dict['loyaltyPoints'], int)
        self.assertIsInstance(user_dict['walletBalance'], (int, float))
