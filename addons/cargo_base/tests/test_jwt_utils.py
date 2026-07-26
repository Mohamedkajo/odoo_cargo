# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
Unit tests for cargo_base.utils.jwt_utils.

All tests are pure Python — no database required.
Uses a fixed test secret so results are deterministic.
"""

import base64
import json
import time

from odoo.tests.common import BaseCase

from ..exceptions import CargoTokenError, CargoTokenExpiredError
from ..utils.jwt_utils import (
    generate_access_token,
    generate_refresh_token,
    verify_token,
    decode_unsafe,
    token_uid,
    hash_token,
    _b64url_encode,
    _b64url_decode,
    _sign,
)

_TEST_SECRET = 'test-secret-do-not-use-in-production-1234567890abcdef'


class TestBase64Utils(BaseCase):

    def test_encode_decode_roundtrip(self):
        original = b'Hello, Cargo!'
        encoded  = _b64url_encode(original)
        decoded  = _b64url_decode(encoded)
        self.assertEqual(decoded, original)

    def test_no_padding_in_encoded(self):
        encoded = _b64url_encode(b'test')
        self.assertNotIn('=', encoded)

    def test_no_plus_or_slash(self):
        """Base64-URL must use - and _ instead of + and /."""
        for data in [b'??', b'>>>', b'\xfb\xff']:
            encoded = _b64url_encode(data)
            self.assertNotIn('+', encoded)
            self.assertNotIn('/', encoded)


class TestGenerateAccessToken(BaseCase):

    def test_returns_three_parts(self):
        token = generate_access_token(42, 'customer', _TEST_SECRET)
        self.assertEqual(len(token.split('.')), 3, 'JWT must have 3 dot-separated parts')

    def test_payload_contains_uid(self):
        token   = generate_access_token(99, 'vendor', _TEST_SECRET)
        payload = decode_unsafe(token)
        self.assertEqual(payload['uid'], 99)

    def test_payload_contains_role(self):
        token   = generate_access_token(1, 'driver', _TEST_SECRET)
        payload = decode_unsafe(token)
        self.assertEqual(payload['role'], 'driver')

    def test_payload_type_is_access(self):
        token   = generate_access_token(1, 'customer', _TEST_SECRET)
        payload = decode_unsafe(token)
        self.assertEqual(payload['type'], 'access')

    def test_payload_exp_in_future(self):
        token   = generate_access_token(1, 'customer', _TEST_SECRET, expiry_secs=3600)
        payload = decode_unsafe(token)
        self.assertGreater(payload['exp'], int(time.time()))

    def test_payload_issuer(self):
        token   = generate_access_token(1, 'customer', _TEST_SECRET)
        payload = decode_unsafe(token)
        self.assertEqual(payload['iss'], 'cargo-marketplace')


class TestGenerateRefreshToken(BaseCase):

    def test_type_is_refresh(self):
        token   = generate_refresh_token(5, _TEST_SECRET)
        payload = decode_unsafe(token)
        self.assertEqual(payload['type'], 'refresh')

    def test_no_role_in_refresh(self):
        token   = generate_refresh_token(5, _TEST_SECRET)
        payload = decode_unsafe(token)
        self.assertNotIn('role', payload)

    def test_longer_expiry_than_access(self):
        access_token   = generate_access_token(1, 'customer', _TEST_SECRET)
        refresh_token  = generate_refresh_token(1, _TEST_SECRET)
        access_exp     = decode_unsafe(access_token)['exp']
        refresh_exp    = decode_unsafe(refresh_token)['exp']
        self.assertGreater(refresh_exp, access_exp)


class TestVerifyToken(BaseCase):

    def test_valid_token_returns_payload(self):
        token   = generate_access_token(7, 'customer', _TEST_SECRET)
        payload = verify_token(token, _TEST_SECRET)
        self.assertEqual(payload['uid'], 7)

    def test_wrong_secret_raises(self):
        token = generate_access_token(7, 'customer', _TEST_SECRET)
        with self.assertRaises(CargoTokenError):
            verify_token(token, 'wrong-secret')

    def test_tampered_payload_raises(self):
        token  = generate_access_token(7, 'customer', _TEST_SECRET)
        parts  = token.split('.')
        # Replace payload with a different base64 to test tamper detection
        evil = base64.urlsafe_b64encode(
            json.dumps({'uid': 1, 'role': 'super_admin', 'exp': 9999999999}).encode()
        ).rstrip(b'=').decode()
        tampered = f'{parts[0]}.{evil}.{parts[2]}'
        with self.assertRaises(CargoTokenError):
            verify_token(tampered, _TEST_SECRET)

    def test_expired_token_raises(self):
        token = generate_access_token(7, 'customer', _TEST_SECRET, expiry_secs=-1)
        with self.assertRaises(CargoTokenExpiredError):
            verify_token(token, _TEST_SECRET)

    def test_malformed_token_raises(self):
        with self.assertRaises(CargoTokenError):
            verify_token('not.a.valid.jwt.string.extra', _TEST_SECRET)

    def test_empty_token_raises(self):
        with self.assertRaises(CargoTokenError):
            verify_token('', _TEST_SECRET)


class TestTokenUID(BaseCase):

    def test_extracts_uid_from_valid_payload(self):
        payload = {'uid': 42, 'role': 'customer'}
        self.assertEqual(token_uid(payload), 42)

    def test_falls_back_to_sub(self):
        payload = {'sub': '99'}
        self.assertEqual(token_uid(payload), 99)

    def test_raises_on_missing_uid(self):
        with self.assertRaises(CargoTokenError):
            token_uid({})

    def test_raises_on_non_numeric(self):
        with self.assertRaises(CargoTokenError):
            token_uid({'uid': 'notanumber'})


class TestHashToken(BaseCase):

    def test_returns_64_char_hex(self):
        h = hash_token('some-token-value')
        self.assertEqual(len(h), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in h))

    def test_same_input_same_hash(self):
        self.assertEqual(hash_token('abc'), hash_token('abc'))

    def test_different_input_different_hash(self):
        self.assertNotEqual(hash_token('abc'), hash_token('xyz'))
