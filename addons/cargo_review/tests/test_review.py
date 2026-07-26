# -*- coding: utf-8 -*-
"""cargo_review — review model tests.

product_id FK → product.template
order_id   FK → sale.order
"""
from odoo.tests.common import TransactionCase


class TestCargoReview(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.store_cat = cls.env['cargo.store.category'].sudo().create({'name': 'ReviewCat'})
        cls.store = cls.env['cargo.store'].sudo().create({
            'name': 'Review Test Store', 'category_id': cls.store_cat.id, 'rating': 0.0,
        })
        cls.customer = cls.env['res.users'].sudo().create({
            'name': 'Reviewer', 'login': 'reviewer@cargo.test',
            'email': 'reviewer@cargo.test', 'password': 'Test1234!', 'cargo_role': 'customer',
        })
        cls.product = cls.env['product.template'].sudo().create({
            'name': 'Review Product', 'type': 'service', 'list_price': 30.0,
            'cargo_store_id': cls.store.id, 'cargo_rating': 0.0, 'cargo_review_count': 0,
        })

    def test_create_store_review(self):
        review = self.env['cargo.review'].sudo().create({
            'user_id':     self.customer.id,
            'review_type': 'store',
            'store_id':    self.store.id,
            'rating':      5,
            'comment':     'Great food!',
        })
        self.assertEqual(review.rating, 5)
        self.assertTrue(review.is_approved)

    def test_rating_out_of_range_rejected(self):
        with self.assertRaises(Exception):
            self.env['cargo.review'].sudo().create({
                'user_id':     self.customer.id,
                'review_type': 'store',
                'store_id':    self.store.id,
                'rating':      6,
            })

    def test_create_product_review(self):
        review = self.env['cargo.review'].sudo().create({
            'user_id':     self.customer.id,
            'review_type': 'product',
            'product_id':  self.product.id,
            'rating':      4,
        })
        self.assertEqual(review.rating, 4)

    def test_review_dict_shape(self):
        review = self.env['cargo.review'].sudo().create({
            'user_id':     self.customer.id,
            'review_type': 'store',
            'store_id':    self.store.id,
            'rating':      3,
        })
        d = review.to_review_dict()
        for key in ('id', 'reviewType', 'rating', 'comment', 'createdAt'):
            self.assertIn(key, d, f'Missing key: {key}')
