# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo.audit.log — Platform audit trail.

Every API request and significant data mutation is recorded here.
Records are append-only — ``write()`` and ``unlink()`` both raise
``AccessError`` at the Python level so no ACL or record rule can bypass them.
"""

from odoo import api, fields, models
from odoo.exceptions import AccessError

from ..constants import AUDIT_ACTIONS


class CargoAuditLog(models.Model):
    """Immutable, append-only audit log for all Cargo platform operations."""

    _name        = 'cargo.audit.log'
    _description = 'Cargo Audit Log'
    _order       = 'id desc'

    # _log_access = False prevents Odoo from adding create_uid/write_uid/
    # create_date/write_date columns to this table — we manage our own
    # timestamps via ``created_at``.
    _log_access  = False

    # ── Who ───────────────────────────────────────────────────────────────────
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
        ondelete='set null',
        index=True,
        readonly=True,
    )
    user_name = fields.Char(
        string='User Name',
        readonly=True,
        help='Denormalised display name; preserved if the user is later deleted.',
    )

    # ── What ─────────────────────────────────────────────────────────────────
    action = fields.Selection(
        selection=AUDIT_ACTIONS,
        string='Action',
        required=True,
        readonly=True,
        index=True,
    )
    model_name = fields.Char(
        string='Model',
        readonly=True,
        index=True,
    )
    record_id = fields.Integer(
        string='Record ID',
        readonly=True,
        index=True,
    )
    changes = fields.Text(
        string='Changes (JSON)',
        readonly=True,
        help='JSON-encoded dict of changed field values (new values only).',
    )

    # ── HTTP context (for API requests) ───────────────────────────────────────
    endpoint = fields.Char(
        string='Endpoint',
        readonly=True,
    )
    http_method = fields.Char(
        string='HTTP Method',
        size=10,
        readonly=True,
    )
    ip_address = fields.Char(
        string='IP Address',
        readonly=True,
    )
    user_agent = fields.Char(
        string='User Agent',
        readonly=True,
    )
    response_code = fields.Integer(
        string='Response Code',
        readonly=True,
    )
    duration_ms = fields.Float(
        string='Duration (ms)',
        digits=(10, 2),
        readonly=True,
    )

    # ── When ─────────────────────────────────────────────────────────────────
    created_at = fields.Datetime(
        string='Timestamp',
        default=fields.Datetime.now,
        required=True,
        readonly=True,
        index=True,
    )

    # ── Display name ──────────────────────────────────────────────────────────
    display_name = fields.Char(
        string='Name',
        compute='_compute_display_name',
        help='Human-readable summary used in breadcrumbs and dropdowns.',
    )

    # ── Computes ──────────────────────────────────────────────────────────────

    @api.depends('action', 'model_name', 'created_at')
    def _compute_display_name(self):
        for log in self:
            ts  = log.created_at.strftime('%Y-%m-%d %H:%M:%S') if log.created_at else '?'
            act = dict(AUDIT_ACTIONS).get(log.action, log.action or '?')
            mdl = log.model_name or '?'
            log.display_name = f'[{ts}] {act} on {mdl}'

    # ── ORM guard — records are append-only ───────────────────────────────────

    def write(self, vals):
        raise AccessError('Audit log records are immutable and cannot be modified.')

    def unlink(self):
        raise AccessError('Audit log records cannot be deleted.')

    # ── Factory ───────────────────────────────────────────────────────────────

    @api.model
    def cargo_log_api(
        self,
        action: str,
        endpoint: str = '',
        method: str = '',
        ip: str = '',
        user_agent: str = '',
        response_code: int = 200,
        duration_ms: float = 0.0,
        model_name: str = '',
        record_id: int = 0,
        changes: str = '',
    ) -> 'CargoAuditLog':
        """
        Convenience factory for writing a single audit log entry.

        Always executes with sudo so the log is written regardless of the
        calling user's group membership.  Callers should never need to call
        ``create()`` directly.
        """
        user = self.env.user
        return self.sudo().create({
            'user_id':       user.id,
            'user_name':     user.name or '',
            'action':        action,
            'model_name':    model_name,
            'record_id':     record_id,
            'changes':       changes,
            'endpoint':      endpoint,
            'http_method':   method,
            'ip_address':    ip,
            'user_agent':    user_agent,
            'response_code': response_code,
            'duration_ms':   duration_ms,
            'created_at':    fields.Datetime.now(),
        })
