# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
sale.order extension — upgrade cargo_store_id to a proper Many2one.

cargo_base declared cargo_store_id as an Integer field because cargo.store
was not yet defined.  Now that cargo.store exists, this module upgrades
the field to a Many2one FK so relationships, ORM queries, and Odoo UI all
work correctly.

This also injects store data into the sale.order API dict.
"""
from odoo import fields, models


class CargoStoreSaleOrder(models.Model):
    """Upgrade cargo_store_id on sale.order to a proper Many2one."""

    _inherit = 'sale.order'

    # Upgrade Integer → Many2one (field redeclaration is supported in _inherit)
    cargo_store_id = fields.Many2one(
        'cargo.store',
        string='Store',
        index=True,
        ondelete='set null',
        copy=False,
        help='The cargo.store this order was placed at.',
    )
    cargo_store_image = fields.Char(
        string='Store Image URL',
        related='cargo_store_id.image',
        store=False,
        readonly=True,
    )

    def cargo_to_api_dict(self) -> dict:
        """Inject store name and image into the API dict."""
        d = super().cargo_to_api_dict()
        d['storeName']  = self.cargo_store_id.name  if self.cargo_store_id else ''
        d['storeImage'] = self.cargo_store_id.image if self.cargo_store_id else ''
        return d
