# -*- coding: utf-8 -*-
"""cargo_inventory — stock tracking tests.

product_id FK is product.template (with cargo_store_id set).
"""
from odoo.tests.common import TransactionCase


class TestCargoInventory(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.store_cat = cls.env['cargo.store.category'].sudo().create({'name': 'InvTestCat'})
        cls.store = cls.env['cargo.store'].sudo().create({
            'name': 'Inventory Test Store', 'category_id': cls.store_cat.id,
        })
        # product.template with cargo_store_id (native model)
        cls.product = cls.env['product.template'].sudo().create({
            'name':               'Inv Product',
            'type':               'service',
            'list_price':         10.0,
            'cargo_store_id':     cls.store.id,
            'cargo_is_available': True,
        })

    def test_create_inventory_entry(self):
        inv = self.env['cargo.inventory'].sudo().create({
            'store_id':   self.store.id,
            'product_id': self.product.id,
            'quantity':   50,
        })
        self.assertEqual(inv.quantity,     50)
        self.assertEqual(inv.available_qty, 50)

    def test_zero_stock_marks_unavailable(self):
        inv = self.env['cargo.inventory'].sudo().create({
            'store_id':   self.store.id,
            'product_id': self.product.id,
            'quantity':   0,
        })
        # _sync_product_availability should have set cargo_is_available = False
        self.assertFalse(inv.product_id.cargo_is_available)

    def test_adjust_stock(self):
        inv = self.env['cargo.inventory'].sudo().create({
            'store_id':   self.store.id,
            'product_id': self.product.id,
            'quantity':   10,
        })
        inv.adjust(-3)
        self.assertEqual(inv.quantity, 7)

    def test_adjust_cannot_go_below_zero(self):
        inv = self.env['cargo.inventory'].sudo().create({
            'store_id':   self.store.id,
            'product_id': self.product.id,
            'quantity':   2,
        })
        inv.adjust(-100)
        self.assertEqual(inv.quantity, 0)

    def test_low_stock_flag(self):
        inv = self.env['cargo.inventory'].sudo().create({
            'store_id':   self.store.id,
            'product_id': self.product.id,
            'quantity':   3,
            'alert_qty':  5,
        })
        self.assertTrue(inv.is_low_stock)

    def test_to_inventory_dict_shape(self):
        inv = self.env['cargo.inventory'].sudo().create({
            'store_id':   self.store.id,
            'product_id': self.product.id,
            'quantity':   5,
        })
        d = inv.to_inventory_dict()
        for key in ('id', 'productId', 'storeId', 'quantity', 'availableQty', 'isLowStock'):
            self.assertIn(key, d, f'Missing key: {key}')
