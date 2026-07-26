# -*- coding: utf-8 -*-
"""
cargo.driver — Delivery driver profile.

Extends the res.users record (via a separate model with user_id FK)
with driver-specific attributes: vehicle info, live location, online
status, and aggregate earnings/rating.
"""
from odoo import api, fields, models
from cargo_base.constants import VEHICLE_TYPES


class CargoDriver(models.Model):
    _name = 'cargo.driver'
    _description = 'Cargo Delivery Driver'
    _rec_name = 'display_name'

    user_id = fields.Many2one(
        'res.users', 'Driver User',
        required=True, ondelete='cascade', index=True,
        domain=[('cargo_role', '=', 'driver')],
    )
    display_name = fields.Char(related='user_id.name', store=True, readonly=True)

    # Vehicle
    vehicle_type  = fields.Selection(VEHICLE_TYPES, 'Vehicle Type', default='scooter')
    vehicle_plate = fields.Char('Plate Number')
    vehicle_color = fields.Char('Vehicle Color')
    vehicle_year  = fields.Integer('Vehicle Year')

    # Live location (updated by the driver app)
    is_online    = fields.Boolean('Online', default=False, index=True)
    current_lat  = fields.Float('Latitude',  digits=(10, 7))
    current_lng  = fields.Float('Longitude', digits=(10, 7))
    location_updated_at = fields.Datetime('Location Updated At')

    # Performance
    rating       = fields.Float('Rating', default=0.0, digits=(3, 1))
    rating_count = fields.Integer('Rating Count', default=0)
    total_deliveries = fields.Integer('Total Deliveries', default=0)
    total_earnings   = fields.Float('Total Earnings (EGP)', digits=(10, 2))

    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('unique_driver_user', 'UNIQUE(user_id)', 'Each user can have only one driver profile.'),
    ]

    def set_online(self, lat=None, lng=None):
        self.ensure_one()
        vals = {'is_online': True, 'location_updated_at': fields.Datetime.now()}
        if lat is not None:
            vals['current_lat'] = lat
        if lng is not None:
            vals['current_lng'] = lng
        self.write(vals)

    def set_offline(self):
        self.write({'is_online': False})

    def to_driver_dict(self):
        self.ensure_one()
        return {
            'id':               self.id,
            'userId':           self.user_id.id,
            'name':             self.display_name,
            'vehicleType':      self.vehicle_type,
            'vehiclePlate':     self.vehicle_plate,
            'isOnline':         self.is_online,
            'lat':              self.current_lat or None,
            'lng':              self.current_lng or None,
            'rating':           self.rating,
            'ratingCount':      self.rating_count,
            'totalDeliveries':  self.total_deliveries,
            'totalEarnings':    self.total_earnings,
        }
