# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo.inventory — Per-product, per-store stock tracking.

Tracks available quantity for each product.template × cargo.store combination.
When available quantity reaches zero, product.template.cargo_is_available is
automatically set to False.  When restocked it is set back to True.

This is a simplified food-delivery inventory model: restaurant items are
tracked by count (portions), not by warehouse locations.  For a full
warehouse-managed deployment, migrate to stock.quant + stock.location.
"""
from odoo import api, fields, models


class CargoInventory(models.Model):
    _name = 'cargo.inventory'
    _description = 'Cargo Product Inventory'
    _rec_name = 'product_id'
    _order = 'store_id, product_id'

    store_id = fields.Many2one(
        'cargo.store', 'Store',
        required=True, ondelete='cascade', index=True,
    )
    product_id = fields.Many2one(
        'product.template', 'Product',
        required=True, ondelete='cascade', index=True,
        domain=[('cargo_store_id', '!=', False)],
        help='product.template record belonging to this store.',
    )

    quantity     = fields.Integer('Quantity in Stock', default=0)
    reserved_qty = fields.Integer('Reserved Quantity', default=0,
                                   help='Quantity held for confirmed but undelivered orders.')
    alert_qty    = fields.Integer('Low-Stock Alert Threshold', default=5)

    available_qty = fields.Integer(
        'Available', compute='_compute_available_qty', store=True,
    )
    is_low_stock = fields.Boolean(
        'Low Stock', compute='_compute_available_qty', store=True,
    )

    _sql_constraints = [
        ('unique_product_store',
         'UNIQUE(product_id, store_id)',
         'Only one inventory entry per product per store.'),
        ('quantity_non_negative',
         'CHECK(quantity >= 0)',
         'Stock quantity cannot be negative.'),
        ('reserved_non_negative',
         'CHECK(reserved_qty >= 0)',
         'Reserved quantity cannot be negative.'),
    ]

    @api.depends('quantity', 'reserved_qty', 'alert_qty')
    def _compute_available_qty(self):
        for inv in self:
            inv.available_qty = max(0, inv.quantity - inv.reserved_qty)
            inv.is_low_stock  = inv.available_qty <= inv.alert_qty

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_product_availability()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'quantity' in vals or 'reserved_qty' in vals:
            self._sync_product_availability()
        return res

    def _sync_product_availability(self):
        """Set product.template.cargo_is_available based on available_qty."""
        for inv in self:
            is_available = inv.available_qty > 0
            if inv.product_id.cargo_is_available != is_available:
                inv.product_id.sudo().write({'cargo_is_available': is_available})

    def adjust(self, delta: int):
        """Add (positive) or subtract (negative) stock."""
        self.ensure_one()
        new_qty = max(0, self.quantity + delta)
        self.write({'quantity': new_qty})

    def to_inventory_dict(self) -> dict:
        self.ensure_one()
        return {
            'id':           self.id,
            'storeId':      self.store_id.id,
            'storeName':    self.store_id.name,
            'productId':    self.product_id.id,
            'productName':  self.product_id.name,
            'quantity':     self.quantity,
            'reservedQty':  self.reserved_qty,
            'availableQty': self.available_qty,
            'isLowStock':   self.is_low_stock,
            'alertQty':     self.alert_qty,
        }
