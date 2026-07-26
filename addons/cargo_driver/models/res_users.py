# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
res.users extension — Cargo driver profile fields.

cargo_base already adds cargo_role, cargo_device_token, cargo_unread_count.

This module adds the driver-specific fields that are only relevant when
cargo_role = 'driver':  vehicle info, live GPS position, online/offline
status, and aggregate performance metrics.

All fields are prefixed with cargo_driver_ to avoid clashes with native
Odoo user fields and to make their purpose immediately obvious in code.

Using _inherit = 'res.users' (rather than a separate cargo.driver profile
model) is the "Native Odoo First" approach:
  • No data duplication — a driver IS a res.users record
  • Odoo's permission system governs all access
  • Driver app authenticates through the same JWT flow as customers
  • cargo_role discriminator keeps queries efficient

Filtering drivers:
  self.env['res.users'].search([('cargo_role', '=', 'driver')])
"""
from odoo import api, fields, models
from cargo_base.constants import VEHICLE_TYPES


class CargoDriverUser(models.Model):
    """Extend res.users with delivery driver profile."""

    _inherit = 'res.users'

    # ── Vehicle ───────────────────────────────────────────────────────────────
    cargo_driver_vehicle_type = fields.Selection(
        selection=VEHICLE_TYPES,
        string='Vehicle Type',
        default='scooter',
    )
    cargo_driver_vehicle_plate = fields.Char('Plate Number')
    cargo_driver_vehicle_color = fields.Char('Vehicle Color')
    cargo_driver_vehicle_year  = fields.Integer('Vehicle Year')

    # ── Live location (updated by the driver app on each GPS event) ───────────
    cargo_driver_is_online = fields.Boolean(
        string='Online',
        default=False,
        index=True,
        help='True while the driver is accepting orders.',
    )
    cargo_driver_current_lat = fields.Float('Latitude',  digits=(10, 7))
    cargo_driver_current_lng = fields.Float('Longitude', digits=(10, 7))
    cargo_driver_location_at = fields.Datetime(
        'Location Updated At',
        help='Timestamp of the last GPS ping from the driver app.',
    )

    # ── Performance metrics (updated by cargo_delivery on order completion) ───
    cargo_driver_rating         = fields.Float('Rating',      digits=(3, 1), default=0.0)
    cargo_driver_rating_count   = fields.Integer('Ratings',   default=0)
    cargo_driver_total_deliveries = fields.Integer('Deliveries', default=0)
    cargo_driver_total_earnings   = fields.Float('Earnings (EGP)', digits=(10, 2), default=0.0)

    # ── Defaults override (expose driver fields as SELF_READABLE) ─────────────
    SELF_READABLE_FIELDS = models.Model.SELF_READABLE_FIELDS | {
        'cargo_driver_vehicle_type',
        'cargo_driver_vehicle_plate',
        'cargo_driver_vehicle_color',
        'cargo_driver_vehicle_year',
        'cargo_driver_is_online',
        'cargo_driver_current_lat',
        'cargo_driver_current_lng',
        'cargo_driver_location_at',
        'cargo_driver_rating',
        'cargo_driver_rating_count',
        'cargo_driver_total_deliveries',
        'cargo_driver_total_earnings',
    }

    SELF_WRITEABLE_FIELDS = models.Model.SELF_WRITEABLE_FIELDS | {
        'cargo_driver_vehicle_type',
        'cargo_driver_vehicle_plate',
        'cargo_driver_vehicle_color',
        'cargo_driver_vehicle_year',
    }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def cargo_driver_go_online(self, lat=None, lng=None):
        """Mark driver as online and optionally update GPS position."""
        vals = {
            'cargo_driver_is_online': True,
            'cargo_driver_location_at': fields.Datetime.now(),
        }
        if lat is not None:
            vals['cargo_driver_current_lat'] = lat
        if lng is not None:
            vals['cargo_driver_current_lng'] = lng
        self.write(vals)

    def cargo_driver_go_offline(self):
        """Mark driver as offline."""
        self.write({'cargo_driver_is_online': False})

    def cargo_driver_update_location(self, lat, lng):
        """Update GPS coordinates from a real-time ping."""
        self.write({
            'cargo_driver_current_lat': lat,
            'cargo_driver_current_lng': lng,
            'cargo_driver_location_at': fields.Datetime.now(),
        })

    def cargo_driver_to_api_dict(self) -> dict:
        """Return driver profile dict for REST API responses."""
        self.ensure_one()
        return {
            'id':               self.id,
            'name':             self.name,
            'phone':            self.partner_id.phone,
            'vehicleType':      self.cargo_driver_vehicle_type,
            'vehiclePlate':     self.cargo_driver_vehicle_plate,
            'vehicleColor':     self.cargo_driver_vehicle_color,
            'isOnline':         self.cargo_driver_is_online,
            'lat':              self.cargo_driver_current_lat or None,
            'lng':              self.cargo_driver_current_lng or None,
            'rating':           self.cargo_driver_rating,
            'ratingCount':      self.cargo_driver_rating_count,
            'totalDeliveries':  self.cargo_driver_total_deliveries,
            'totalEarnings':    self.cargo_driver_total_earnings,
        }
