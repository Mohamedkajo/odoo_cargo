# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
Push-notification hooks for order status changes and driver assignment.

This module extends two models that belong to earlier modules:

1. sale.order  (via cargo_base / cargo_order)
   Override ``cargo_transition_status`` to fire customer-facing and
   driver-facing push notifications after a successful status write.

2. cargo.delivery  (via cargo_delivery)
   Override ``create`` to notify the assigned driver the moment a new
   delivery record is created for them.

Notification philosophy
-----------------------
* Customer receives a push for every status change that affects their
  experience: preparing → ready → collecting → delivering → delivered
  and on cancellation.
* Driver receives a push when assigned (delivery created) and when the
  vendor confirms the order is ready for pickup (status = ready).
* All pushes are fail-safe: exceptions are logged but never re-raised.
"""

import json
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)

# ── Customer-facing status messages ───────────────────────────────────────────
# Maps new_status → (title, body)
_CUSTOMER_MESSAGES = {
    'preparing':  (
        '🍳 Order Being Prepared',
        'The restaurant has started preparing your order.',
    ),
    'ready': (
        '✅ Order Ready',
        'Your order is ready and waiting for a driver.',
    ),
    'collecting': (
        '🛵 Driver on the Way to Restaurant',
        'A driver has been assigned and is heading to pick up your order.',
    ),
    'delivering': (
        '📦 Order Out for Delivery',
        'Your order is on its way to you!',
    ),
    'otp_check': (
        '🔑 Confirm Your Delivery',
        'The driver has arrived. Please share your OTP to confirm delivery.',
    ),
    'delivered': (
        '🎉 Order Delivered',
        'Your order has been delivered. Enjoy your meal!',
    ),
    'cancelled': (
        '❌ Order Cancelled',
        'Your order has been cancelled.',
    ),
}

# ── Driver-facing status messages ─────────────────────────────────────────────
_DRIVER_MESSAGES = {
    'ready': (
        '📦 Order Ready for Pickup',
        'The restaurant has confirmed the order is ready. Head to the store now.',
    ),
}


class CargoSaleOrderNotificationHook(models.Model):
    """Extend sale.order to fire push notifications on status transitions."""

    _inherit = 'sale.order'

    def cargo_transition_status(self, new_status: str) -> bool:
        """
        Call super() to do the actual write, then fire push notifications
        to the customer (and driver where relevant) — fail-safe.
        """
        result = super().cargo_transition_status(new_status)

        try:
            self._cargo_send_status_notifications(new_status)
        except Exception:  # noqa: BLE001
            _logger.exception(
                'cargo_notification: failed to send push for order %s → %s',
                self.id, new_status,
            )

        return result

    def _cargo_send_status_notifications(self, new_status: str):
        """
        Internal: fire customer + driver push notifications for ``new_status``.
        Uses a soft-get on ``cargo.notification`` so cargo_base never depends
        on cargo_notification (the dependency is the other way around).
        """
        Notif = self.env.get('cargo.notification')
        if Notif is None:
            return   # cargo_notification not installed

        # ── Customer notification ──────────────────────────────────────────────
        customer_msg = _CUSTOMER_MESSAGES.get(new_status)
        if customer_msg and self.partner_id:
            # Find the res.users record for this customer partner
            customer_user = self.env['res.users'].sudo().search(
                [('partner_id', '=', self.partner_id.id)], limit=1
            )
            if customer_user:
                title, body = customer_msg
                payload = {
                    'type':    'order_update',
                    'orderId': str(self.id),
                    'status':  new_status,
                }
                Notif.sudo().send_to_user(
                    customer_user,
                    title=title,
                    body=body,
                    notif_type='order_update',
                    payload=payload,
                    order=self,
                )

        # ── Driver notification ────────────────────────────────────────────────
        driver_msg = _DRIVER_MESSAGES.get(new_status)
        if driver_msg and self.cargo_driver_id:
            # cargo_driver_id may be Integer (cargo_base) or Many2one (cargo_driver)
            driver_user = None
            if hasattr(self.cargo_driver_id, 'id'):
                # Many2one (cargo_driver installed): it IS a res.users record
                driver_user = self.cargo_driver_id
            else:
                # Integer FK: look up the res.users record
                driver_id_int = int(self.cargo_driver_id)
                if driver_id_int:
                    driver_user = self.env['res.users'].sudo().browse(driver_id_int)

            if driver_user and driver_user.exists():
                title, body = driver_msg
                payload = {
                    'type':    'driver_update',
                    'orderId': str(self.id),
                    'status':  new_status,
                }
                Notif.sudo().send_to_user(
                    driver_user,
                    title=title,
                    body=body,
                    notif_type='driver_update',
                    payload=payload,
                    order=self,
                )


class CargoDeliveryNotificationHook(models.Model):
    """Extend cargo.delivery to notify the driver when they are assigned."""

    _inherit = 'cargo.delivery'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        try:
            self._cargo_notify_driver_assigned(records)
        except Exception:  # noqa: BLE001
            _logger.exception(
                'cargo_notification: failed to send driver assignment push'
            )
        return records

    def _cargo_notify_driver_assigned(self, deliveries):
        """Send a push to each assigned driver when their delivery is created."""
        Notif = self.env.get('cargo.notification')
        if Notif is None:
            return

        for delivery in deliveries:
            if not delivery.driver_id:
                continue

            order_ref = delivery.order_name or f'Order #{delivery.order_id.id}'
            payload = json.dumps({
                'type':       'driver_update',
                'orderId':    str(delivery.order_id.id),
                'deliveryId': str(delivery.id),
                'status':     'assigned',
            })

            Notif.sudo().send_to_user(
                delivery.driver_id,
                title='🛵 New Delivery Assigned',
                body=f'You have been assigned to {order_ref}. Check your app for details.',
                notif_type='driver_update',
                payload={'type': 'driver_update',
                         'orderId': str(delivery.order_id.id),
                         'deliveryId': str(delivery.id)},
                order=delivery.order_id,
            )

            _logger.info(
                'cargo_notification: driver assignment push sent '
                'driver=%s order=%s delivery=%s',
                delivery.driver_id.id, delivery.order_id.id, delivery.id,
            )
