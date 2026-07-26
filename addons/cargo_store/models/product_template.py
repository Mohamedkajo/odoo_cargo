# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
product.template extension — cargo_store fields.

cargo_base could not add cargo_store_id to product.template because cargo.store
did not exist yet (would create a circular dependency).  This module adds the
store association now that cargo.store is defined, and overrides cargo_to_api_dict
to inject the store data the Flutter app expects.
"""
from odoo import fields, models


class CargoStoreProductTemplate(models.Model):
    """Add store association and store-level API dict to product.template."""

    _inherit = 'product.template'

    cargo_store_id = fields.Many2one(
        'cargo.store',
        string='Store',
        index=True,
        ondelete='cascade',
        help='The cargo.store this product belongs to. '
             'All marketplace products must reference a store.',
    )
    cargo_store_name = fields.Char(
        string='Store Name',
        related='cargo_store_id.name',
        store=True,
        readonly=True,
        translate=False,  # cargo_store.name has translate=True; must override or Odoo 18
                          # writes jsonb into a character varying column → DB crash
    )

    # ── API serialisation override ────────────────────────────────────────────

    def cargo_to_api_dict(self) -> dict:
        """Extend cargo_base dict with store data."""
        d = super().cargo_to_api_dict()
        d['storeId']   = self.cargo_store_id.id if self.cargo_store_id else None
        d['storeName'] = self.cargo_store_name or ''
        return d
