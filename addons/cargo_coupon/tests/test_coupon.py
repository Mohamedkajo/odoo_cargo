# -*- coding: utf-8 -*-
"""cargo_coupon — coupon validation tests."""
from odoo.tests.common import TransactionCase


class TestCargoCoupon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env['res.users'].sudo().create({
            'name': 'Coupon User', 'login': 'coupon@cargo.test',
            'email': 'coupon@cargo.test', 'password': 'Test1234!', 'cargo_role': 'customer',
        })
        cls.coupon_pct = cls.env['cargo.coupon'].sudo().create({
            'code': 'TEST10', 'type': 'percentage', 'discount_value': 10.0,
            'min_order_amount': 50.0, 'max_discount': 100.0,
        })
        cls.coupon_fixed = cls.env['cargo.coupon'].sudo().create({
            'code': 'FIXED30', 'type': 'fixed', 'discount_value': 30.0,
            'min_order_amount': 100.0,
        })

    def test_percentage_discount_calculated(self):
        result = self.coupon_pct.validate_for_cart(self.user.id, cart_subtotal=200.0)
        self.assertTrue(result['valid'])
        self.assertAlmostEqual(result['discountAmount'], 20.0)

    def test_percentage_capped_by_max_discount(self):
        coupon = self.env['cargo.coupon'].sudo().create({
            'code': 'BIG50', 'type': 'percentage', 'discount_value': 50.0, 'max_discount': 25.0,
        })
        result = coupon.validate_for_cart(self.user.id, cart_subtotal=200.0)
        self.assertTrue(result['valid'])
        self.assertAlmostEqual(result['discountAmount'], 25.0)

    def test_fixed_discount(self):
        result = self.coupon_fixed.validate_for_cart(self.user.id, cart_subtotal=150.0)
        self.assertTrue(result['valid'])
        self.assertAlmostEqual(result['discountAmount'], 30.0)

    def test_below_min_order_fails(self):
        result = self.coupon_pct.validate_for_cart(self.user.id, cart_subtotal=10.0)
        self.assertFalse(result['valid'])

    def test_per_user_limit_enforced(self):
        coupon = self.env['cargo.coupon'].sudo().create({
            'code': 'ONETIME', 'type': 'fixed', 'discount_value': 5.0, 'per_user_limit': 1,
        })
        coupon.redeem(self.user.id)
        result = coupon.validate_for_cart(self.user.id, cart_subtotal=0.0)
        self.assertFalse(result['valid'])
