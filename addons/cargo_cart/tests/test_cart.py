# -*- coding: utf-8 -*-
"""cargo_cart — shopping cart model tests.

Cart lines reference product.template (cargo_store_id required).
"""
from odoo.tests.common import TransactionCase


class TestCargoCart(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env['res.users'].sudo().create({
            'name':       'Cart User',
            'login':      'cartuser@cargo.test',
            'email':      'cartuser@cargo.test',
            'password':   'Test1234!',
            'cargo_role': 'customer',
        })
        cat = cls.env['cargo.store.category'].sudo().create({'name': 'CartCat'})
        cls.store = cls.env['cargo.store'].sudo().create({
            'name': 'Cart Test Store', 'category_id': cat.id,
        })
        # product.template with cargo_store_id (native model)
        cls.product = cls.env['product.template'].sudo().create({
            'name':               'Cart Product',
            'type':               'service',
            'list_price':         50.0,
            'cargo_store_id':     cls.store.id,
            'cargo_is_available': True,
        })

    def test_get_or_create_cart(self):
        cart = self.env['cargo.cart'].sudo().get_or_create_for_user(self.user.id)
        self.assertEqual(cart.user_id.id, self.user.id)

    def test_idempotent_get_or_create(self):
        cart1 = self.env['cargo.cart'].sudo().get_or_create_for_user(self.user.id)
        cart2 = self.env['cargo.cart'].sudo().get_or_create_for_user(self.user.id)
        self.assertEqual(cart1.id, cart2.id)

    def test_add_cart_line(self):
        cart = self.env['cargo.cart'].sudo().get_or_create_for_user(self.user.id)
        line = self.env['cargo.cart.line'].sudo().create({
            'cart_id':    cart.id,
            'product_id': self.product.id,
            'name':       self.product.name,
            'price':      50.0,
            'quantity':   2,
        })
        self.assertEqual(line.quantity, 2)
        self.assertEqual(line.price, 50.0)

    def test_cart_to_dict_shape(self):
        cart = self.env['cargo.cart'].sudo().get_or_create_for_user(self.user.id)
        d = cart.to_cart_dict()
        for key in ('id', 'items', 'subtotal', 'deliveryFee', 'total'):
            self.assertIn(key, d, f'Missing key in cart dict: {key}')

    def test_clear_cart(self):
        cart = self.env['cargo.cart'].sudo().get_or_create_for_user(self.user.id)
        self.env['cargo.cart.line'].sudo().create({
            'cart_id':    cart.id,
            'product_id': self.product.id,
            'name':       'Test item',
            'price':      50.0,
            'quantity':   1,
        })
        cart.clear()
        self.assertFalse(cart.line_ids)
