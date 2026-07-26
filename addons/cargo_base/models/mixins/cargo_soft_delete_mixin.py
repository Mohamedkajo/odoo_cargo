# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
CargoSoftDeleteMixin
====================
Abstract mixin that implements Odoo's native soft-delete pattern using the
``active`` boolean field.

When ``active`` is False the record is treated as deleted.  Odoo
automatically excludes inactive records from every search unless the caller
sets ``context={'active_test': False}``.  This is the standard, ORM-supported
pattern — no ``search()`` override is needed or appropriate.

Additional metadata fields (``deleted_at``, ``deleted_by_id``) are stored
alongside ``active`` for auditing and recovery purposes.

Usage::

    class CargoStore(models.Model):
        _name    = 'cargo.store'
        _inherit = ['cargo.soft.delete.mixin', 'cargo.timestamp.mixin']
        _description = 'Cargo Store'

To include deleted records in a search::

    stores = self.env['cargo.store'].with_context(active_test=False).search([...])

To restore a soft-deleted record::

    store.restore()

To permanently destroy a record (superusers only)::

    store.hard_unlink()
"""

from odoo import api, fields, models
from odoo.exceptions import AccessError


class CargoSoftDeleteMixin(models.AbstractModel):
    """Abstract mixin — Odoo-idiomatic soft delete via the ``active`` field."""

    _name        = 'cargo.soft.delete.mixin'
    _description = 'Cargo Soft Delete Mixin'

    # ── Core soft-delete field ────────────────────────────────────────────────
    # Odoo automatically excludes records with active=False from all searches.
    # No search() override is needed — this is the ORM's built-in mechanism.
    active = fields.Boolean(
        string='Active',
        default=True,
        index=True,
        help='Uncheck to soft-delete this record. '
             'Inactive records are hidden from all standard searches.',
    )

    # ── Audit metadata ────────────────────────────────────────────────────────
    deleted_at = fields.Datetime(
        string='Deleted At',
        readonly=True,
        copy=False,
        help='Timestamp when this record was soft-deleted.',
    )
    deleted_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Deleted By',
        readonly=True,
        copy=False,
        ondelete='set null',
        help='User who performed the soft delete.',
    )

    # ── Convenience computed flag ─────────────────────────────────────────────
    is_deleted = fields.Boolean(
        string='Is Deleted',
        compute='_compute_is_deleted',
        store=True,
        index=True,
        help='True when this record has been soft-deleted (active=False).',
    )

    # ── Computes ──────────────────────────────────────────────────────────────

    @api.depends('active')
    def _compute_is_deleted(self):
        for record in self:
            record.is_deleted = not record.active

    # ── ORM overrides ─────────────────────────────────────────────────────────

    def unlink(self):
        """
        Soft-delete: set active=False instead of removing the database row.
        Records are recoverable via restore().
        """
        now = fields.Datetime.now()
        # Write directly to avoid triggering the mixin's own unlink recursion
        return self.write({
            'active':        False,
            'deleted_at':    now,
            'deleted_by_id': self.env.uid,
        })

    def hard_unlink(self):
        """
        Permanently remove records from the database.

        Restricted to superuser sessions only (``self.env.su``).
        Use with extreme caution — this action cannot be undone.
        """
        if not self.env.su:
            raise AccessError(
                'Only a superuser session can permanently delete records. '
                'Use unlink() to soft-delete instead.'
            )
        return super().unlink()

    def restore(self):
        """
        Restore a soft-deleted record.
        Clears the active=False flag and wipes the deletion metadata.
        """
        self.ensure_one()
        return self.write({
            'active':        True,
            'deleted_at':    False,
            'deleted_by_id': False,
        })
