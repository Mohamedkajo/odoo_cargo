# -*- coding: utf-8 -*-
"""cargo_dashboard — smoke test: module loads and action exists."""
from odoo.tests.common import TransactionCase


class TestCargoDashboard(TransactionCase):

    def test_dashboard_action_exists(self):
        action = self.env.ref('cargo_dashboard.action_cargo_dashboard', raise_if_not_found=False)
        self.assertIsNotNone(action, 'Cargo Dashboard action should exist after module install.')
