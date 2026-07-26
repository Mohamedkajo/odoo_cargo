# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
Cargo test base class.

All cargo_base test cases inherit from CargoBaseTestCase which provides:
- Pre-created users for each Cargo role
- Helper to retrieve any ir.config_parameter value
- Clean Odoo test environment
"""

from odoo.tests.common import TransactionCase


class CargoBaseTestCase(TransactionCase):
    """Base test case for all cargo_base tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # ── Groups ────────────────────────────────────────────────────────────
        cls.group_customer     = cls.env.ref('cargo_base.cargo_group_customer')
        cls.group_vendor       = cls.env.ref('cargo_base.cargo_group_vendor')
        cls.group_driver       = cls.env.ref('cargo_base.cargo_group_driver')
        cls.group_operations   = cls.env.ref('cargo_base.cargo_group_operations')
        cls.group_finance      = cls.env.ref('cargo_base.cargo_group_finance')
        cls.group_admin        = cls.env.ref('cargo_base.cargo_group_admin')
        cls.group_super_admin  = cls.env.ref('cargo_base.cargo_group_super_admin')

        # ── Users ─────────────────────────────────────────────────────────────
        cls.user_customer = cls.env['res.users'].create({
            'name':     'Test Customer',
            'login':    'test.customer@cargo.test',
            'email':    'test.customer@cargo.test',
            'groups_id': [(6, 0, [cls.group_customer.id])],
            'partner_id': cls.env['res.partner'].create({
                'name':       'Test Customer',
                'cargo_role': 'customer',
            }).id,
        })

        cls.user_vendor = cls.env['res.users'].create({
            'name':     'Test Vendor',
            'login':    'test.vendor@cargo.test',
            'email':    'test.vendor@cargo.test',
            'groups_id': [(6, 0, [cls.group_vendor.id])],
            'partner_id': cls.env['res.partner'].create({
                'name':       'Test Vendor',
                'cargo_role': 'vendor',
            }).id,
        })

        cls.user_driver = cls.env['res.users'].create({
            'name':     'Test Driver',
            'login':    'test.driver@cargo.test',
            'email':    'test.driver@cargo.test',
            'groups_id': [(6, 0, [cls.group_driver.id])],
            'partner_id': cls.env['res.partner'].create({
                'name':       'Test Driver',
                'cargo_role': 'driver',
            }).id,
        })

        cls.user_admin = cls.env['res.users'].create({
            'name':     'Test Admin',
            'login':    'test.admin@cargo.test',
            'email':    'test.admin@cargo.test',
            'groups_id': [(6, 0, [cls.group_admin.id])],
        })

    def get_config(self, key: str, default: str = '') -> str:
        """Retrieve an ir.config_parameter value."""
        return self.env['ir.config_parameter'].sudo().get_param(key, default)

    def set_config(self, key: str, value: str) -> None:
        """Set an ir.config_parameter value."""
        self.env['ir.config_parameter'].sudo().set_param(key, value)
