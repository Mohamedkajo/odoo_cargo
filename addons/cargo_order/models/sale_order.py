# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
sale.order extension — Cargo order delivery fields.

cargo_base already adds:
  • cargo_status        — delivery FSM (confirmed → … → delivered)
  • cargo_store_id      — store reference (Integer, upgraded to Many2one by cargo_store)
  • cargo_driver_id     — driver reference (Integer, upgraded by cargo_driver if present)
  • cargo_delivery_fee  — Monetary
  • cargo_estimated_time — Integer (minutes)
  • OTP fields (cargo_otp_code, cargo_otp_verified, cargo_otp_expires_at)
  • cargo_commission fields
  • cargo_to_api_dict() / cargo_transition_status() / cargo_verify_otp()

cargo_store upgrades cargo_store_id to Many2one and injects storeName/storeImage.

This module adds:
  • cargo_delivery_address — where to deliver
  • cargo_payment_method   — cash / card / wallet
  • cargo_discount         — coupon / promo discount (EGP)
  • cargo_coupon_code      — applied coupon code

Flutter Order.fromJson complete contract:
  id, orderRef, status, total, subtotal, deliveryFee, discount, itemCount,
  createdAt, storeName, storeImage, items, estimatedTime, paymentMethod,
  couponCode, driverName, driverPhone, driverRating
"""
from odoo import api, fields, models
from odoo.addons.cargo_base.constants import (
    ORDER_STATUSES,
    ORDER_STATUS_CONFIRMED,
    ORDER_TRANSITIONS,
    ORDER_TERMINAL_STATES,
)

PAYMENT_METHODS = [
    ('cash',   'Cash on Delivery'),
    ('card',   'Card'),
    ('wallet', 'Wallet'),
]


class CargoOrderSaleOrder(models.Model):
    """Add delivery-specific fields to sale.order."""

    _inherit = 'sale.order'

    cargo_delivery_address = fields.Char(
        string='Delivery Address',
        help='Customer-supplied delivery address for this order.',
    )
    cargo_payment_method = fields.Selection(
        selection=PAYMENT_METHODS,
        string='Payment Method',
        default='cash',
    )
    cargo_discount = fields.Monetary(
        string='Discount',
        currency_field='currency_id',
        default=0.0,
        help='Coupon or promotional discount applied to this order.',
    )
    cargo_coupon_code = fields.Char(
        string='Coupon Code',
        copy=False,
        help='Code of the coupon that generated cargo_discount.',
    )
    # Driver info (denormalised from res.users driver for quick serialisation)
    cargo_driver_name   = fields.Char('Driver Name',   readonly=True)
    cargo_driver_phone  = fields.Char('Driver Phone',  readonly=True)
    cargo_driver_rating = fields.Float('Driver Rating', digits=(3, 1), default=0.0)

    # ── API dict override ──────────────────────────────────────────────────────

    def cargo_to_api_dict(self) -> dict:
        d = super().cargo_to_api_dict()
        d['deliveryAddress'] = self.cargo_delivery_address or ''
        d['paymentMethod']   = self.cargo_payment_method or 'cash'
        d['couponCode']      = self.cargo_coupon_code or None
        d['discount']        = self.cargo_discount or 0.0
        d['driverName']      = self.cargo_driver_name or None
        d['driverPhone']     = self.cargo_driver_phone or None
        d['driverRating']    = self.cargo_driver_rating or 0.0
        return d

    def cargo_to_api_detail_dict(self) -> dict:
        """Extended dict including status timeline."""
        self.ensure_one()
        d = self.cargo_to_api_dict()
        statuses = [s[0] for s in ORDER_STATUSES]
        current_idx = statuses.index(self.cargo_status) if self.cargo_status in statuses else 0
        timeline = []
        for idx, (s_key, s_label) in enumerate(ORDER_STATUSES):
            if s_key == 'cancelled':
                continue
            completed = (idx <= current_idx and self.cargo_status != 'cancelled')
            timeline.append({
                'status':    s_key,
                'label':     s_label,
                'completed': completed,
                'timestamp': self.date_order.isoformat() if completed and self.date_order else None,
            })
        d['timeline'] = timeline
        return d

    # ── Helper: assign driver ─────────────────────────────────────────────────

    def cargo_assign_driver(self, driver_user):
        """Assign a driver user to this order."""
        self.ensure_one()
        self.write({
            'cargo_driver_id':    driver_user.id,
            'cargo_driver_name':  driver_user.name,
            'cargo_driver_phone': driver_user.partner_id.phone,
            'cargo_driver_rating': driver_user.cargo_driver_rating,
        })
