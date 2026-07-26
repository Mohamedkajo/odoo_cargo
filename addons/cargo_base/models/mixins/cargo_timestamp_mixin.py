# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
CargoTimestampMixin
===================
Abstract mixin that adds `created_at` and `updated_at` fields to any model.

Usage::

    class CargoStore(models.Model):
        _name        = 'cargo.store'
        _inherit     = ['cargo.timestamp.mixin']
        _description = 'Cargo Store'

Both fields are read-only and set automatically by the ORM.
`created_at` is immutable after creation.
`updated_at` is refreshed on every write.
"""

from odoo import api, fields, models


class CargoTimestampMixin(models.AbstractModel):
    """Abstract mixin — supplies immutable created_at and auto-refreshed updated_at."""

    _name        = 'cargo.timestamp.mixin'
    _description = 'Cargo Timestamp Mixin'

    created_at = fields.Datetime(
        string='Created At',
        required=True,
        readonly=True,
        default=fields.Datetime.now,
        copy=False,
        help='Timestamp when this record was first created. Never changes.',
    )
    updated_at = fields.Datetime(
        string='Updated At',
        readonly=True,
        copy=False,
        help='Timestamp of the last modification to this record.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        now = fields.Datetime.now()
        for vals in vals_list:
            vals.setdefault('created_at', now)
            vals['updated_at'] = now
        return super().create(vals_list)

    def write(self, vals):
        vals['updated_at'] = fields.Datetime.now()
        return super().write(vals)
