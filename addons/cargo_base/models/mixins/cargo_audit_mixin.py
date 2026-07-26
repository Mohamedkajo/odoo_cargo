# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
CargoAuditMixin
===============
Abstract mixin that automatically creates cargo.audit.log entries
whenever a record is created, written or deleted.

Usage::

    class CargoWallet(models.Model):
        _name    = 'cargo.wallet'
        _inherit = ['cargo.audit.mixin', 'cargo.timestamp.mixin']

Set `_cargo_audit_fields` on the model to restrict which fields are logged::

    _cargo_audit_fields = {'balance', 'state'}   # only log changes to these

Leave empty to log all field changes (default behaviour).
"""

import json
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class CargoAuditMixin(models.AbstractModel):
    """Abstract mixin — writes cargo.audit.log entries on create/write/unlink."""

    _name        = 'cargo.audit.mixin'
    _description = 'Cargo Audit Mixin'

    # Subclasses may restrict which fields are tracked
    _cargo_audit_fields: set = set()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _cargo_audit_model_name(self) -> str:
        return self._name

    def _cargo_get_changed_fields(self, vals: dict) -> dict:
        """Return a dict of {field: new_value} restricted to tracked fields."""
        if self._cargo_audit_fields:
            return {k: v for k, v in vals.items() if k in self._cargo_audit_fields}
        return vals

    def _cargo_write_audit(self, action: str, record_id: int, changes: dict = None):
        """Write one audit log entry using sudo to avoid permission issues."""
        try:
            self.env['cargo.audit.log'].sudo().create({
                'user_id':    self.env.uid,
                'action':     action,
                'model_name': self._cargo_audit_model_name(),
                'record_id':  record_id,
                'changes':    json.dumps(changes or {}, default=str),
            })
        except Exception:
            # Audit logging must never crash the main operation
            _logger.exception(
                '[cargo_audit_mixin] Failed to write audit log for %s id=%s action=%s',
                self._name, record_id, action,
            )

    # ── ORM overrides ─────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            self._cargo_write_audit('create', record.id)
        return records

    def write(self, vals):
        tracked = self._cargo_get_changed_fields(vals)
        result  = super().write(vals)
        if tracked:
            for record in self:
                self._cargo_write_audit('update', record.id, tracked)
        return result

    def unlink(self):
        for record in self:
            self._cargo_write_audit('delete', record.id)
        return super().unlink()
