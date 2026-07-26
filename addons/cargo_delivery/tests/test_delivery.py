# -*- coding: utf-8 -*-
"""cargo_delivery — delivery model tests."""
from odoo.tests.common import TransactionCase


class TestCargoDelivery(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cat = cls.env['cargo.store.category'].sudo().create({'name': 'DelTestCat'})
        store = cls.env['cargo.store'].sudo().create({
            'name': 'Delivery Test Store', 'category_id': cat.id,
        })
        product = cls.env['cargo.product'].sudo().create({
            'name': 'Del Product', 'store_id': store.id, 'price': 50.0,
        })
        user = cls.env['res.users'].sudo().create({
            'name': 'Del Customer', 'login': 'delcust@cargo.test',
            'email': 'delcust@cargo.test', 'password': 'Test1234!', 'cargo_role': 'customer',
        })
        cart = cls.env['cargo.cart'].sudo().get_or_create_for_user(user.id)
        cls.env['cargo.cart.line'].sudo().create({
            'cart_id': cart.id, 'product_id': product.id,
            'quantity': 1, 'unit_price': 50.0,
        })
        cls.order = cls.env['cargo.order'].sudo().create({
            'user_id': user.id, 'store_id': store.id,
            'delivery_address': 'Test Address', 'delivery_fee': 15.0, 'subtotal': 50.0,
        })
        d_user = cls.env['res.users'].sudo().create({
            'name': 'Test Driver', 'login': 'testdriver@cargo.test',
            'email': 'testdriver@cargo.test', 'password': 'Test1234!', 'cargo_role': 'driver',
        })
        cls.driver = cls.env['cargo.driver'].sudo().create({'user_id': d_user.id})

    def test_create_delivery_generates_otps(self):
        delivery = self.env['cargo.delivery'].sudo().create({
            'order_id': self.order.id, 'driver_id': self.driver.id,
        })
        self.assertEqual(len(delivery.pickup_otp), 4)
        self.assertEqual(len(delivery.delivery_otp), 4)

    def test_advance_status_valid(self):
        delivery = self.env['cargo.delivery'].sudo().create({
            'order_id': self.order.id,
        })
        delivery.advance_status('picked_up')
        self.assertEqual(delivery.status, 'picked_up')

    def test_advance_status_invalid_raises(self):
        delivery = self.env['cargo.delivery'].sudo().create({
            'order_id': self.order.id,
        })
        with self.assertRaises(ValueError):
            delivery.advance_status('delivered')  # must go assigned→picked_up first

    def test_tracking_dict_shape(self):
        delivery = self.env['cargo.delivery'].sudo().create({
            'order_id': self.order.id, 'driver_id': self.driver.id,
        })
        d = delivery.to_tracking_dict()
        for key in ('deliveryId', 'status', 'driver', 'etaMinutes'):
            self.assertIn(key, d)
