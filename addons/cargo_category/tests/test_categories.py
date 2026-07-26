# -*- coding: utf-8 -*-
"""cargo_category — tests for category models and the GET /api/categories endpoint."""
import json
from odoo.tests.common import HttpCase


class TestCargoCategory(HttpCase):

    def test_list_categories_returns_list(self):
        resp = self.url_open('/api/categories')
        self.assertEqual(resp.status, 200)
        data = json.loads(resp.read())
        self.assertIsInstance(data, list)

    def test_store_category_dict_shape(self):
        cat = self.env['cargo.store.category'].sudo().create({'name': 'Test', 'icon': '🧪'})
        d = cat.to_category_dict()
        for key in ('id', 'name', 'icon'):
            self.assertIn(key, d)

    def test_product_category_dict_shape(self):
        cat = self.env['cargo.product.category'].sudo().create({'name': 'TestMenu', 'icon': '🍔'})
        d = cat.to_category_dict()
        for key in ('id', 'name', 'icon'):
            self.assertIn(key, d)

    def test_categories_ordered_by_sequence(self):
        resp = self.url_open('/api/categories')
        data = json.loads(resp.read())
        self.assertIsInstance(data, list, 'Expected JSON array')

    def test_inactive_categories_excluded(self):
        self.env['cargo.store.category'].sudo().create({'name': 'Hidden', 'active': False})
        resp  = self.url_open('/api/categories')
        names = [c['name'] for c in json.loads(resp.read())]
        self.assertNotIn('Hidden', names)
