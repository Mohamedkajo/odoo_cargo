# -*- coding: utf-8 -*-
"""cargo_inventory — stock tracking tests."""
from odoo.tests.common import TransactionCase


class TestCargoInventory(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.store_cat = cls.env['cargo.store.category'].sudo().create({'name': 'InvTestCat'})
        cls.store = cls.env['cargo.store'].sudo().create({
            'name': 'Inventory Test Store', 'category_id': cls.store_cat.id,
        })
        cls.product = cls.env['cargo.product'].sudo().create({
            'name': 'Inv Product', 'store_id': cls.store.id, 'price': 10.0,
        })

    def test_create_inventory_entry(self):
        inv = self.env['cargo.inventory'].sudo().create({
            'store_id': self.store.id, 'product_id': self.product.id, 'quantity': 50,
        })
        self.assertEqual(inv.available_qty, 50)

    def test_zero_stock_marks_unavailable(self):
        inv = self.env['cargo.inventory'].sudo().create({
            'store_id': self.store.id, 'product_id': self.product.id, 'quantity': 0,
        })
        self.assertFalse(inv.product_id.is_available)

    def test_adjust_stock(self):
        inv = self.env['cargo.inventory'].sudo().create({
            'store_id': self.store.id, 'product_id': self.product.id, 'quantity': 10,
        })
        inv.adjust(-3)
        self.assertEqual(inv.quantity, 7)

    def test_adjust_cannot_go_below_zero(self):
        inv = self.env['cargo.inventory'].sudo().create({
            'store_id': self.store.id, 'product_id': self.product.id, 'quantity': 2,
        })
        inv.adjust(-100)
        self.assertEqual(inv.quantity, 0)

    def test_dict_shape(self):
        inv = self.env['cargo.inventory'].sudo().create({
            'store_id': self.store.id, 'product_id': self.product.id, 'quantity': 5,
        })
        d = inv.to_inventory_dict()
        for key in ('id', 'productId', 'storeId', 'quantity', 'availableQty'):
            self.assertIn(key, d)
