# -*- coding: utf-8 -*-
"""cargo_notification — notification send, FCM dispatch, and read tests."""
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase


class TestCargoNotification(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env['res.users'].sudo().create({
            'name': 'Notif User',
            'login': 'notifuser@cargo.test',
            'email': 'notifuser@cargo.test',
            'password': 'Test1234!',
            'cargo_role': 'customer',
        })

    def test_send_to_user_creates_record(self):
        """send_to_user should create a cargo.notification record."""
        n = self.env['cargo.notification'].sudo().send_to_user(
            user=self.user,
            title='Order Confirmed',
            body='Your order #001 is confirmed.',
            notif_type='order_update',
        )
        self.assertFalse(n.is_read)
        self.assertTrue(n.is_sent)
        self.assertEqual(n.title, 'Order Confirmed')
        self.assertEqual(n.user_id, self.user)

    def test_send_to_user_no_token_no_fcm_call(self):
        """send_to_user without a device token must not attempt FCM dispatch."""
        # Ensure user has no token
        self.user.sudo().cargo_device_token = False
        with patch.object(
            type(self.env['cargo.notification']), '_dispatch_fcm'
        ) as mock_fcm:
            self.env['cargo.notification'].sudo().send_to_user(
                user=self.user,
                title='No Token Test',
                body='Should not call FCM.',
            )
            mock_fcm.assert_not_called()

    def test_send_to_user_with_token_calls_fcm(self):
        """send_to_user with a device token must call _dispatch_fcm."""
        self.user.sudo().cargo_device_token = 'fake_device_token_123'
        with patch.object(
            type(self.env['cargo.notification']), '_dispatch_fcm', return_value=True
        ) as mock_fcm:
            self.env['cargo.notification'].sudo().send_to_user(
                user=self.user,
                title='FCM Test',
                body='Should call FCM.',
            )
            mock_fcm.assert_called_once()
            args = mock_fcm.call_args
            self.assertEqual(args.kwargs.get('device_token') or args[1].get('device_token') or args[0][1],
                             'fake_device_token_123')

    def test_dispatch_fcm_no_server_key_returns_false(self):
        """_dispatch_fcm must return False and not call urlopen when no key is set."""
        # Ensure no FCM key is configured
        self.env['ir.config_parameter'].sudo().set_param('cargo.fcm.server_key', '')
        notif = self.env['cargo.notification'].sudo().create({
            'title': 'Test', 'body': 'Test body',
        })
        with patch('urllib.request.urlopen') as mock_urlopen:
            result = notif._dispatch_fcm(
                device_token='sometoken',
                title='Test',
                body='Test body',
            )
            self.assertFalse(result)
            mock_urlopen.assert_not_called()

    def test_dispatch_fcm_with_key_posts_to_fcm(self):
        """_dispatch_fcm must POST to FCM endpoint when server key is set."""
        self.env['ir.config_parameter'].sudo().set_param(
            'cargo.fcm.server_key', 'AAAA_fake_server_key'
        )
        notif = self.env['cargo.notification'].sudo().create({
            'title': 'Test', 'body': 'Test body',
        })
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.read.return_value = b'{"multicast_id": 1, "success": 1, "failure": 0, "results": [{"message_id": "msg_1"}]}'
        with patch('urllib.request.urlopen', return_value=mock_resp):
            with patch('urllib.request.Request') as MockRequest:
                result = notif._dispatch_fcm(
                    device_token='device_token_abc',
                    title='Push Title',
                    body='Push body',
                    data={'orderId': 42},
                )
                self.assertTrue(result)
                # Verify the FCM endpoint was targeted
                call_args = MockRequest.call_args
                self.assertIn('fcm.googleapis.com', call_args[0][0])

    def test_dispatch_fcm_network_error_returns_false(self):
        """_dispatch_fcm must return False (not raise) on network error."""
        import urllib.error
        self.env['ir.config_parameter'].sudo().set_param(
            'cargo.fcm.server_key', 'AAAA_fake_server_key'
        )
        notif = self.env['cargo.notification'].sudo().create({
            'title': 'Test', 'body': 'Test body',
        })
        with patch('urllib.request.urlopen', side_effect=urllib.error.URLError('timeout')):
            result = notif._dispatch_fcm(
                device_token='device_token_abc',
                title='Test',
                body='Test body',
            )
            self.assertFalse(result)

    def test_unread_count_computed(self):
        """Unread notification count on user should include newly sent notifications."""
        before = self.user.cargo_unread_count
        self.env['cargo.notification'].sudo().send_to_user(
            user=self.user,
            title='Promo',
            body='Deal!',
            notif_type='promo',
        )
        self.user.invalidate_recordset()
        self.assertGreaterEqual(self.user.cargo_unread_count, before + 1)

    def test_broadcast_notification(self):
        """broadcast_notification should create one record per matching user."""
        Notif = self.env['cargo.notification'].sudo()
        before = Notif.search_count([('broadcast', '=', True), ('type', '=', 'promo')])
        Notif.broadcast_notification(
            title='Flash Sale',
            body='50% off everything!',
            notif_type='promo',
            role='customer',
        )
        after = Notif.search_count([('broadcast', '=', True), ('type', '=', 'promo')])
        # At least our test customer user should have received one
        self.assertGreater(after, before)


class TestSaleOrderStatusNotification(TransactionCase):
    """Test that sale.order write triggers customer push notifications."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Partner + linked user to act as the customer
        cls.customer_user = cls.env['res.users'].sudo().create({
            'name': 'Customer Push Test',
            'login': 'custpush@cargo.test',
            'email': 'custpush@cargo.test',
            'password': 'Test1234!',
            'cargo_role': 'customer',
        })
        cls.partner = cls.customer_user.partner_id

        # Minimal sale.order
        cls.order = cls.env['sale.order'].sudo().create({
            'partner_id': cls.partner.id,
            'cargo_status': 'confirmed',
        })

    def test_status_change_creates_notification(self):
        """Writing cargo_status on an order should create a cargo.notification."""
        Notif = self.env['cargo.notification'].sudo()
        before = Notif.search_count([
            ('order_id', '=', self.order.id),
            ('type', '=', 'order_update'),
        ])
        self.order.sudo().write({'cargo_status': 'preparing'})
        after = Notif.search_count([
            ('order_id', '=', self.order.id),
            ('type', '=', 'order_update'),
        ])
        self.assertGreater(after, before)

    def test_status_change_no_duplicate_on_no_change(self):
        """Writing the same cargo_status value should not create extra notifications."""
        Notif = self.env['cargo.notification'].sudo()
        self.order.sudo().write({'cargo_status': 'preparing'})
        before = Notif.search_count([('order_id', '=', self.order.id)])
        # Write same status again
        self.order.sudo().write({'cargo_status': 'preparing'})
        after = Notif.search_count([('order_id', '=', self.order.id)])
        self.assertEqual(before, after)
