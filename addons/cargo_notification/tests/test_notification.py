# -*- coding: utf-8 -*-
"""cargo_notification — notification send and read tests."""
from odoo.tests.common import TransactionCase


class TestCargoNotification(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env['res.users'].sudo().create({
            'name': 'Notif User', 'login': 'notifuser@cargo.test',
            'email': 'notifuser@cargo.test', 'password': 'Test1234!', 'cargo_role': 'customer',
        })

    def test_send_to_user(self):
        n = self.env['cargo.notification'].sudo().send_to_user(
            user_id=self.user.id,
            notif_type='order',
            title='Order Confirmed',
            body='Your order #001 is confirmed.',
        )
        self.assertFalse(n.is_read)
        self.assertEqual(n.title, 'Order Confirmed')

    def test_mark_read(self):
        n = self.env['cargo.notification'].sudo().send_to_user(
            user_id=self.user.id, notif_type='system',
            title='Test', body='Test body',
        )
        n.action_mark_read()
        self.assertTrue(n.is_read)

    def test_unread_count_computed(self):
        self.env['cargo.notification'].sudo().send_to_user(
            user_id=self.user.id, notif_type='promo',
            title='Promo', body='Deal!',
        )
        count = self.user.cargo_unread_notifications_count
        self.assertGreaterEqual(count, 1)
