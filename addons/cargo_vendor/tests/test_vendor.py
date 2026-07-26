# -*- coding: utf-8 -*-
"""cargo_vendor — basic model and API tests."""
from odoo.tests.common import TransactionCase


class TestCargoVendor(TransactionCase):

    def _make_vendor_user(self):
        user = self.env['res.users'].sudo().create({
            'name':       'Test Vendor',
            'login':      'vendor_test@cargo.test',
            'email':      'vendor_test@cargo.test',
            'password':   'Test1234!',
            'cargo_role': 'vendor',
        })
        return user

    def test_create_vendor_profile(self):
        user   = self._make_vendor_user()
        vendor = self.env['cargo.vendor'].sudo().create({
            'user_id':       user.id,
            'business_name': 'Test Kitchen',
        })
        self.assertEqual(vendor.business_name, 'Test Kitchen')
        self.assertFalse(vendor.is_approved)

    def test_approve_vendor(self):
        user   = self._make_vendor_user()
        vendor = self.env['cargo.vendor'].sudo().create({
            'user_id':       user.id,
            'business_name': 'Approved Kitchen',
        })
        vendor.action_approve()
        self.assertTrue(vendor.is_approved)
        self.assertIsNotNone(vendor.approved_at)

    def test_vendor_dict_shape(self):
        user   = self._make_vendor_user()
        vendor = self.env['cargo.vendor'].sudo().create({
            'user_id':       user.id,
            'business_name': 'Dict Kitchen',
        })
        d = vendor.to_vendor_dict()
        for key in ('id', 'businessName', 'isApproved', 'commissionRate'):
            self.assertIn(key, d)
