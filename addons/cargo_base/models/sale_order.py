# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
sale.order extension — Cargo marketplace fields.

Extends Odoo's native sale.order with the Cargo delivery status machine,
OTP confirmation, commission calculation and driver association.

store_id and driver_id are Integer fields here because cargo.store and
cargo.driver do not exist yet (they are defined in cargo_store and
cargo_driver modules).  Those modules upgrade these fields to proper
Many2one relational fields via further _inherit of sale.order.
"""

import logging
import random
import string
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

from ..constants import (
    ORDER_STATUSES,
    ORDER_STATUS_CONFIRMED,
    ORDER_TRANSITIONS,
    OTP_LENGTH,
    OTP_EXPIRY_MINUTES,
)


class CargoSaleOrder(models.Model):
    """Extend sale.order with Cargo marketplace delivery and financial fields."""

    _inherit = 'sale.order'

    # ── Cargo order status (parallel to Odoo native state) ────────────────────
    cargo_status = fields.Selection(
        selection=ORDER_STATUSES,
        string='Cargo Status',
        default=ORDER_STATUS_CONFIRMED,
        index=True,
        tracking=True,
        copy=False,
        help='Cargo-specific delivery workflow status.',
    )

    # ── Store & Driver references (Integer FK — upgraded by cargo_store/driver) ─
    cargo_store_id = fields.Integer(
        string='Store ID',
        index=True,
        copy=False,
        help='Internal ID of the cargo.store. Upgraded to Many2one by cargo_store module.',
    )
    cargo_driver_id = fields.Integer(
        string='Driver ID',
        index=True,
        copy=False,
        help='Internal ID of the cargo.driver. Upgraded to Many2one by cargo_driver module.',
    )

    # ── Delivery ──────────────────────────────────────────────────────────────
    cargo_delivery_fee = fields.Monetary(
        string='Delivery Fee',
        currency_field='currency_id',
        default=0.0,
        help='Delivery fee charged to the customer.',
    )
    cargo_estimated_time = fields.Integer(
        string='Estimated Time (min)',
        default=0,
        help='Estimated delivery time in minutes.',
    )

    # ── Commission & Vendor Earnings ──────────────────────────────────────────
    cargo_commission_rate = fields.Float(
        string='Commission Rate (%)',
        digits=(5, 2),
        default=0.0,
        help='Platform commission percentage for this order.',
    )
    cargo_commission_amount = fields.Monetary(
        string='Commission Amount',
        currency_field='currency_id',
        compute='_compute_cargo_financials',
        store=True,
        help='Platform commission = order total × commission rate.',
    )
    cargo_vendor_earnings = fields.Monetary(
        string='Vendor Earnings',
        currency_field='currency_id',
        compute='_compute_cargo_financials',
        store=True,
        help='Amount credited to the vendor wallet after commission.',
    )

    # ── OTP Delivery Verification ─────────────────────────────────────────────
    cargo_otp_code = fields.Char(
        string='OTP Code',
        size=6,
        copy=False,
        help='One-time passcode sent to the customer to confirm delivery.',
    )
    cargo_otp_verified = fields.Boolean(
        string='OTP Verified',
        default=False,
        copy=False,
        tracking=True,
    )
    cargo_otp_expires_at = fields.Datetime(
        string='OTP Expires At',
        copy=False,
    )

    # ── SQL constraints ───────────────────────────────────────────────────────
    _sql_constraints = [
        (
            'cargo_commission_rate_range',
            'CHECK (cargo_commission_rate >= 0 AND cargo_commission_rate <= 100)',
            'Commission rate must be between 0 and 100.',
        ),
        (
            'cargo_delivery_fee_positive',
            'CHECK (cargo_delivery_fee >= 0)',
            'Delivery fee cannot be negative.',
        ),
    ]

    # ── Computes ──────────────────────────────────────────────────────────────

    @api.depends('amount_total', 'cargo_commission_rate')
    def _compute_cargo_financials(self):
        for order in self:
            if order.cargo_commission_rate > 0:
                commission = order.amount_total * (order.cargo_commission_rate / 100.0)
                order.cargo_commission_amount = round(commission, 2)
                order.cargo_vendor_earnings   = round(order.amount_total - commission, 2)
            else:
                order.cargo_commission_amount = 0.0
                order.cargo_vendor_earnings   = order.amount_total

    # ── Status-change notification hook ──────────────────────────────────────

    # Maps cargo_status values to (title, body) push messages sent to the customer.
    _CARGO_STATUS_MESSAGES = {
        'preparing':  (
            'Order Being Prepared 🍳',
            'Your order is being prepared by the vendor.',
        ),
        'ready': (
            'Order Ready 📦',
            'Your order is ready and waiting for driver pickup.',
        ),
        'collecting': (
            'Driver on the Way 🚗',
            'A driver has been assigned and is heading to the store.',
        ),
        'delivering': (
            'Order En Route 🚀',
            'Your order is on the way! Track your driver on the map.',
        ),
        'otp_check': (
            'Driver Arrived 📍',
            'Your driver has arrived. Provide your OTP to confirm delivery.',
        ),
        'delivered': (
            'Order Delivered ✅',
            'Your order has been delivered. Enjoy!',
        ),
        'cancelled': (
            'Order Cancelled ❌',
            'Your order has been cancelled.',
        ),
    }

    def write(self, vals):
        # Snapshot pre-write statuses so we can detect changes after super().
        old_statuses = {}
        if 'cargo_status' in vals:
            old_statuses = {order.id: order.cargo_status for order in self}

        result = super().write(vals)

        if old_statuses:
            new_status = vals['cargo_status']
            for order in self:
                old = old_statuses.get(order.id)
                if old != new_status:
                    order._cargo_notify_customer_status_change(old, new_status)

        return result

    def _cargo_notify_customer_status_change(self, old_status: str, new_status: str):
        """
        Fire a push notification to the customer when cargo_status changes.

        Fails silently — a notification error must never break the status write.
        """
        msg = self._CARGO_STATUS_MESSAGES.get(new_status)
        if not msg:
            return  # no message defined for this transition

        Notif = self.env.get('cargo.notification')
        if Notif is None:
            return  # cargo_notification module not installed

        title, body = msg
        # Find the active customer user(s) linked to the order's partner.
        customer_users = self.partner_id.user_ids.filtered(lambda u: u.active)
        for user in customer_users:
            try:
                Notif.send_to_user(
                    user=user,
                    title=title,
                    body=body,
                    notif_type='order_update',
                    payload={
                        'orderId':    self.id,
                        'orderRef':   self.name or '',
                        'status':     new_status,
                        'prevStatus': old_status or '',
                    },
                    order=self,
                )
            except Exception:
                _logger.exception(
                    'cargo.notification: failed to notify user %s for order %s '
                    'status change %s → %s',
                    user.id, self.id, old_status, new_status,
                )

    # ── Status transition ─────────────────────────────────────────────────────

    def cargo_transition_status(self, new_status: str) -> bool:
        """
        Attempt to transition the order to ``new_status``.

        Validates the transition against the state machine defined in
        ``constants.ORDER_TRANSITIONS``.  Raises ``UserError`` if the
        transition is not permitted.

        Returns True on success.
        """
        self.ensure_one()
        current = self.cargo_status or ORDER_STATUS_CONFIRMED
        allowed = ORDER_TRANSITIONS.get(current, set())

        if new_status not in allowed:
            raise UserError(
                f"Cannot move order {self.name!r} from {current!r} to {new_status!r}. "
                f"Allowed transitions: {', '.join(sorted(allowed)) or 'none (terminal state)'}."
            )

        write_vals = {'cargo_status': new_status}

        # Generate OTP when the driver starts collecting the order
        if new_status == 'collecting':
            write_vals.update(self._cargo_generate_otp_vals())

        self.write(write_vals)
        return True

    # ── OTP helpers ───────────────────────────────────────────────────────────

    def _cargo_generate_otp_vals(self) -> dict:
        """
        Return a write-ready dict containing a fresh OTP code and its expiry.
        Called automatically when an order transitions to ``collecting``.
        """
        otp     = ''.join(random.choices(string.digits, k=OTP_LENGTH))
        expires = fields.Datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)
        return {
            'cargo_otp_code':       otp,
            'cargo_otp_verified':   False,
            'cargo_otp_expires_at': expires,
        }

    def cargo_verify_otp(self, otp: str) -> bool:
        """
        Verify the OTP provided by the driver at the point of delivery.

        Args:
            otp: The code entered by the driver on the Driver App.

        Returns:
            True if verification succeeded.

        Raises:
            UserError: If OTP is missing, expired, or incorrect.
        """
        self.ensure_one()
        now = fields.Datetime.now()

        if not self.cargo_otp_code:
            raise UserError('No OTP has been generated for this order.')
        if self.cargo_otp_expires_at and now > self.cargo_otp_expires_at:
            raise UserError('OTP has expired. Please request a new one.')
        if self.cargo_otp_code != otp:
            raise UserError('Invalid OTP code.')

        self.write({'cargo_otp_verified': True})
        return True

    # ── API serialisation ─────────────────────────────────────────────────────

    def cargo_to_api_dict(self) -> dict:
        """
        Return a dict matching the Flutter Order model exactly.
        ``storeName``, ``storeImage``, ``driverName``, ``driverPhone`` and
        ``driverRating`` are populated by cargo_store and cargo_driver modules
        via super() chaining on _inherit.
        """
        self.ensure_one()
        return {
            'id':            self.id,
            'orderRef':      self.name or '',
            'status':        self.cargo_status or ORDER_STATUS_CONFIRMED,
            'total':         self.amount_total,
            'subtotal':      self.amount_untaxed,
            'deliveryFee':   self.cargo_delivery_fee,
            'itemCount':     int(sum(line.product_uom_qty for line in self.order_line)),
            'createdAt':     self.date_order.isoformat() if self.date_order else '',
            'storeName':     '',
            'storeImage':    '',
            'items':         [line.cargo_to_api_dict() for line in self.order_line],
            'estimatedTime': self.cargo_estimated_time,
            'driverName':    '',
            'driverPhone':   '',
            'driverRating':  0.0,
        }


class CargoSaleOrderLine(models.Model):
    """Extend sale.order.line with Cargo API serialisation helper."""

    _inherit = 'sale.order.line'

    def cargo_to_api_dict(self) -> dict:
        """Return a dict matching the Flutter OrderItem model."""
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url', 'http://localhost:8069'
        )
        tmpl_id   = self.product_id.product_tmpl_id.id if self.product_id else 0
        image_url = (
            f'{base_url}/web/image/product.template/{tmpl_id}/image_256'
            if self.product_id and self.product_id.image_256 else ''
        )
        return {
            'productId': self.product_id.id if self.product_id else 0,
            'name':      self.product_id.name if self.product_id else self.name,
            'price':     self.price_unit,
            'quantity':  int(self.product_uom_qty),
            'image':     image_url,
        }
