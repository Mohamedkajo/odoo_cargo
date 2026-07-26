# -*- coding: utf-8 -*-
"""
cargo.delivery — Delivery record linking an order to its assigned driver.

Lifecycle:
  assigned → picked_up → on_the_way → delivered
                       ↘ failed

OTP flow:
  * pickup_otp  — vendor hands this to driver at store pickup
  * delivery_otp — customer must confirm delivery; generated on creation
"""
import random
import string

from odoo import api, fields, models

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

    order_id  = fields.Many2one('cargo.order',  'Order',  required=True, ondelete='cascade', index=True)
    driver_id = fields.Many2one('cargo.driver', 'Driver', ondelete='set null', index=True)

    status = fields.Selection(DELIVERY_STATES, 'Status', default='assigned', index=True)

    # OTPs
    pickup_otp   = fields.Char('Pickup OTP',   readonly=True)
    delivery_otp = fields.Char('Delivery OTP', readonly=True)

    # Timestamps
    assigned_at  = fields.Datetime('Assigned At',  default=fields.Datetime.now)
    picked_up_at = fields.Datetime('Picked Up At')
    delivered_at = fields.Datetime('Delivered At')

    # Live location (written by driver app)
    driver_lat   = fields.Float('Driver Latitude',  digits=(10, 7))
    driver_lng   = fields.Float('Driver Longitude', digits=(10, 7))
    eta_minutes  = fields.Integer('ETA (min)')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('pickup_otp'):
                vals['pickup_otp'] = _otp()
            if not vals.get('delivery_otp'):
                vals['delivery_otp'] = _otp()
        return super().create(vals_list)

    def advance_status(self, new_status):
        self.ensure_one()
        allowed = DELIVERY_TRANSITIONS.get(self.status, [])
        if new_status not in allowed:
            raise ValueError(
                f'Cannot transition delivery from {self.status!r} to {new_status!r}.'
            )
        vals = {'status': new_status}
        if new_status == 'picked_up':
            vals['picked_up_at'] = fields.Datetime.now()
        elif new_status == 'delivered':
            vals['delivered_at'] = fields.Datetime.now()
            # Increment driver delivery count
            if self.driver_id:
                self.driver_id.sudo().write({
                    'total_deliveries': self.driver_id.total_deliveries + 1,
                })
        self.write(vals)

    def to_tracking_dict(self):
        """Compact dict for Flutter's order tracking screen."""
        self.ensure_one()
        driver = self.driver_id
        return {
            'deliveryId':   self.id,
            'status':       self.status,
            'driver': {
                'id':    driver.id,
                'name':  driver.display_name,
                'phone': driver.user_id.phone if driver else None,
                'lat':   self.driver_lat or None,
                'lng':   self.driver_lng or None,
            } if driver else None,
            'etaMinutes':  self.eta_minutes,
            'assignedAt':  self.assigned_at.isoformat() if self.assigned_at else None,
            'pickedUpAt':  self.picked_up_at.isoformat() if self.picked_up_at else None,
            'deliveredAt': self.delivered_at.isoformat() if self.delivered_at else None,
        }
