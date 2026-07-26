# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
Installation, upgrade and uninstall validation tests for cargo_base.

These tests verify that:
  - post_init_hook seeded all required config parameters correctly
  - JWT secret was generated (not empty, not the placeholder)
  - All 8 security groups exist in the registry
  - All expected models are registered
  - ACLs exist for cargo.audit.log
  - Record rules are present
  - Upgrade is idempotent (running hooks twice does not corrupt state)
  - Simulated uninstall removes all cargo.* config params
"""

from odoo.tests.common import TransactionCase


_EXPECTED_CONFIG_KEYS = [
    'cargo.jwt.secret',
    'cargo.jwt.access_expiry_seconds',
    'cargo.jwt.refresh_expiry_seconds',
    'cargo.otp.expiry_minutes',
    'cargo.commission.default_rate',
    'cargo.default_currency',
    'cargo.default_country_code',
    'cargo.support.email',
    'cargo.support.phone',
    'cargo.rate_limit.requests_per_minute',
    'cargo.media.max_image_size_mb',
]

_EXPECTED_GROUPS = [
    'cargo_base.cargo_group_customer',
    'cargo_base.cargo_group_driver',
    'cargo_base.cargo_group_vendor',
    'cargo_base.cargo_group_vendor_manager',
    'cargo_base.cargo_group_operations',
    'cargo_base.cargo_group_finance',
    'cargo_base.cargo_group_admin',
    'cargo_base.cargo_group_super_admin',
]

_EXPECTED_MODELS = [
    'res.partner',
    'res.users',
    'product.template',
    'product.category',
    'sale.order',
    'cargo.audit.log',
    'cargo.soft.delete.mixin',
    'cargo.timestamp.mixin',
    'cargo.audit.mixin',
]


class TestCargoBaseInstallation(TransactionCase):
    """Verify that post_init_hook seeded the environment correctly."""

    def _get_param(self, key):
        return self.env['ir.config_parameter'].sudo().get_param(key)

    # ── Config parameters ─────────────────────────────────────────────────────

    def test_all_config_params_present(self):
        """Every expected cargo.* config parameter must exist after installation."""
        ICP = self.env['ir.config_parameter'].sudo()
        missing = []
        for key in _EXPECTED_CONFIG_KEYS:
            val = ICP.get_param(key)
            if not val:
                missing.append(key)
        self.assertFalse(
            missing,
            f'{len(missing)} config param(s) missing after install: {missing}',
        )

    def test_jwt_secret_generated_and_long_enough(self):
        """
        JWT secret must be a hex string of at least 64 characters (256-bit minimum).
        It must not be the string 'None', empty, or a placeholder.
        """
        secret = self._get_param('cargo.jwt.secret')
        self.assertTrue(secret, 'JWT secret must not be empty.')
        self.assertNotEqual(secret, 'None', 'JWT secret must not be the string "None".')
        self.assertNotIn('placeholder', secret.lower(), 'JWT secret must not be a placeholder.')
        self.assertGreaterEqual(
            len(secret), 64,
            f'JWT secret is too short ({len(secret)} chars); minimum is 64 hex chars (256 bits).',
        )
        # Must be a valid hex string
        try:
            int(secret, 16)
        except ValueError:
            self.fail('JWT secret must be a valid hex string.')

    def test_access_expiry_is_positive_integer(self):
        """Access token expiry must be a positive integer (seconds)."""
        val = self._get_param('cargo.jwt.access_expiry_seconds')
        self.assertTrue(val, 'Access expiry param must be set.')
        try:
            expiry = int(val)
        except ValueError:
            self.fail('Access expiry must be an integer.')
        self.assertGreater(expiry, 0, 'Access expiry must be positive.')

    def test_refresh_expiry_greater_than_access_expiry(self):
        """Refresh token expiry must be longer than access token expiry."""
        access  = int(self._get_param('cargo.jwt.access_expiry_seconds')  or 0)
        refresh = int(self._get_param('cargo.jwt.refresh_expiry_seconds') or 0)
        self.assertGreater(
            refresh, access,
            'Refresh token expiry must be greater than access token expiry.',
        )

    def test_commission_rate_is_valid_percentage(self):
        """Default commission rate must be between 0 and 100."""
        val = float(self._get_param('cargo.commission.default_rate') or '-1')
        self.assertGreaterEqual(val, 0.0)
        self.assertLessEqual(val, 100.0)

    def test_rate_limit_is_positive_integer(self):
        """Rate limit must be a positive integer."""
        val = self._get_param('cargo.rate_limit.requests_per_minute')
        self.assertTrue(val)
        rpm = int(val)
        self.assertGreater(rpm, 0)

    def test_max_image_size_is_positive(self):
        """Max image size must be positive."""
        val = self._get_param('cargo.media.max_image_size_mb')
        self.assertTrue(val)
        size = float(val)
        self.assertGreater(size, 0)

    # ── Security groups ───────────────────────────────────────────────────────

    def test_all_cargo_groups_exist(self):
        """All 8 Cargo security groups must be created after installation."""
        missing = []
        for ext_id in _EXPECTED_GROUPS:
            try:
                group = self.env.ref(ext_id)
                if not group:
                    missing.append(ext_id)
            except Exception:
                missing.append(ext_id)
        self.assertFalse(missing, f'Missing security groups: {missing}')

    def test_group_hierarchy_super_admin_implies_admin(self):
        """cargo_group_super_admin must imply cargo_group_admin."""
        super_admin = self.env.ref('cargo_base.cargo_group_super_admin')
        admin       = self.env.ref('cargo_base.cargo_group_admin')
        implied_ids = super_admin.implied_ids
        self.assertIn(
            admin, implied_ids,
            'cargo_group_super_admin must imply cargo_group_admin.',
        )

    def test_group_hierarchy_admin_implies_operations(self):
        """cargo_group_admin must imply cargo_group_operations."""
        admin      = self.env.ref('cargo_base.cargo_group_admin')
        operations = self.env.ref('cargo_base.cargo_group_operations')
        self.assertIn(
            operations, admin.implied_ids,
            'cargo_group_admin must imply cargo_group_operations.',
        )

    def test_group_hierarchy_admin_implies_finance(self):
        """cargo_group_admin must imply cargo_group_finance."""
        admin   = self.env.ref('cargo_base.cargo_group_admin')
        finance = self.env.ref('cargo_base.cargo_group_finance')
        self.assertIn(
            finance, admin.implied_ids,
            'cargo_group_admin must imply cargo_group_finance.',
        )

    def test_group_hierarchy_vendor_manager_implies_vendor(self):
        """cargo_group_vendor_manager must imply cargo_group_vendor."""
        vendor_manager = self.env.ref('cargo_base.cargo_group_vendor_manager')
        vendor         = self.env.ref('cargo_base.cargo_group_vendor')
        self.assertIn(
            vendor, vendor_manager.implied_ids,
            'cargo_group_vendor_manager must imply cargo_group_vendor.',
        )

    # ── Model registry ────────────────────────────────────────────────────────

    def test_all_expected_models_registered(self):
        """All Cargo models and mixins must be present in the Odoo registry."""
        missing = [m for m in _EXPECTED_MODELS if m not in self.env.registry]
        self.assertFalse(missing, f'Models missing from registry: {missing}')

    def test_audit_log_model_is_immutable(self):
        """cargo.audit.log must reject write() at the model level."""
        from odoo.exceptions import AccessError
        log = self.env['cargo.audit.log'].sudo().create({
            'action':     'create',
            'user_id':    self.env.uid,
            'user_name':  'Test',
            'model_name': 'test.model',
            'record_id':  1,
        })
        with self.assertRaises(AccessError):
            log.write({'user_name': 'Tampered'})

    # ── ACLs ─────────────────────────────────────────────────────────────────

    def test_audit_log_acl_exists(self):
        """
        At least one ir.model.access record must exist for cargo.audit.log.
        """
        model = self.env['ir.model'].sudo().search(
            [('model', '=', 'cargo.audit.log')], limit=1,
        )
        self.assertTrue(model, 'cargo.audit.log model must exist in ir.model.')
        acls = self.env['ir.model.access'].sudo().search(
            [('model_id', '=', model.id)],
        )
        self.assertTrue(acls, 'At least one ACL must exist for cargo.audit.log.')

    def test_audit_log_acl_no_write_or_unlink(self):
        """
        No ACL row for cargo.audit.log should grant perm_write or perm_unlink.
        The model enforces immutability at Python level, but belt-and-suspenders.
        """
        model = self.env['ir.model'].sudo().search(
            [('model', '=', 'cargo.audit.log')], limit=1,
        )
        bad_acls = self.env['ir.model.access'].sudo().search([
            ('model_id', '=', model.id),
            '|',
            ('perm_write', '=', True),
            ('perm_unlink', '=', True),
        ])
        self.assertFalse(
            bad_acls,
            f'ACL(s) for cargo.audit.log must not grant write/unlink: '
            f'{bad_acls.mapped("name")}',
        )

    # ── Record rules ─────────────────────────────────────────────────────────

    def test_partner_record_rules_exist(self):
        """
        Record rules that restrict partner access by role must exist.
        """
        rules = self.env['ir.rule'].sudo().search([
            ('name', 'ilike', 'cargo'),
            ('model_id.model', '=', 'res.partner'),
        ])
        self.assertTrue(
            len(rules) >= 3,
            f'At least 3 cargo partner record rules expected, found {len(rules)}.',
        )


class TestCargoBaseUpgrade(TransactionCase):
    """Verify that re-running the post_init_hook (upgrade scenario) is idempotent."""

    def test_post_init_hook_idempotent(self):
        """
        Calling post_init_hook a second time must not overwrite the JWT secret
        or corrupt any existing config parameter.
        """
        ICP = self.env['ir.config_parameter'].sudo()
        original_secret = ICP.get_param('cargo.jwt.secret')
        self.assertTrue(original_secret, 'JWT secret must exist before idempotency test.')

        # Re-run the hook
        from cargo_base.hooks import post_init_hook
        post_init_hook(self.env)

        # Secret must be unchanged (hook must not overwrite existing)
        new_secret = ICP.get_param('cargo.jwt.secret')
        self.assertEqual(
            original_secret, new_secret,
            'post_init_hook must not overwrite an existing JWT secret on upgrade.',
        )

    def test_upgrade_preserves_all_params(self):
        """All config params must still exist after a simulated re-install."""
        from cargo_base.hooks import post_init_hook
        ICP = self.env['ir.config_parameter'].sudo()

        # Record original values
        before = {key: ICP.get_param(key) for key in [
            'cargo.jwt.access_expiry_seconds',
            'cargo.commission.default_rate',
            'cargo.rate_limit.requests_per_minute',
        ]}

        post_init_hook(self.env)

        after = {key: ICP.get_param(key) for key in before}
        for key in before:
            self.assertEqual(
                before[key], after[key],
                f'Upgrade must not change existing param {key}.',
            )


class TestCargoBaseUninstall(TransactionCase):
    """Verify the uninstall_hook cleans up all cargo.* config parameters."""

    def test_uninstall_hook_removes_all_cargo_params(self):
        """
        uninstall_hook must remove ALL cargo.* ir.config_parameter entries.
        After running it, none of the expected keys should exist.
        """
        from cargo_base.hooks import uninstall_hook
        uninstall_hook(self.env)

        ICP = self.env['ir.config_parameter'].sudo()
        remaining = ICP.search([('key', 'like', 'cargo.%')])
        self.assertFalse(
            remaining,
            f'uninstall_hook must remove all cargo.* params; '
            f'found {len(remaining)}: {remaining.mapped("key")}',
        )

    def test_uninstall_does_not_remove_non_cargo_params(self):
        """
        uninstall_hook must not touch ir.config_parameter entries
        that do not start with 'cargo.'.
        """
        ICP = self.env['ir.config_parameter'].sudo()
        # Ensure a native param exists
        web_base = ICP.get_param('web.base.url')
        self.assertTrue(web_base, 'web.base.url must exist as a reference non-cargo param.')

        from cargo_base.hooks import uninstall_hook
        uninstall_hook(self.env)

        after = ICP.get_param('web.base.url')
        self.assertEqual(
            web_base, after,
            'uninstall_hook must not remove non-cargo params like web.base.url.',
        )
