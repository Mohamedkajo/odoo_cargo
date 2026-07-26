# -*- coding: utf-8 -*-
"""cargo_marketplace — settings singleton and public API tests."""
import json
from odoo.tests.common import HttpCase, TransactionCase


class TestCargoMarketplaceSettings(TransactionCase):

    def test_get_settings_creates_singleton(self):
        settings = self.env['cargo.marketplace.settings'].sudo().get_settings()
        self.assertIsNotNone(settings)
        settings2 = self.env['cargo.marketplace.settings'].sudo().get_settings()
        self.assertEqual(settings.id, settings2.id, 'get_settings() must return the same record.')

    def test_public_dict_shape(self):
        settings = self.env['cargo.marketplace.settings'].sudo().get_settings()
        d = settings.to_public_dict()
        for key in ('platformName', 'maintenanceMode', 'walletEnabled', 'defaultDeliveryFee'):
            self.assertIn(key, d)

    def test_public_dict_excludes_sensitive_fields(self):
        settings = self.env['cargo.marketplace.settings'].sudo().get_settings()
        d = settings.to_public_dict()
        self.assertNotIn('default_commission_rate', d)


class TestCargoMarketplaceApi(HttpCase):

    def test_settings_endpoint_is_public(self):
        resp = self.url_open('/api/settings')
        self.assertEqual(resp.status, 200)
        data = json.loads(resp.read())
        self.assertIn('platformName', data)
