# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo.order and cargo.order.line — Cargo delivery orders.

Status flow (from cargo_base.constants):
  confirmed → preparing → ready → collecting → delivering → otp_check → delivered
  Any non-terminal state can transition to: cancelled

Flutter Order.fromJson fields:
  id, status, total, subtotal, deliveryFee, itemCount, createdAt,
  storeName, storeImage, items, estimatedTime, driverName, driverPhone, driverRating

Flutter OrderItem fields:
  productId, name, price, quantity, image
"""
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

from cargo_base.constants import (
    ORDER_STATUSES,
    ORDER_TERMINAL_STATES,
    ORDER_TRANSITIONS,
    ORDER_STATUS_CONFIRMED,
    ORDER_STATUS_CANCELLED,
)

_logger = logging.getLogger(__name__)

# Payment method options
PAYMENT_METHODS = [
    ('cash',   'Cash on Delivery'),
    ('card',   'Card'),
    ('wallet', 'Wallet'),
]


class CargoOrder(models.Model):
    _name = 'cargo.order'
    _description = 'Cargo Delivery Order'
    _order = 'id desc'
    _rec_name = 'name'

    # ── Identity ──────────────────────────────────────────────────────────────
    name = fields.Char('Order Ref', required=True, readonly=True, default='New')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('cargo.order') or 'New'
        return super().create(vals)

    # ── Relations ─────────────────────────────────────────────────────────────
    user_id = fields.Many2one(
        'res.users', 'Customer',
        required=True, ondelete='restrict', index=True,
    )
    store_id = fields.Many2one('cargo.store', 'Store', ondelete='set null')
    store_name  = fields.Char('Store Name')
    store_image = fields.Char('Store Image URL')
    driver_id   = fields.Many2one('res.users', 'Assigned Driver', domain=[('cargo_role', '=', 'driver')])
    driver_name = fields.Char('Driver Name')
    driver_phone = fields.Char('Driver Phone')
    driver_rating = fields.Float('Driver Rating', digits=(3, 1), default=0.0)

    # ── Financial ─────────────────────────────────────────────────────────────
    subtotal     = fields.Float('Subtotal',      digits=(10, 2))
    delivery_fee = fields.Float('Delivery Fee',  digits=(10, 2), default=15.0)
    discount     = fields.Float('Discount',      digits=(10, 2), default=0.0)
    total        = fields.Float('Total',         digits=(10, 2))
    payment_method = fields.Selection(PAYMENT_METHODS, 'Payment Method', default='cash')

    # ── Delivery ──────────────────────────────────────────────────────────────
    delivery_address = fields.Char('Delivery Address', required=True)
    estimated_time   = fields.Char('Estimated Time', default='30-45 Min')
    coupon_code      = fields.Char('Coupon Code')

    # ── Status ────────────────────────────────────────────────────────────────
    status = fields.Selection(
        selection=ORDER_STATUSES,
        string='Status',
        default=ORDER_STATUS_CONFIRMED,
        index=True,
        tracking=True,
    )
    item_count = fields.Integer('Item Count', default=0)

    # ── Lines ─────────────────────────────────────────────────────────────────
    line_ids = fields.One2many('cargo.order.line', 'order_id', string='Order Lines')

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at = fields.Datetime('Ordered At', default=fields.Datetime.now, readonly=True)
    updated_at = fields.Datetime('Updated At', default=fields.Datetime.now)

    # ── Status transitions ────────────────────────────────────────────────────

    def action_cancel(self, reason=None):
        """Cancel this order if the current status allows it."""
        for order in self:
            if order.status in ORDER_TERMINAL_STATES:
                raise UserError(
                    f'Cannot cancel order {order.name}: it is already {order.status}.'
                )
            allowed = ORDER_TRANSITIONS.get(order.status, set())
            if ORDER_STATUS_CANCELLED not in allowed:
                raise UserError(
                    f'Order {order.name} (status: {order.status}) cannot be cancelled at this stage.'
                )
            order.write({
                'status':     ORDER_STATUS_CANCELLED,
                'updated_at': fields.Datetime.now(),
            })

    # ── Flutter dict ──────────────────────────────────────────────────────────

    def to_order_dict(self):
        self.ensure_one()
        return {
            'id':            self.id,
            'status':        self.status,
            'total':         self.total,
            'subtotal':      self.subtotal,
            'deliveryFee':   self.delivery_fee,
            'discount':      self.discount,
            'itemCount':     self.item_count,
            'createdAt':     self.created_at.isoformat() if self.created_at else None,
            'storeName':     self.store_name or None,
            'storeImage':    self.store_image or None,
            'estimatedTime': self.estimated_time or '30-45 Min',
            'driverName':    self.driver_name or None,
            'driverPhone':   self.driver_phone or None,
            'driverRating':  self.driver_rating or 0.0,
            'paymentMethod': self.payment_method or 'cash',
            'couponCode':    self.coupon_code or None,
            'items':         [l.to_line_dict() for l in self.line_ids],
        }

    def to_order_detail_dict(self):
        self.ensure_one()
        d = self.to_order_dict()
        # Build status timeline
        statuses = [s[0] for s in ORDER_STATUSES]
        current_idx = statuses.index(self.status) if self.status in statuses else 0
        import datetime
        timeline = []
        for idx, (s_key, s_label) in enumerate(ORDER_STATUSES):
            if s_key == ORDER_STATUS_CANCELLED:
                continue
            completed = (idx <= current_idx and self.status != ORDER_STATUS_CANCELLED)
            timeline.append({
                'status':    s_key,
                'label':     s_label,
                'completed': completed,
                'timestamp': self.created_at.isoformat() if completed else None,
            })
        d['timeline'] = timeline
        return d


class CargoOrderLine(models.Model):
    _name = 'cargo.order.line'
    _description = 'Cargo Order Line'
    _order = 'id'

    order_id = fields.Many2one('cargo.order', 'Order', required=True, ondelete='cascade', index=True)
    product_id = fields.Many2one('cargo.product', 'Product', ondelete='set null')
    name = fields.Char('Product Name', required=True)
    image = fields.Char('Image URL')
    price = fields.Float('Unit Price', required=True, digits=(10, 2))
    quantity = fields.Integer('Quantity', default=1)
    variant = fields.Char('Variant')
    special_instructions = fields.Char('Special Instructions')

    def to_line_dict(self):
        self.ensure_one()
        return {
            'productId': self.product_id.id if self.product_id else None,
            'name':      self.name or '',
            'price':     self.price,
            'quantity':  self.quantity,
            'image':     self.image or None,
        }
