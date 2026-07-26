# -*- coding: utf-8 -*-
"""cargo_reports — admin summary endpoint tests."""
import json
from odoo.tests.common import HttpCase


class TestCargoReports(HttpCase):

    def test_summary_requires_auth(self):
        resp = self.url_open('/api/admin/reports/summary')
        data = json.loads(resp.read())
        self.assertIn('error', data)

    def test_orders_by_date_requires_auth(self):
        resp = self.url_open('/api/admin/reports/orders')
        data = json.loads(resp.read())
        self.assertIn('error', data)
