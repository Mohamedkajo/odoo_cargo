# -*- coding: utf-8 -*-
"""
cargo_store — Integration tests for store listing endpoints.
"""
import json

from odoo.tests.common import HttpCase


class TestCargoStores(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cat = cls.env['cargo.store.category'].sudo().create({
            'name': 'Test Category', 'icon': '🧪',
        })
        cls.store = cls.env['cargo.store'].sudo().create({
            'name': 'Test Store',
            'category_id': cls.cat.id,
            'is_featured': True,
            'is_online': True,
            'is_open': True,
            'rating': 4.5,
        })

    def _get(self, path):
        return self.url_open('/api' + path)

    def _json(self, path):
        resp = self._get(path)
        return json.loads(resp.read())

    def test_get_categories_returns_list(self):
        data = self._json('/categories')
        self.assertIsInstance(data, list)
        self.assertTrue(any(c['name'] == 'Test Category' for c in data))

    def test_list_stores_returns_data(self):
        data = self._json('/stores')
        self.assertIn('data', data)
        self.assertIn('total', data)
        self.assertIsInstance(data['data'], list)

    def test_store_dict_has_flutter_fields(self):
        data = self._json('/stores')
        if data['data']:
            s = data['data'][0]
            for key in ('id', 'name', 'rating', 'deliveryFee', 'isOpen', 'isFeatured'):
                self.assertIn(key, s, f'Missing Flutter field: {key}')

    def test_get_featured_stores(self):
        data = self._json('/stores/featured')
        self.assertIsInstance(data, list)
        for s in data:
            self.assertTrue(s['isFeatured'])

    def test_get_online_stores(self):
        data = self._json('/stores/online')
        self.assertIsInstance(data, list)
        for s in data:
            self.assertTrue(s['isOnline'])

    def test_get_store_detail(self):
        data = self._json(f'/stores/{self.store.id}')
        self.assertEqual(data['id'], self.store.id)
        self.assertEqual(data['name'], 'Test Store')

    def test_get_store_not_found(self):
        resp = self._get('/stores/999999')
        self.assertEqual(resp.status, 404)

    def test_get_store_categories(self):
        data = self._json(f'/stores/{self.store.id}/categories')
        self.assertIsInstance(data, list)
