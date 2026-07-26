# -*- coding: utf-8 -*-
"""res.users extension for cargo_store — vendor store link."""
from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    cargo_store_id = fields.Many2one(
        'cargo.store', 'My Store',
        help='Store managed by this vendor user.',
    )
