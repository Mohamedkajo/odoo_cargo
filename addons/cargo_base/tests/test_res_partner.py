# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
Tests for the res.partner Cargo extension.

Verifies cargo_role, cargo_is_cargo_user, cargo_full_address,
loyalty_points constraint and API serialisation.
"""

from psycopg2 import IntegrityError

from odoo.tests.common import TransactionCase
from odoo.tools.misc import mute_logger


class TestCargoResPartner(TransactionCase):

    def _make_partner(self, **vals):
        defaults = {'name': 'Test Partner'}
        defaults.update(vals)
        return self.env['res.partner'].sudo().create(defaults)

    # ── cargo_role ────────────────────────────────────────────────────────────

    def test_cargo_role_customer(self):
        partner = self._make_partner(cargo_role='customer')
        self.assertEqual(partner.cargo_role, 'customer')

    def test_cargo_role_vendor(self):
        partner = self._make_partner(cargo_role='vendor')
        self.assertEqual(partner.cargo_role, 'vendor')

    def test_cargo_role_driver(self):
        partner = self._make_partner(cargo_role='driver')
        self.assertEqual(partner.cargo_role, 'driver')

    def test_cargo_role_none_by_default(self):
        partner = self._make_partner()
        self.assertFalse(partner.cargo_role)

    # ── cargo_is_cargo_user ───────────────────────────────────────────────────

    def test_is_cargo_user_true_when_role_set(self):
        partner = self._make_partner(cargo_role='customer')
        self.assertTrue(partner.cargo_is_cargo_user)

    def test_is_cargo_user_false_when_no_role(self):
        partner = self._make_partner()
        self.assertFalse(partner.cargo_is_cargo_user)

    # ── cargo_full_address ────────────────────────────────────────────────────

    def test_full_address_returns_string(self):
        """cargo_full_address must always return a string, never crash."""
        partner = self._make_partner()
        self.assertIsInstance(partner.cargo_full_address, str)

    def test_full_address_includes_city(self):
        partner = self._make_partner(
            street='123 Tahrir Square',
            city='Cairo',
        )
        self.assertIn('Cairo', partner.cargo_full_address)

    def test_full_address_includes_street(self):
        partner = self._make_partner(
            street='123 Tahrir Square',
            city='Cairo',
        )
        self.assertIn('123 Tahrir Square', partner.cargo_full_address)

    # ── cargo_loyalty_points ──────────────────────────────────────────────────

    def test_loyalty_points_default_zero(self):
        partner = self._make_partner()
        self.assertEqual(partner.cargo_loyalty_points, 0)

    def test_loyalty_points_valid_positive(self):
        partner = self._make_partner(cargo_loyalty_points=500)
        self.assertEqual(partner.cargo_loyalty_points, 500)

    def test_loyalty_points_negative_raises_integrity_error(self):
        """
        The DB-level CHECK constraint (cargo_loyalty_points >= 0) must reject
        negative values.  We bypass the ORM to test the raw constraint.
        """
        partner = self._make_partner()
        with mute_logger('odoo.sql_db'):
            with self.assertRaises(IntegrityError):
                with self.env.cr.savepoint():
                    self.env.cr.execute(
                        "UPDATE res_partner "
                        "SET cargo_loyalty_points = -1 "
                        "WHERE id = %s",
                        [partner.id],
                    )

    # ── cargo_to_api_dict ─────────────────────────────────────────────────────

    def test_to_api_dict_structure(self):
        """API dict must contain all keys expected by the Flutter User model."""
        partner = self._make_partner(
            name='Ahmed Hassan',
            email='ahmed@test.com',
            phone='01012345678',
            cargo_role='customer',
            cargo_loyalty_points=100,
        )
        d = partner.cargo_to_api_dict()

        expected_keys = ['id', 'name', 'email', 'phone', 'avatar',
                         'role', 'loyaltyPoints', 'address']
        for key in expected_keys:
            self.assertIn(key, d, f"Key '{key}' missing from cargo_to_api_dict()")

        self.assertEqual(d['name'],          'Ahmed Hassan')
        self.assertEqual(d['email'],         'ahmed@test.com')
        self.assertEqual(d['role'],          'customer')
        self.assertEqual(d['loyaltyPoints'], 100)

    def test_to_api_dict_no_exception_with_minimal_partner(self):
        """cargo_to_api_dict() must not raise even with a bare-minimum partner."""
        partner = self._make_partner()
        try:
            d = partner.cargo_to_api_dict()
        except Exception as exc:
            self.fail(f'cargo_to_api_dict() raised unexpectedly: {exc}')
        self.assertIsInstance(d, dict)

    def test_to_api_dict_avatar_is_string(self):
        """Avatar URL must always be a string (empty or a URL)."""
        partner = self._make_partner(cargo_role='vendor')
        d = partner.cargo_to_api_dict()
        self.assertIsInstance(d['avatar'], str)

    def test_to_api_dict_loyalty_points_is_int(self):
        """loyaltyPoints must be an integer in the API response."""
        partner = self._make_partner(cargo_loyalty_points=250)
        d = partner.cargo_to_api_dict()
        self.assertIsInstance(d['loyaltyPoints'], int)
        self.assertEqual(d['loyaltyPoints'], 250)
