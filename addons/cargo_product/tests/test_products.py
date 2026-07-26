# -*- coding: utf-8 -*-
"""cargo_product — Integration tests for product catalogue endpoints.

Products are product.template records with cargo_store_id set.
"""
import json
from odoo.tests.common import HttpCase, TransactionCase


class TestCargoProductModel(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        store_cat = cls.env['cargo.store.category'].sudo().create({
            'name': 'Test Food', 'icon': '🍔',
        })
        cls.store = cls.env['cargo.store'].sudo().create({
            'name': 'Test Product Store',
            'category_id': store_cat.id,
            'is_open': True,
        })
        cls.prod_cat = cls.env['product.category'].sudo().create({
            'name': 'Burgers',
            'cargo_is_active': True,
        })
        # Create product.template with cargo fields
        cls.product = cls.env['product.template'].sudo().create({
            'name':               'Test Burger',
            'type':               'service',
            'list_price':         75.0,
            'cargo_store_id':     cls.store.id,
            'categ_id':           cls.prod_cat.id,
            'cargo_is_available': True,
            'cargo_is_featured':  True,
            'cargo_rating':       4.7,
            'cargo_image_url':    'https://example.com/burger.jpg',
            'cargo_original_price': 90.0,
            'cargo_discount_percent': 17.0,
        })
        cls.flash_product = cls.env['product.template'].sudo().create({
            'name':                  'Flash Burger',
            'type':                  'service',
            'list_price':            50.0,
            'cargo_store_id':        cls.store.id,
            'cargo_is_available':    True,
            'cargo_is_flash_sale':   True,
            'cargo_flash_sale_price': 40.0,
        })

    def test_cargo_to_api_dict_shape(self):
        d = self.product.cargo_to_api_dict()
        for key in ('id', 'name', 'price', 'storeId', 'storeName',
                    'isAvailable', 'isFeatured', 'rating', 'isFlashSale'):
            self.assertIn(key, d, f'Missing key: {key}')

    def test_cargo_to_api_detail_dict_has_addons_and_variants(self):
        d = self.product.cargo_to_api_detail_dict()
        self.assertIn('addons',   d)
        self.assertIn('variants', d)

    def test_effective_price_applied(self):
        d = self.product.cargo_to_api_dict()
        # cargo_effective_price should be ≤ list_price when discount set
        self.assertLessEqual(d['price'], self.product.list_price)

    def test_flash_sale_dict_includes_flash_fields(self):
        d = self.flash_product.cargo_to_api_detail_dict()
        self.assertTrue(d['isFlashSale'])
        self.assertIn('flashSalePrice', d)

    def test_addon_to_dict(self):
        addon = self.env['cargo.product.addon'].sudo().create({
            'product_tmpl_id': self.product.id,
            'name': 'Extra Cheese',
            'price': 10.0,
        })
        d = addon.to_dict()
        self.assertEqual(d['name'],  'Extra Cheese')
        self.assertEqual(d['price'], 10.0)

    def test_variant_to_dict(self):
        import json as _json
        variant = self.env['cargo.product.variant'].sudo().create({
            'product_tmpl_id': self.product.id,
            'name': 'Size',
            'options': '["Small", "Large"]',
            'price_delta': 15.0,
        })
        d = variant.to_dict()
        self.assertIn('Small', d['options'])


class TestCargoProductEndpoints(HttpCase):

    def test_list_products_returns_data_and_total(self):
        resp = self.url_open('/api/products')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIn('data',  data)
        self.assertIn('total', data)

    def test_trending_returns_list(self):
        resp = self.url_open('/api/products/trending')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIsInstance(data, list)

    def test_flash_sales_returns_list(self):
        resp = self.url_open('/api/flash-sales')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIsInstance(data, list)

    def test_product_not_found_returns_404(self):
        resp = self.url_open('/api/products/999999999')
        self.assertEqual(resp.status_code, 404)
