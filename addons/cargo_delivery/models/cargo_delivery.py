# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo.delivery — Delivery record linking a sale.order to its assigned driver.

Lifecycle:
  assigned → picked_up → on_the_way → delivered
                       ↘ failed

OTP flow:
  * pickup_otp  — vendor hands to driver at store pickup (verified by vendor)
  * delivery_otp — customer confirms delivery (verified by driver app)

Driver FK: res.users with cargo_role = 'driver'
Order FK:  sale.order with cargo_status set (extended by cargo_base)
"""
import random
import string

from odoo import api, fields, models
from odoo.exceptions import UserError

DELIVERY_STATES = [
    ('assigned',   'Driver Assigned'),
    ('picked_up',  'Picked Up'),
    ('on_the_way', 'On the Way'),
    ('delivered',  'Delivered'),
    ('failed',     'Failed'),
]

DELIVERY_TRANSITIONS = {
    'assigned':   ['picked_up', 'failed'],
    'picked_up':  ['on_the_way', 'failed'],
    'on_the_way': ['delivered', 'failed'],
}


def _otp():
    return ''.join(random.choices(string.digits, k=4))


class CargoDelivery(models.Model):
    _name = 'cargo.delivery'
    _description = 'Cargo Delivery'
    _rec_name = 'order_id'
    _order = 'create_date desc'

    # ── Core FKs (native models) ──────────────────────────────────────────────
    order_id = fields.Many2one(
        'sale.order', 'Order',
        required=True, ondelete='cascade', index=True,
        domain=[('cargo_status', '!=', False)],
        help='The sale.order this delivery record tracks.',
    )
    driver_id = fields.Many2one(
        'res.users', 'Driver',
        domain=[('cargo_role', '=', 'driver')],
        ondelete='set null', index=True,
        help='The res.users driver assigned to this delivery.',
    )

    status = fields.Selection(DELIVERY_STATES, 'Status', default='assigned', index=True)

    # ── OTPs ──────────────────────────────────────────────────────────────────
    pickup_otp   = fields.Char('Pickup OTP',   readonly=True)
    delivery_otp = fields.Char('Delivery OTP', readonly=True)

    # ── Timestamps ────────────────────────────────────────────────────────────
    assigned_at  = fields.Datetime('Assigned At',  default=fields.Datetime.now)
    picked_up_at = fields.Datetime('Picked Up At')
    delivered_at = fields.Datetime('Delivered At')

    # ── Live location (written by driver app via /api/driver/location) ────────
    driver_lat  = fields.Float('Driver Latitude',  digits=(10, 7))
    driver_lng  = fields.Float('Driver Longitude', digits=(10, 7))
    eta_minutes = fields.Integer('ETA (min)')

    # ── Denormalised for quick display ────────────────────────────────────────
    order_name    = fields.Char(related='order_id.name',              store=True, readonly=True, translate=False)
    customer_name = fields.Char(related='order_id.partner_id.name',   store=True, readonly=True)
    driver_name   = fields.Char(related='driver_id.name',             store=True, readonly=True, translate=False)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.setdefault('pickup_otp',   _otp())
            vals.setdefault('delivery_otp', _otp())
        return super().create(vals_list)

    def transition(self, new_status: str):
        """Advance delivery status, updating the parent sale.order.cargo_status."""
        self.ensure_one()
        allowed = DELIVERY_TRANSITIONS.get(self.status, [])
        if new_status not in allowed:
            raise UserError(
                f'Cannot move delivery from "{self.status}" to "{new_status}".'
            )
        write_vals = {'status': new_status}
        if new_status == 'picked_up':
            write_vals['picked_up_at'] = fields.Datetime.now()
        elif new_status == 'delivered':
            write_vals['delivered_at'] = fields.Datetime.now()
            self.order_id.cargo_transition_status('delivered')
            # Update driver stats
            if self.driver_id:
                self.driver_id.sudo().write({
                    'cargo_driver_total_deliveries':
                        self.driver_id.cargo_driver_total_deliveries + 1,
                    'cargo_driver_total_earnings':
                        self.driver_id.cargo_driver_total_earnings
                        + (self.order_id.cargo_delivery_fee or 0),
                })
        self.write(write_vals)

    def to_delivery_dict(self) -> dict:
        self.ensure_one()
        return {
            'id':          self.id,
            'orderId':     self.order_id.id,
            'orderRef':    self.order_name or '',
            'status':      self.status,
            'driverId':    self.driver_id.id if self.driver_id else None,
            'driverName':  self.driver_name or None,
            'driverLat':   self.driver_lat or None,
            'driverLng':   self.driver_lng or None,
            'etaMinutes':  self.eta_minutes or None,
            'assignedAt':  self.assigned_at.isoformat() if self.assigned_at else None,
            'deliveredAt': self.delivered_at.isoformat() if self.delivered_at else None,
        }
