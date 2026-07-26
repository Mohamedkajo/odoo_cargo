# -*- coding: utf-8 -*-
"""cargo_product — Integration tests for product catalogue endpoints."""
import json
from odoo.tests.common import HttpCase


class TestCargoProducts(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create store category, store, product category, and test products
        store_cat = cls.env['cargo.store.category'].sudo().create({
            'name': 'Test Food', 'icon': '🍔',
        })
        cls.store = cls.env['cargo.store'].sudo().create({
            'name': 'Test Product Store',
            'category_id': store_cat.id,
            'is_open': True,
            'is_online': True,
        })
        cls.prod_cat = cls.env['cargo.product.category'].sudo().create({
            'name': 'Burgers',
            'store_id': cls.store.id,
        })
        cls.product = cls.env['cargo.product'].sudo().create({
            'name': 'Test Burger',
            'store_id': cls.store.id,
            'category_id': cls.prod_cat.id,
            'price': 75.0,
            'original_price': 90.0,
            'is_available': True,
            'is_featured': True,
            'rating': 4.7,
            'image': 'https://example.com/burger.jpg',
        })
        cls.flash_product = cls.env['cargo.product'].sudo().create({
            'name': 'Flash Burger',
            'store_id': cls.store.id,
            'price': 50.0,
            'is_available': True,
            'is_flash_sale': True,
            'flash_sale_price': 40.0,
        })

    def _get(self, path):
        return self.url_open('/api' + path)

    def _json(self, path):
        return json.loads(self._get(path).read())

    def test_list_products_returns_data_and_total(self):
        data = self._json('/products')
        self.assertIn('data', data)
        self.assertIn('total', data)

    def test_product_dict_has_flutter_fields(self):
        data = self._json('/products')
        self.assertTrue(data['data'], 'No products returned')
        p = data['data'][0]
        for key in ('id', 'name', 'price', 'originalPrice', 'isAvailable',
                    'rating', 'reviewCount', 'discountPercent'):
            self.assertIn(key, p, f'Missing Flutter field: {key}')

    def test_discount_percent_computed(self):
        data = self._json(f'/products/{self.product.id}')
        self.assertGreater(data['discountPercent'], 0)

    def test_trending_products(self):
        data = self._json('/products/trending')
        self.assertIsInstance(data, list)
        for p in data:
            self.assertTrue(p['isAvailable'])

    def test_get_product_detail(self):
        data = self._json(f'/products/{self.product.id}')
        self.assertEqual(data['id'], self.product.id)
        self.assertIn('gallery', data)
        self.assertIn('variants', data)
        self.assertIn('addons', data)

    def test_get_product_not_found(self):
        resp = self._get('/products/999999')
        self.assertEqual(resp.status, 404)

    def test_flash_sales(self):
        data = self._json('/flash-sales')
        self.assertIsInstance(data, list)
        for p in data:
            self.assertIn('flashSalePrice', p)

    def test_filter_by_store(self):
        data = self._json(f'/products?storeId={self.store.id}')
        for p in data['data']:
            self.assertEqual(p['storeId'], self.store.id)

    def test_search_by_name(self):
        data = self._json('/products?search=Burger')
        self.assertTrue(any('Burger' in p['name'] for p in data['data']))
