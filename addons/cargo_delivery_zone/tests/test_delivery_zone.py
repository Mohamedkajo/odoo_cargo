# -*- coding: utf-8 -*-
"""cargo_delivery_zone — zone model tests."""
from odoo.tests.common import TransactionCase


class TestCargoDeliveryZone(TransactionCase):

    def test_create_zone(self):
        zone = self.env['cargo.delivery.zone'].sudo().create({
            'name': 'Test Zone', 'city': 'Cairo',
            'center_lat': 30.05, 'center_lng': 31.23,
            'max_radius_km': 5.0, 'base_delivery_fee': 15.0,
        })
        self.assertTrue(zone.is_active)

    def test_covers_coordinates_within_radius(self):
        zone = self.env['cargo.delivery.zone'].sudo().create({
            'name': 'Radius Zone', 'city': 'Cairo',
            'center_lat': 30.0, 'center_lng': 31.0, 'max_radius_km': 20.0,
        })
        self.assertTrue(zone.covers_coordinates(30.01, 31.01))

    def test_covers_coordinates_outside_radius(self):
        zone = self.env['cargo.delivery.zone'].sudo().create({
            'name': 'Small Zone', 'city': 'Cairo',
            'center_lat': 30.0, 'center_lng': 31.0, 'max_radius_km': 1.0,
        })
        self.assertFalse(zone.covers_coordinates(31.0, 32.0))

    def test_zone_dict_shape(self):
        zone = self.env['cargo.delivery.zone'].sudo().create({
            'name': 'Dict Zone', 'city': 'Cairo',
        })
        d = zone.to_zone_dict()
        for key in ('id', 'name', 'city', 'baseDeliveryFee', 'isActive'):
            self.assertIn(key, d)
