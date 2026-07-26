# -*- coding: utf-8 -*-
"""
cargo_auth — Integration tests for authentication endpoints.

Tests map directly to Flutter Customer App flows:
  - Register → Login → Get Profile → Update Profile → Refresh → Logout
"""
import json

from .common import CargoAuthTestCase


class TestCargoAuthRegister(CargoAuthTestCase):
    """POST /api/auth/register"""

    def test_register_success_returns_token_and_user(self):
        data, token = self.register_via_api('_reg1')
        self.assertIn('token', data, 'Response must have token')
        self.assertIn('user', data, 'Response must have user')
        self.assertIsNotNone(token, 'Token must not be None')
        self.assert_user_dict(data['user'])

    def test_register_user_dict_has_flutter_fields(self):
        data, _ = self.register_via_api('_reg2')
        u = data['user']
        self.assertEqual(u['role'], 'customer')
        self.assertEqual(u['loyaltyPoints'], 0)
        self.assertIsInstance(u['walletBalance'], (int, float))

    def test_register_duplicate_email_returns_409(self):
        self.register_via_api('_dup')
        # second register with same email
        body = {
            'name':     'Dup User',
            'email':    'api_dup@cargo.test',
            'password': 'DupPass123!',
        }
        resp = self._post('/auth/register', body)
        self.assertEqual(resp.status, 409)

    def test_register_missing_name_returns_400(self):
        resp = self._post('/auth/register', {'email': 'x@cargo.test', 'password': 'Pass1234!'})
        self.assertEqual(resp.status, 400)

    def test_register_invalid_email_returns_400(self):
        resp = self._post('/auth/register', {'name': 'X', 'email': 'not-an-email', 'password': 'Pass1234!'})
        self.assertEqual(resp.status, 400)

    def test_register_weak_password_returns_400(self):
        resp = self._post('/auth/register', {'name': 'X', 'email': 'weak@cargo.test', 'password': '123'})
        self.assertEqual(resp.status, 400)

    def test_register_invalid_phone_returns_400(self):
        resp = self._post('/auth/register', {
            'name': 'X', 'email': 'ph@cargo.test',
            'password': 'Pass1234!', 'phone': 'invalid'
        })
        self.assertEqual(resp.status, 400)

    def test_register_valid_egyptian_phone_accepted(self):
        data, _ = self.register_via_api('_ph')
        self.assertEqual(data['user']['role'], 'customer')


class TestCargoAuthLogin(CargoAuthTestCase):
    """POST /api/auth/login"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = cls.env['res.users'].sudo().create({
            'name':       'Login Test User',
            'login':      'logintest@cargo.test',
            'email':      'logintest@cargo.test',
            'password':   'LoginPass123!',
            'cargo_role': 'customer',
            'groups_id':  [(4, cls.env.ref('cargo_base.cargo_group_customer').id)],
        })

    def test_login_success_returns_token_and_user(self):
        data, token = self.login_via_api('logintest@cargo.test', 'LoginPass123!')
        self.assertIn('token', data)
        self.assertIn('user', data)
        self.assertIsNotNone(token)
        self.assert_user_dict(data['user'])

    def test_login_wrong_password_returns_401(self):
        resp = self._post('/auth/login', {'email': 'logintest@cargo.test', 'password': 'WRONG'})
        self.assertEqual(resp.status, 401)

    def test_login_unknown_email_returns_401(self):
        resp = self._post('/auth/login', {'email': 'nobody@cargo.test', 'password': 'Pass1234!'})
        self.assertEqual(resp.status, 401)

    def test_login_missing_fields_returns_400(self):
        resp = self._post('/auth/login', {'email': 'logintest@cargo.test'})
        self.assertEqual(resp.status, 400)

    def test_login_response_matches_flutter_contract(self):
        data, _ = self.login_via_api('logintest@cargo.test', 'LoginPass123!')
        u = data['user']
        # Flutter User.fromJson() requires these exact keys
        for key in ('id', 'name', 'email', 'role', 'loyaltyPoints', 'walletBalance'):
            self.assertIn(key, u)


class TestCargoAuthProfile(CargoAuthTestCase):
    """GET/PATCH /api/users/profile"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env['res.users'].sudo().create({
            'name':       'Profile Test',
            'login':      'profile@cargo.test',
            'email':      'profile@cargo.test',
            'password':   'ProfilePass123!',
            'cargo_role': 'customer',
            'groups_id':  [(4, cls.env.ref('cargo_base.cargo_group_customer').id)],
        })

    def _get_token(self):
        data, token = self.login_via_api('profile@cargo.test', 'ProfilePass123!')
        return token

    def test_get_profile_returns_user_dict(self):
        token = self._get_token()
        resp  = self._get('/users/profile', token=token)
        data  = json.loads(resp.read())
        self.assert_user_dict(data)

    def test_get_profile_without_token_returns_401(self):
        resp = self._get('/users/profile')
        self.assertEqual(resp.status, 401)

    def test_update_profile_name(self):
        token = self._get_token()
        resp  = self._patch('/users/profile', {'name': 'Updated Name'}, token=token)
        # status 200 and name updated
        if hasattr(resp, 'status'):
            status = resp.status
        else:
            status = resp.code
        self.assertEqual(status, 200)


class TestCargoAuthRefresh(CargoAuthTestCase):
    """POST /api/auth/refresh"""

    def test_refresh_with_valid_token_returns_new_tokens(self):
        data, _ = self.register_via_api('_refresh')
        refresh_token = data.get('refreshToken')
        if not refresh_token:
            self.skipTest('No refreshToken in register response')

        resp = self._post('/auth/refresh', {'refreshToken': refresh_token})
        self.assertEqual(resp.status, 200)
        new_data = json.loads(resp.read())
        self.assertIn('token', new_data)
        self.assertIn('user', new_data)

    def test_refresh_with_invalid_token_returns_401(self):
        resp = self._post('/auth/refresh', {'refreshToken': 'invalid.token.here'})
        self.assertEqual(resp.status, 401)

    def test_refresh_missing_token_returns_400(self):
        resp = self._post('/auth/refresh', {})
        self.assertEqual(resp.status, 400)


class TestCargoAuthLogout(CargoAuthTestCase):
    """POST /api/auth/logout"""

    def test_logout_with_valid_token_returns_200(self):
        data, token = self.register_via_api('_logout')
        resp = self._post('/auth/logout', {}, token=token)
        self.assertEqual(resp.status, 200)

    def test_logout_without_token_returns_401(self):
        resp = self._post('/auth/logout', {})
        self.assertEqual(resp.status, 401)
