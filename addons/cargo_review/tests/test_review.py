# -*- coding: utf-8 -*-
"""cargo_review — review model tests."""
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestCargoReview(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cat = cls.env['cargo.store.category'].sudo().create({'name': 'RevTestCat'})
        cls.store = cls.env['cargo.store'].sudo().create({
            'name': 'Review Test Store', 'category_id': cat.id, 'rating': 0, 'review_count': 0,
        })
        cls.product = cls.env['cargo.product'].sudo().create({
            'name': 'Review Product', 'store_id': cls.store.id, 'price': 30.0,
        })
        cls.user = cls.env['res.users'].sudo().create({
            'name': 'Reviewer', 'login': 'reviewer@cargo.test',
            'email': 'reviewer@cargo.test', 'password': 'Test1234!', 'cargo_role': 'customer',
        })

    def test_create_store_review(self):
        review = self.env['cargo.review'].sudo().create({
            'user_id': self.user.id, 'review_type': 'store',
            'store_id': self.store.id, 'rating': 5, 'body': 'Excellent!',
        })
        self.assertEqual(review.rating, 5)

    def test_rating_recomputed_on_store(self):
        self.env['cargo.review'].sudo().create({
            'user_id': self.user.id, 'review_type': 'store',
            'store_id': self.store.id, 'rating': 4,
        })
        self.assertAlmostEqual(self.store.rating, 4.0, places=0)
        self.assertGreaterEqual(self.store.review_count, 1)

    def test_rating_out_of_range_fails(self):
        with self.assertRaises(Exception):
            self.env['cargo.review'].sudo().create({
                'user_id': self.user.id, 'review_type': 'store',
                'store_id': self.store.id, 'rating': 6,
            })

    def test_store_review_requires_store(self):
        with self.assertRaises(ValidationError):
            self.env['cargo.review'].sudo().create({
                'user_id': self.user.id, 'review_type': 'store', 'rating': 3,
            })

    def test_review_dict_shape(self):
        review = self.env['cargo.review'].sudo().create({
            'user_id': self.user.id, 'review_type': 'store',
            'store_id': self.store.id, 'rating': 3,
        })
        d = review.to_review_dict()
        for key in ('id', 'userId', 'rating', 'createdAt'):
            self.assertIn(key, d)
