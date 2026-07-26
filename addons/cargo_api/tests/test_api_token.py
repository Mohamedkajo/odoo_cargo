# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
Tests for the cargo.api.token model.

Verifies:
  - Token creation with hash validation
  - is_expired / is_valid computed fields
  - Revocation via action_revoke()
  - cargo_revoke_all_for_user()
  - cargo_cleanup_expired() removes old rows
  - Idempotent revocation raises ValidationError
"""

import datetime
import time

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

from cargo_base.utils.jwt_utils import hash_token


class TestCargoApiToken(TransactionCase):

    def _now_plus(self, **delta_kwargs):
        return datetime.datetime.utcnow() + datetime.timedelta(**delta_kwargs)

    def _now_minus(self, **delta_kwargs):
        return datetime.datetime.utcnow() - datetime.timedelta(**delta_kwargs)

    def _make_token(self, user=None, expires_offset_days=30, revoked=False,
                    raw_token=None):
        if user is None:
            user = self.env.user
        if raw_token is None:
            raw_token = f'test_token_{user.id}_{time.time()}'
        expires = self._now_plus(days=expires_offset_days)
        return self.env['cargo.api.token'].sudo().create({
            'user_id':    user.id,
            'token_hash': hash_token(raw_token),
            'expires_at': expires.strftime('%Y-%m-%d %H:%M:%S'),
            'is_revoked': revoked,
            'ip_address': '127.0.0.1',
            'device_info': 'Test Device',
        })

    # ── Token creation ────────────────────────────────────────────────────────

    def test_create_token_succeeds(self):
        token = self._make_token()
        self.assertTrue(token.id)
        self.assertEqual(token.ip_address, '127.0.0.1')

    def test_create_requires_token_hash(self):
        expires = self._now_plus(days=30).strftime('%Y-%m-%d %H:%M:%S')
        with self.assertRaises(ValidationError):
            self.env['cargo.api.token'].sudo().create({
                'user_id':    self.env.user.id,
                'token_hash': '',
                'expires_at': expires,
            })

    def test_token_hash_must_be_at_least_32_chars(self):
        expires = self._now_plus(days=30).strftime('%Y-%m-%d %H:%M:%S')
        with self.assertRaises(ValidationError):
            self.env['cargo.api.token'].sudo().create({
                'user_id':    self.env.user.id,
                'token_hash': 'short',
                'expires_at': expires,
            })

    def test_token_hash_unique_constraint(self):
        token_a = self._make_token(raw_token='unique_tok_a')
        from psycopg2 import IntegrityError
        from odoo.tools.misc import mute_logger
        with mute_logger('odoo.sql_db'):
            with self.assertRaises(IntegrityError):
                with self.env.cr.savepoint():
                    # Try to create another token with the same hash
                    expires = self._now_plus(days=30).strftime('%Y-%m-%d %H:%M:%S')
                    self.env['cargo.api.token'].sudo().create({
                        'user_id':    self.env.user.id,
                        'token_hash': token_a.token_hash,
                        'expires_at': expires,
                    })

    # ── Computed fields ───────────────────────────────────────────────────────

    def test_is_valid_true_for_fresh_token(self):
        token = self._make_token(expires_offset_days=30)
        self.assertTrue(token.is_valid)
        self.assertFalse(token.is_expired)
        self.assertFalse(token.is_revoked)

    def test_is_expired_true_for_past_expiry(self):
        token = self._make_token(expires_offset_days=-1)
        self.assertTrue(token.is_expired)
        self.assertFalse(token.is_valid)

    def test_is_valid_false_when_revoked(self):
        token = self._make_token(revoked=True)
        self.assertFalse(token.is_valid)

    def test_display_name_not_empty(self):
        token = self._make_token()
        self.assertTrue(token.display_name)
        self.assertIsInstance(token.display_name, str)

    # ── Revocation ────────────────────────────────────────────────────────────

    def test_action_revoke(self):
        token = self._make_token()
        self.assertFalse(token.is_revoked)
        token.action_revoke()
        self.assertTrue(token.is_revoked)

    def test_action_revoke_already_revoked_raises(self):
        token = self._make_token(revoked=True)
        with self.assertRaises(ValidationError):
            token.action_revoke()

    def test_revoke_all_for_user(self):
        user = self.env.user
        t1 = self._make_token(user=user, raw_token='tok_multi_1')
        t2 = self._make_token(user=user, raw_token='tok_multi_2')
        self.assertFalse(t1.is_revoked)
        self.assertFalse(t2.is_revoked)

        self.env['cargo.api.token'].sudo().cargo_revoke_all_for_user(user.id)

        self.assertTrue(t1.is_revoked)
        self.assertTrue(t2.is_revoked)

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def test_cleanup_removes_expired_tokens(self):
        # Create a token that expired 8 days ago (past the 7-day cleanup cutoff)
        old_token = self._make_token(expires_offset_days=-8)
        old_id = old_token.id

        # Verify it exists
        self.assertTrue(self.env['cargo.api.token'].sudo().browse(old_id).exists())

        count = self.env['cargo.api.token'].sudo().cargo_cleanup_expired()
        self.assertGreater(count, 0)

        # Verify it was removed
        self.assertFalse(self.env['cargo.api.token'].sudo().browse(old_id).exists())

    def test_cleanup_preserves_valid_tokens(self):
        valid_token = self._make_token(expires_offset_days=30)
        valid_id = valid_token.id

        self.env['cargo.api.token'].sudo().cargo_cleanup_expired()

        # Valid token must still exist
        self.assertTrue(self.env['cargo.api.token'].sudo().browse(valid_id).exists())
