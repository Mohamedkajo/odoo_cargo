# -*- coding: utf-8 -*-
"""cargo_vendor — vendor profile tests.

Vendor fields are on res.partner (user.partner_id), not a custom cargo.vendor model.
"""
from odoo.tests.common import TransactionCase


class TestCargoVendor(TransactionCase):

    def _make_vendor_user(self, suffix=''):
        user = self.env['res.users'].sudo().create({
            'name':       f'Test Vendor{suffix}',
            'login':      f'vendor_test{suffix}@cargo.test',
            'email':      f'vendor_test{suffix}@cargo.test',
            'password':   'Test1234!',
            'cargo_role': 'vendor',
        })
        return user

    def test_vendor_partner_has_cargo_fields(self):
        user = self._make_vendor_user('A')
        user.partner_id.sudo().write({
            'cargo_vendor_business_name': 'Test Kitchen',
        })
        self.assertEqual(user.partner_id.cargo_vendor_business_name, 'Test Kitchen')
        self.assertFalse(user.partner_id.cargo_vendor_is_approved)

    def test_approve_vendor(self):
        user = self._make_vendor_user('B')
        user.partner_id.cargo_vendor_approve()
        self.assertTrue(user.partner_id.cargo_vendor_is_approved)
        self.assertIsNotNone(user.partner_id.cargo_vendor_approved_at)

    def test_reject_vendor(self):
        user = self._make_vendor_user('C')
        user.partner_id.cargo_vendor_reject('Incomplete documents')
        self.assertFalse(user.partner_id.cargo_vendor_is_approved)
        self.assertEqual(user.partner_id.cargo_vendor_reject_reason, 'Incomplete documents')

    def test_vendor_to_api_dict_shape(self):
        user = self._make_vendor_user('D')
        user.partner_id.sudo().write({
            'cargo_vendor_business_name': 'Dict Kitchen',
        })
        d = user.partner_id.cargo_vendor_to_api_dict()
        for key in ('id', 'businessName', 'isApproved', 'commissionRate'):
            self.assertIn(key, d, f'Missing key: {key}')

    def test_default_commission_rate(self):
        user = self._make_vendor_user('E')
        self.assertEqual(user.partner_id.cargo_vendor_commission_rate, 15.0)
