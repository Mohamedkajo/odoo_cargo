# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo.coupon — Discount coupons and promotional codes.

Coupons are applied at cart checkout.  On success the discount is stored on
sale.order.cargo_discount and the code on sale.order.cargo_coupon_code.

Coupon types:
  flat     — fixed EGP discount
  percent  — percentage of order subtotal
  delivery — waive the delivery fee
"""
import logging
import string
import secrets

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

COUPON_TYPES = [
    ('flat',     'Flat Discount (EGP)'),
    ('percent',  'Percentage Discount'),
    ('delivery', 'Free Delivery'),
]


class CargoCoupon(models.Model):
    _name = 'cargo.coupon'
    _description = 'Cargo Coupon'
    _rec_name = 'code'
    _order = 'create_date desc'

    code        = fields.Char('Code', required=True, index=True, copy=False)
    description = fields.Char('Description')
    coupon_type = fields.Selection(COUPON_TYPES, 'Type', required=True, default='flat')

    discount_value   = fields.Float('Discount Value',     digits=(10, 2))
    discount_percent = fields.Float('Discount Percent (%)', digits=(5, 2))
    min_order_value  = fields.Float('Min Order (EGP)',    digits=(10, 2), default=0.0)
    max_discount     = fields.Float('Max Discount (EGP)', digits=(10, 2),
                                    help='Cap on percentage discounts. 0 = no cap.')

    # ── Validity ──────────────────────────────────────────────────────────────
    valid_from  = fields.Date('Valid From')
    valid_until = fields.Date('Valid Until')
    is_active   = fields.Boolean('Active', default=True, index=True)

    # ── Usage limits ──────────────────────────────────────────────────────────
    usage_limit      = fields.Integer('Total Usage Limit', default=0,
                                       help='0 = unlimited.')
    usage_per_user   = fields.Integer('Per-User Limit', default=1)
    used_count       = fields.Integer('Times Used', readonly=True, default=0)

    # ── Scoping (optional) ────────────────────────────────────────────────────
    store_id = fields.Many2one(
        'cargo.store', 'Restricted to Store',
        ondelete='set null',
        help='Leave empty to apply across all stores.',
    )

    _sql_constraints = [
        ('unique_code', 'UNIQUE(code)', 'Coupon code must be unique.'),
    ]

    # ── Helpers ───────────────────────────────────────────────────────────────

    @api.model
    def generate_code(self, length=8) -> str:
        """Generate a unique random code."""
        alphabet = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(secrets.choice(alphabet) for _ in range(length))
            if not self.sudo().search([('code', '=', code)], limit=1):
                return code

    def validate_and_apply(self, code: str, subtotal: float,
                           user_id: int, store_id=None) -> dict:
        """
        Validate a coupon code and return the discount details.

        Returns:
            { discount: float, deliveryWaived: bool, couponId: int }

        Raises UserError if the coupon is invalid.
        """
        coupon = self.sudo().search([
            ('code', '=', code.strip().upper()),
            ('is_active', '=', True),
        ], limit=1)
        if not coupon:
            raise UserError('Coupon code is not valid or has expired.')

        # Date validity
        today = fields.Date.today()
        if coupon.valid_from and today < coupon.valid_from:
            raise UserError('This coupon is not yet active.')
        if coupon.valid_until and today > coupon.valid_until:
            raise UserError('This coupon has expired.')

        # Minimum order
        if subtotal < coupon.min_order_value:
            raise UserError(
                f'Minimum order of EGP {coupon.min_order_value:.2f} required.'
            )

        # Usage limits
        if coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
            raise UserError('This coupon has reached its usage limit.')
        if coupon.usage_per_user:
            used_by_user = self.env['sale.order'].sudo().search_count([
                ('cargo_coupon_code', '=', code.strip().upper()),
                ('partner_id.user_ids', 'in', [user_id]),
            ])
            if used_by_user >= coupon.usage_per_user:
                raise UserError('You have already used this coupon.')

        # Store restriction
        if coupon.store_id and store_id and coupon.store_id.id != store_id:
            raise UserError('This coupon is not valid for this store.')

        # Calculate discount
        delivery_waived = False
        discount = 0.0
        if coupon.coupon_type == 'flat':
            discount = coupon.discount_value
        elif coupon.coupon_type == 'percent':
            discount = subtotal * (coupon.discount_percent / 100.0)
            if coupon.max_discount:
                discount = min(discount, coupon.max_discount)
        elif coupon.coupon_type == 'delivery':
            delivery_waived = True

        return {
            'discount':       round(discount, 2),
            'deliveryWaived': delivery_waived,
            'couponId':       coupon.id,
        }

    def mark_used(self):
        """Increment the used count after an order is placed."""
        self.write({'used_count': self.used_count + 1})

    def to_coupon_dict(self) -> dict:
        self.ensure_one()
        return {
            'id':              self.id,
            'code':            self.code,
            'description':     self.description or '',
            'type':            self.coupon_type,
            'discountValue':   self.discount_value,
            'discountPercent': self.discount_percent,
            'minOrder':        self.min_order_value,
            'validUntil':      str(self.valid_until) if self.valid_until else None,
        }
