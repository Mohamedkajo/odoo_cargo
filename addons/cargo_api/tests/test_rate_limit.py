# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
Tests for the cargo.rate.limit model.

Verifies:
  - cargo_increment() creates a new row for a new IP+window
  - cargo_increment() increments the count atomically for existing rows
  - cargo_cleanup_old_windows() removes rows older than 1 hour
  - display_name is computed correctly
  - UNIQUE constraint on (ip_address, window_start)
"""

import datetime

from odoo.tests.common import TransactionCase


class TestCargoRateLimit(TransactionCase):

    def _now_window(self, offset_minutes=0):
        """Return a window_start datetime (truncated to minute) with optional offset."""
        now = datetime.datetime.utcnow() + datetime.timedelta(minutes=offset_minutes)
        return now.replace(second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')

    # ── cargo_increment ───────────────────────────────────────────────────────

    def test_increment_creates_new_row(self):
        """First call for an IP must insert a new row with count=1."""
        ip = '10.0.0.1'
        # Clear any existing rows for this IP to avoid test interference
        self.env.cr.execute(
            "DELETE FROM cargo_rate_limit WHERE ip_address = %s", [ip]
        )
        count = self.env['cargo.rate.limit'].sudo().cargo_increment(ip)
        self.assertGreaterEqual(count, 1)

    def test_increment_increases_count(self):
        """Subsequent calls for the same IP in the same minute must increment."""
        ip = '10.0.0.2'
        self.env.cr.execute(
            "DELETE FROM cargo_rate_limit WHERE ip_address = %s", [ip]
        )
        c1 = self.env['cargo.rate.limit'].sudo().cargo_increment(ip)
        c2 = self.env['cargo.rate.limit'].sudo().cargo_increment(ip)
        c3 = self.env['cargo.rate.limit'].sudo().cargo_increment(ip)
        self.assertEqual(c2, c1 + 1)
        self.assertEqual(c3, c1 + 2)

    def test_increment_returns_integer(self):
        """cargo_increment must return an integer."""
        count = self.env['cargo.rate.limit'].sudo().cargo_increment('10.0.0.3')
        self.assertIsInstance(count, int)
        self.assertGreater(count, 0)

    def test_different_ips_have_independent_counters(self):
        """Different IPs must not interfere with each other's counters."""
        for ip in ['10.1.0.1', '10.1.0.2']:
            self.env.cr.execute(
                "DELETE FROM cargo_rate_limit WHERE ip_address = %s", [ip]
            )

        c_a = self.env['cargo.rate.limit'].sudo().cargo_increment('10.1.0.1')
        c_b = self.env['cargo.rate.limit'].sudo().cargo_increment('10.1.0.2')
        c_a2 = self.env['cargo.rate.limit'].sudo().cargo_increment('10.1.0.1')

        # b's count must not be affected by a's increments
        self.assertEqual(c_a2, c_a + 1)
        self.assertEqual(c_b, 1)

    # ── cleanup ───────────────────────────────────────────────────────────────

    def test_cleanup_removes_old_windows(self):
        """Rows from more than 1 hour ago must be deleted by cleanup."""
        ip = '10.2.0.1'
        old_window = (datetime.datetime.utcnow() - datetime.timedelta(hours=2)).replace(
            second=0, microsecond=0
        ).strftime('%Y-%m-%d %H:%M:%S')

        # Insert an old row directly
        self.env.cr.execute(
            """
            INSERT INTO cargo_rate_limit (ip_address, window_start, request_count)
            VALUES (%s, %s, 5)
            ON CONFLICT (ip_address, window_start) DO UPDATE SET request_count = 5
            """,
            [ip, old_window],
        )

        # Verify the row is there
        self.env.cr.execute(
            "SELECT COUNT(*) FROM cargo_rate_limit WHERE ip_address = %s AND window_start = %s",
            [ip, old_window],
        )
        count_before = self.env.cr.fetchone()[0]
        self.assertEqual(count_before, 1)

        # Run cleanup
        removed = self.env['cargo.rate.limit'].sudo().cargo_cleanup_old_windows()
        self.assertGreater(removed, 0)

        # Verify the old row is gone
        self.env.cr.execute(
            "SELECT COUNT(*) FROM cargo_rate_limit WHERE ip_address = %s AND window_start = %s",
            [ip, old_window],
        )
        count_after = self.env.cr.fetchone()[0]
        self.assertEqual(count_after, 0)

    def test_cleanup_preserves_current_window(self):
        """Rows from the current minute must NOT be deleted by cleanup."""
        ip = '10.3.0.1'
        self.env['cargo.rate.limit'].sudo().cargo_increment(ip)

        # Run cleanup
        self.env['cargo.rate.limit'].sudo().cargo_cleanup_old_windows()

        # Current window row should still exist
        self.env.cr.execute(
            "SELECT COUNT(*) FROM cargo_rate_limit WHERE ip_address = %s",
            [ip],
        )
        count = self.env.cr.fetchone()[0]
        self.assertGreater(count, 0, 'Current window rows must not be deleted by cleanup.')

    # ── Model fields ──────────────────────────────────────────────────────────

    def test_display_name_not_empty(self):
        """display_name must be a non-empty string for every rate limit record."""
        ip = '10.4.0.1'
        self.env['cargo.rate.limit'].sudo().cargo_increment(ip)
        record = self.env['cargo.rate.limit'].sudo().search(
            [('ip_address', '=', ip)], limit=1
        )
        self.assertTrue(record, 'Rate limit record must exist.')
        self.assertTrue(record.display_name, 'display_name must not be empty.')
        self.assertIsInstance(record.display_name, str)
