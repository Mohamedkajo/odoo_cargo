# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo_category — tests.

Covers:
  • cargo.store.category CRUD and serialisation
  • product.category cargo extension (cargo_base fields)
  • GET /api/categories endpoint
"""
import json
from odoo.tests.common import HttpCase, TransactionCase


class TestCargoStoreCategory(TransactionCase):

    def test_store_category_create_and_dict(self):
        cat = self.env['cargo.store.category'].sudo().create({
            'name': 'TestCat',
            'icon': '🧪',
            'sequence': 99,
        })
        d = cat.to_category_dict()
        self.assertEqual(d['id'], cat.id)
        self.assertEqual(d['name'], 'TestCat')
        self.assertEqual(d['icon'], '🧪')

    def test_inactive_store_category_excluded(self):
        self.env['cargo.store.category'].sudo().create({
            'name': 'HiddenCat', 'active': False,
        })
        cats = self.env['cargo.store.category'].sudo().search([('name', '=', 'HiddenCat')])
        # search without active_test should still find it
        self.assertTrue(cats)
        # default search (active_test=True) must exclude it
        cats_active = self.env['cargo.store.category'].sudo().search(
            [('name', '=', 'HiddenCat'), ('active', '=', True)]
        )
        self.assertFalse(cats_active)

    def test_store_category_ordered_by_sequence(self):
        self.env['cargo.store.category'].sudo().create([
            {'name': 'Z', 'sequence': 90},
            {'name': 'A', 'sequence': 1},
        ])
        cats = self.env['cargo.store.category'].sudo().search([], order='sequence, name')
        sequences = [c.sequence for c in cats]
        self.assertEqual(sequences, sorted(sequences))


class TestCargoProductCategory(TransactionCase):
    """product.category extended with cargo_base fields."""

    def test_product_category_cargo_fields(self):
        cat = self.env['product.category'].sudo().create({
            'name': 'Test Menu Section',
            'cargo_icon': '🍔',
            'cargo_is_active': True,
            'cargo_sort_order': 5,
        })
        self.assertEqual(cat.cargo_icon, '🍔')
        self.assertTrue(cat.cargo_is_active)
        self.assertEqual(cat.cargo_sort_order, 5)

    def test_product_category_api_dict(self):
        cat = self.env['product.category'].sudo().create({
            'name': 'Drinks',
            'cargo_icon': '🥤',
            'cargo_slug': 'drinks',
        })
        d = cat.cargo_to_api_dict()
        self.assertIn('id', d)
        self.assertEqual(d['name'], 'Drinks')
        self.assertEqual(d['icon'], '🥤')

    def test_slug_auto_generated_on_create(self):
        cat = self.env['product.category'].sudo().create({'name': 'Hot Drinks'})
        self.assertEqual(cat.cargo_slug, 'hot-drinks')

    def test_slug_uniqueness_constraint(self):
        self.env['product.category'].sudo().create({
            'name': 'Cat1', 'cargo_slug': 'unique-slug',
        })
        with self.assertRaises(Exception):
            self.env['product.category'].sudo().create({
                'name': 'Cat2', 'cargo_slug': 'unique-slug',
            })


class TestCargoCategoryEndpoints(HttpCase):

    def test_list_categories_returns_list(self):
        resp = self.url_open('/api/categories')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIsInstance(data, list)

    def test_inactive_store_categories_excluded(self):
        self.env['cargo.store.category'].sudo().create({
            'name': 'Hidden', 'active': False,
        })
        resp  = self.url_open('/api/categories')
        names = [c['name'] for c in json.loads(resp.content)]
        self.assertNotIn('Hidden', names)
