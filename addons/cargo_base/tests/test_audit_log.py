# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
Tests for cargo.audit.log model.

Verifies immutability, factory method, and field constraints.
"""

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestCargoAuditLog(TransactionCase):

    def _make_log(self, **extra):
        defaults = {
            'action':     'create',
            'user_id':    self.env.uid,
            'user_name':  'Test User',
            'model_name': 'res.partner',
            'record_id':  1,
        }
        defaults.update(extra)
        return self.env['cargo.audit.log'].sudo().create(defaults)

    # ── Creation ──────────────────────────────────────────────────────────────

    def test_create_log_entry(self):
        log = self._make_log()
        self.assertTrue(log.id, 'Log entry must be created with an ID')

    def test_created_at_auto_set(self):
        log = self._make_log()
        self.assertTrue(log.created_at, 'created_at must be set automatically')

    def test_all_audit_actions_accepted(self):
        actions = ['create', 'read', 'update', 'delete', 'login', 'logout', 'register']
        for action in actions:
            log = self._make_log(action=action)
            self.assertEqual(log.action, action)

    # ── Immutability ──────────────────────────────────────────────────────────

    def test_write_raises_access_error(self):
        log = self._make_log()
        with self.assertRaises(AccessError):
            log.write({'user_name': 'Hacker'})

    def test_unlink_raises_access_error(self):
        log = self._make_log()
        with self.assertRaises(AccessError):
            log.unlink()

    # ── Factory method ────────────────────────────────────────────────────────

    def test_cargo_log_api_factory(self):
        log = self.env['cargo.audit.log'].cargo_log_api(
            action='login',
            endpoint='/api/v1/auth/login',
            method='POST',
            ip='127.0.0.1',
            user_agent='Flutter/3.0',
            response_code=200,
            duration_ms=45.3,
        )
        self.assertEqual(log.action, 'login')
        self.assertEqual(log.endpoint, '/api/v1/auth/login')
        self.assertEqual(log.http_method, 'POST')
        self.assertEqual(log.response_code, 200)
        self.assertAlmostEqual(log.duration_ms, 45.3, places=1)

    def test_factory_sets_user(self):
        log = self.env['cargo.audit.log'].cargo_log_api(action='read')
        self.assertEqual(log.user_id.id, self.env.uid)

    # ── Read access ───────────────────────────────────────────────────────────

    def test_can_search_logs(self):
        self._make_log(action='login')
        logs = self.env['cargo.audit.log'].sudo().search([('action', '=', 'login')])
        self.assertTrue(len(logs) >= 1)

    def test_ordering_newest_first(self):
        log1 = self._make_log()
        log2 = self._make_log()
        logs = self.env['cargo.audit.log'].sudo().search([], order='id desc', limit=2)
        self.assertGreater(logs[0].id, logs[1].id, 'Newest log must appear first')
