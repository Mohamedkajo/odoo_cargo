# -*- coding: utf-8 -*-
"""cargo_delivery — delivery lifecycle tests.

order_id  FK → sale.order (cargo_status field present)
driver_id FK → res.users  (cargo_role='driver')
"""
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestCargoDelivery(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.store_cat = cls.env['cargo.store.category'].sudo().create({'name': 'DelivCat'})
        cls.store = cls.env['cargo.store'].sudo().create({
            'name': 'Delivery Test Store', 'category_id': cls.store_cat.id,
        })
        cls.customer = cls.env['res.users'].sudo().create({
            'name': 'Delivery Customer', 'login': 'deliv_cust@cargo.test',
            'email': 'deliv_cust@cargo.test', 'password': 'Test1234!', 'cargo_role': 'customer',
        })
        cls.driver = cls.env['res.users'].sudo().create({
            'name': 'Test Driver', 'login': 'deliv_driver@cargo.test',
            'email': 'deliv_driver@cargo.test', 'password': 'Test1234!', 'cargo_role': 'driver',
        })
        cls.order = cls.env['sale.order'].sudo().create({
            'partner_id':    cls.customer.partner_id.id,
            'cargo_status':  'confirmed',
            'cargo_store_id': cls.store.id,
        })

    def _make_delivery(self):
        return self.env['cargo.delivery'].sudo().create({
            'order_id':  self.order.id,
            'driver_id': self.driver.id,
        })

    def test_create_delivery_generates_otps(self):
        d = self._make_delivery()
        self.assertTrue(d.pickup_otp)
        self.assertTrue(d.delivery_otp)
        self.assertEqual(d.status, 'assigned')

    def test_transition_to_picked_up(self):
        d = self._make_delivery()
        d.transition('picked_up')
        self.assertEqual(d.status, 'picked_up')
        self.assertIsNotNone(d.picked_up_at)

    def test_invalid_transition_raises(self):
        d = self._make_delivery()
        with self.assertRaises(UserError):
            d.transition('delivered')  # Must go assigned → picked_up → on_the_way → delivered

    def test_delivery_dict_shape(self):
        d = self._make_delivery()
        dd = d.to_delivery_dict()
        for key in ('id', 'orderId', 'status', 'driverId'):
            self.assertIn(key, dd, f'Missing key: {key}')
