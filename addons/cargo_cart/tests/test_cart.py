# -*- coding: utf-8 -*-
"""cargo_cart — cart model tests."""
from odoo.tests.common import TransactionCase


class TestCargoCart(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env['res.users'].sudo().create({
            'name': 'Cart User', 'login': 'cartuser@cargo.test',
            'email': 'cartuser@cargo.test', 'password': 'Test1234!', 'cargo_role': 'customer',
        })
        cat = cls.env['cargo.store.category'].sudo().create({'name': 'CartCat'})
        cls.store = cls.env['cargo.store'].sudo().create({
            'name': 'Cart Test Store', 'category_id': cat.id,
        })
        cls.product = cls.env['cargo.product'].sudo().create({
            'name': 'Cart Product', 'store_id': cls.store.id, 'price': 50.0,
        })

    def test_get_or_create_cart(self):
        cart = self.env['cargo.cart'].sudo().get_or_create_for_user(self.user.id)
        self.assertEqual(cart.user_id.id, self.user.id)

    def test_idempotent_get_or_create(self):
        cart1 = self.env['cargo.cart'].sudo().get_or_create_for_user(self.user.id)
        cart2 = self.env['cargo.cart'].sudo().get_or_create_for_user(self.user.id)
        self.assertEqual(cart1.id, cart2.id)

    def test_add_item(self):
        cart = self.env['cargo.cart'].sudo().get_or_create_for_user(self.user.id)
        line = self.env['cargo.cart.line'].sudo().create({
            'cart_id': cart.id, 'product_id': self.product.id,
            'quantity': 2, 'unit_price': 50.0,
        })
        self.assertEqual(line.subtotal, 100.0)

    def test_cart_dict_shape(self):
        cart = self.env['cargo.cart'].sudo().get_or_create_for_user(self.user.id)
        d = cart.to_cart_dict()
        for key in ('id', 'userId', 'items', 'subtotal'):
            self.assertIn(key, d)
