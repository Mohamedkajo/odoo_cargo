# -*- coding: utf-8 -*-
"""cargo_driver — driver profile tests.

Driver fields are on res.users (with cargo_role='driver'), not a custom cargo.driver model.
"""
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

    def test_driver_user_has_cargo_driver_fields(self):
        user = self._make_driver_user('A')
        user.sudo().write({
            'cargo_driver_vehicle_type':  'scooter',
            'cargo_driver_vehicle_plate': 'ABC-123',
        })
        self.assertEqual(user.cargo_driver_vehicle_plate, 'ABC-123')
        self.assertFalse(user.cargo_driver_is_online)

    def test_go_online(self):
        user = self._make_driver_user('B')
        user.cargo_driver_go_online(lat=30.05, lng=31.23)
        self.assertTrue(user.cargo_driver_is_online)
        self.assertAlmostEqual(user.cargo_driver_current_lat, 30.05)

    def test_go_offline(self):
        user = self._make_driver_user('C')
        user.cargo_driver_go_online()
        user.cargo_driver_go_offline()
        self.assertFalse(user.cargo_driver_is_online)

    def test_update_location(self):
        user = self._make_driver_user('D')
        user.cargo_driver_update_location(29.98, 31.13)
        self.assertAlmostEqual(user.cargo_driver_current_lat, 29.98)
        self.assertAlmostEqual(user.cargo_driver_current_lng, 31.13)

    def test_driver_to_api_dict_shape(self):
        user = self._make_driver_user('E')
        d = user.cargo_driver_to_api_dict()
        for key in ('id', 'name', 'vehicleType', 'isOnline', 'rating'):
            self.assertIn(key, d, f'Missing key: {key}')

    def test_default_values(self):
        user = self._make_driver_user('F')
        self.assertEqual(user.cargo_driver_total_deliveries, 0)
        self.assertEqual(user.cargo_driver_total_earnings,   0.0)
        self.assertEqual(user.cargo_driver_rating,           0.0)
