# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo.coupon.usage — per-user redemption tracking.

Each row records one coupon use by one customer so the system can enforce
per-user usage limits without scanning sale.order every time.
"""
from odoo import fields, models


class CargoCouponUsage(models.Model):
    _name = 'cargo.coupon.usage'
    _description = 'Cargo Coupon Usage'
    _order = 'create_date desc'

    coupon_id = fields.Many2one(
        'cargo.coupon', 'Coupon', required=True, ondelete='cascade', index=True,
    )
    user_id = fields.Many2one(
        'res.users', 'Customer', required=True, ondelete='cascade', index=True,
    )
    order_id = fields.Many2one(
        'sale.order', 'Order', ondelete='set null',
    )
    discount_amount = fields.Float('Discount Applied (EGP)', digits=(10, 2))

    _sql_constraints = [
        ('unique_coupon_user_order',
         'UNIQUE(coupon_id, user_id, order_id)',
         'Duplicate coupon usage record.'),
    ]
