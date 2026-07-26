# -*- coding: utf-8 -*-
"""cargo_driver — driver profile tests."""
from odoo.tests.common import TransactionCase


class TestCargoDriver(TransactionCase):

    def _make_driver_user(self, suffix=''):
        return self.env['res.users'].sudo().create({
            'name':       f'Test Driver{suffix}',
            'login':      f'driver{suffix}@cargo.test',
            'email':      f'driver{suffix}@cargo.test',
            'password':   'Test1234!',
            'cargo_role': 'driver',
        })

    def test_create_driver_profile(self):
        user   = self._make_driver_user('1')
        driver = self.env['cargo.driver'].sudo().create({
            'user_id':      user.id,
            'vehicle_type': 'scooter',
            'vehicle_plate': 'ABC-123',
        })
        self.assertEqual(driver.vehicle_plate, 'ABC-123')
        self.assertFalse(driver.is_online)

    def test_set_online(self):
        user   = self._make_driver_user('2')
        driver = self.env['cargo.driver'].sudo().create({'user_id': user.id})
        driver.set_online(lat=30.05, lng=31.23)
        self.assertTrue(driver.is_online)
        self.assertAlmostEqual(driver.current_lat, 30.05)

    def test_driver_dict_shape(self):
        user   = self._make_driver_user('3')
        driver = self.env['cargo.driver'].sudo().create({'user_id': user.id})
        d = driver.to_driver_dict()
        for key in ('id', 'userId', 'name', 'isOnline', 'rating'):
            self.assertIn(key, d)
