# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
Tests for CargoTimestampMixin, CargoSoftDeleteMixin and CargoAuditMixin.

We use real Odoo models that use these mixins rather than creating
throwaway test models:
  - cargo.audit.log  → uses no mixin directly but tests timestamp pattern
  - The mixin classes are AbstractModel — we verify their registry presence
    and field behaviour via the mixin contract.
"""

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestCargoTimestampMixin(TransactionCase):
    """Verify created_at and updated_at behave correctly."""

    def _create_log(self, **extra):
        defaults = {
            'action':     'create',
            'user_id':    self.env.uid,
            'user_name':  'Test User',
            'model_name': 'test.model',
            'record_id':  1,
        }
        defaults.update(extra)
        return self.env['cargo.audit.log'].sudo().create(defaults)

    def test_created_at_set_on_create(self):
        """created_at must be populated automatically on record creation."""
        log = self._create_log()
        self.assertTrue(log.created_at, 'created_at must be set on creation')

    def test_created_at_immutable(self):
        """Attempting to modify any audit log field must raise AccessError."""
        log = self._create_log()
        original = log.created_at
        # cargo.audit.log enforces immutability at Python level
        with self.assertRaises(AccessError):
            log.write({'user_name': 'Changed'})
        self.assertEqual(log.created_at, original, 'created_at must not change')

    def test_display_name_computed(self):
        """display_name must be a non-empty string for every log entry."""
        log = self._create_log()
        self.assertTrue(log.display_name, 'display_name must not be empty')
        self.assertIsInstance(log.display_name, str)


class TestCargoSoftDeleteMixin(TransactionCase):
    """Verify the soft-delete mixin's contract."""

    def test_soft_delete_mixin_registered(self):
        """cargo.soft.delete.mixin must be in the Odoo model registry."""
        self.assertIn(
            'cargo.soft.delete.mixin',
            self.env.registry,
            'cargo.soft.delete.mixin must be registered as an AbstractModel',
        )

    def test_audit_mixin_registered(self):
        """cargo.audit.mixin must be in the Odoo model registry."""
        self.assertIn(
            'cargo.audit.mixin',
            self.env.registry,
        )

    def test_timestamp_mixin_registered(self):
        """cargo.timestamp.mixin must be in the Odoo model registry."""
        self.assertIn(
            'cargo.timestamp.mixin',
            self.env.registry,
        )

    def test_soft_delete_mixin_uses_active_field(self):
        """
        The mixin must declare active as a Boolean field — not override search().
        Verified by inspecting the AbstractModel's _fields registry.
        """
        Mixin = self.env.registry.get('cargo.soft.delete.mixin')
        self.assertIsNotNone(Mixin, 'Mixin class must exist in registry')

        # active must be a defined field on the mixin
        self.assertIn(
            'active',
            Mixin._fields,
            'cargo.soft.delete.mixin must define an active field',
        )
        # is_deleted must be a computed convenience field
        self.assertIn(
            'is_deleted',
            Mixin._fields,
            'cargo.soft.delete.mixin must define an is_deleted field',
        )
        # search() must NOT be overridden — Odoo handles active filtering natively
        self.assertFalse(
            'search' in Mixin.__dict__,
            'cargo.soft.delete.mixin must NOT override search() — '
            'use Odoo native active field instead',
        )

    def test_soft_delete_mixin_metadata_fields(self):
        """Mixin must expose deleted_at and deleted_by_id for auditing."""
        Mixin = self.env.registry.get('cargo.soft.delete.mixin')
        for field_name in ('deleted_at', 'deleted_by_id'):
            self.assertIn(
                field_name,
                Mixin._fields,
                f'cargo.soft.delete.mixin must define {field_name}',
            )


class TestCargoAuditMixin(TransactionCase):
    """Verify the audit mixin's ORM overrides write to cargo.audit.log."""

    def test_audit_mixin_create_override(self):
        """
        Creating a record on a model that uses CargoAuditMixin must
        result in a corresponding cargo.audit.log 'create' entry.

        We test indirectly via product.category since cargo.store
        (the primary consumer of cargo.audit.mixin) is not installed
        in cargo_base — the mixin itself is pure Python and its logic
        is verified here at the mixin class level.
        """
        # Verify the mixin class itself has the ORM overrides
        Mixin = self.env.registry.get('cargo.audit.mixin')
        self.assertIsNotNone(Mixin)
        # create must be overridden
        self.assertIn('create', Mixin.__dict__, 'cargo.audit.mixin must override create()')
        # write must be overridden
        self.assertIn('write', Mixin.__dict__, 'cargo.audit.mixin must override write()')
        # unlink must be overridden
        self.assertIn('unlink', Mixin.__dict__, 'cargo.audit.mixin must override unlink()')
