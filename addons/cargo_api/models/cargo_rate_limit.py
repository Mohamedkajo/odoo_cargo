# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo.rate.limit — Per-IP-per-minute request counter.

Rate limiting uses an atomic PostgreSQL UPSERT so it is safe under
concurrent Odoo workers with no application-level locking.

Table structure:
  - ip_address  : VARCHAR — the requesting IP (or 'user:<uid>' for auth'd users)
  - window_start: TIMESTAMP — truncated to the minute boundary
  - request_count: INTEGER — running total for this window

The UNIQUE constraint on (ip_address, window_start) is the foundation
for the ON CONFLICT … DO UPDATE upsert.

Cleanup of old rows is handled by an ir.cron job (hourly).
"""

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class CargoRateLimit(models.Model):
    """Per-IP request counter for the API rate limiter."""

    _name        = 'cargo.rate.limit'
    _description = 'Cargo API Rate Limit Counter'
    _order       = 'window_start desc'
    _log_access  = False   # no create_uid / write_uid columns

    # ── Fields ────────────────────────────────────────────────────────────────

    ip_address = fields.Char(
        string='IP / Identity',
        required=True,
        index=True,
        help='Requesting IP address, or "user:<uid>" for authenticated requests.',
    )
    window_start = fields.Datetime(
        string='Window Start',
        required=True,
        index=True,
        help='Minute boundary for this rate-limit window.',
    )
    request_count = fields.Integer(
        string='Request Count',
        default=1,
        required=True,
    )

    # ── SQL constraints ───────────────────────────────────────────────────────

    _sql_constraints = [
        ('ip_window_unique', 'UNIQUE(ip_address, window_start)',
         'Only one rate-limit row per IP per minute window.'),
    ]

    # ── Computed display_name ─────────────────────────────────────────────────

    display_name = fields.Char(
        string='Name',
        compute='_compute_display_name',
        store=False,
    )

    def _compute_display_name(self):
        for rec in self:
            window_str = rec.window_start.strftime('%Y-%m-%d %H:%M') if rec.window_start else '?'
            rec.display_name = f'{rec.ip_address} @ {window_str} ({rec.request_count} req)'

    # ── Core method ───────────────────────────────────────────────────────────

    @api.model
    def cargo_increment(self, ip_address):
        """
        Atomically increment (or initialise) the request counter for this IP
        in the current one-minute window.

        Uses an ON CONFLICT … DO UPDATE upsert so it is race-condition-free
        across multiple Odoo worker processes sharing the same PostgreSQL DB.

        Returns the updated request count after the increment.
        """
        now    = fields.Datetime.now()
        # Truncate to the start of the current minute
        window = now.replace(second=0, microsecond=0)

        self.env.cr.execute(
            """
            INSERT INTO cargo_rate_limit (ip_address, window_start, request_count)
            VALUES (%s, %s, 1)
            ON CONFLICT (ip_address, window_start)
            DO UPDATE
               SET request_count = cargo_rate_limit.request_count + 1
            RETURNING request_count
            """,
            [ip_address, window],
        )
        result = self.env.cr.fetchone()
        return result[0] if result else 1

    # ── Cleanup ───────────────────────────────────────────────────────────────

    @api.model
    def cargo_cleanup_old_windows(self):
        """
        Delete rate-limit rows older than 1 hour.
        Called by ir.cron every hour.
        """
        cutoff = fields.Datetime.subtract(fields.Datetime.now(), hours=1)
        self.env.cr.execute(
            "DELETE FROM cargo_rate_limit WHERE window_start < %s",
            [cutoff],
        )
        deleted = self.env.cr.rowcount
        _logger.debug('cargo.rate.limit cleanup: removed %d old window(s).', deleted)
        return deleted
