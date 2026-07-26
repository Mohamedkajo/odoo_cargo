# -*- coding: utf-8 -*-
"""cargo_favorite — favourite toggle tests."""
from odoo.tests.common import TransactionCase


class TestCargoFavorite(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env['res.users'].sudo().create({
            'name': 'Fav User', 'login': 'favuser@cargo.test',
            'email': 'favuser@cargo.test', 'password': 'Test1234!', 'cargo_role': 'customer',
        })
        cat = cls.env['cargo.store.category'].sudo().create({'name': 'FavCat'})
        cls.store = cls.env['cargo.store'].sudo().create({
            'name': 'Fav Test Store', 'category_id': cat.id,
        })

    def test_toggle_adds_favorite(self):
        added = self.env['cargo.favorite'].sudo().toggle(
            user_id=self.user.id, fav_type='store', store_id=self.store.id
        )
        self.assertTrue(added)

    def test_toggle_removes_favorite(self):
        self.env['cargo.favorite'].sudo().toggle(
            user_id=self.user.id, fav_type='store', store_id=self.store.id
        )
        removed = self.env['cargo.favorite'].sudo().toggle(
            user_id=self.user.id, fav_type='store', store_id=self.store.id
        )
        self.assertFalse(removed)

    def test_favorites_list_for_user(self):
        self.env['cargo.favorite'].sudo().toggle(
            user_id=self.user.id, fav_type='store', store_id=self.store.id
        )
        favs = self.env['cargo.favorite'].sudo().search([('user_id', '=', self.user.id)])
        self.assertGreaterEqual(len(favs), 1)
