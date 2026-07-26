# -*- coding: utf-8 -*-
"""
cargo.delivery.zone — Geographic delivery zone.

Zones define coverage areas (identified by city name), delivery fees,
and minimum order thresholds. Stores are associated with zones via m2m.

Coordinate matching is done via a simple bounding-box + Haversine helper
(no PostGIS required).
"""
import math

from odoo import fields, models


def _haversine(lat1, lng1, lat2, lng2):
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlng / 2) ** 2)
    return 6371 * 2 * math.asin(math.sqrt(a))


class CargoDeliveryZone(models.Model):
    _name = 'cargo.delivery.zone'
    _description = 'Cargo Delivery Zone'
    _rec_name = 'name'
    _order = 'name'

    name              = fields.Char('Zone Name', required=True)
    city              = fields.Char('City',      required=True)
    base_delivery_fee = fields.Float('Base Delivery Fee (EGP)', default=15.0, digits=(8, 2))
    min_order_amount  = fields.Float('Min Order Amount (EGP)', default=50.0, digits=(8, 2))
    max_radius_km     = fields.Float('Coverage Radius (km)', default=10.0, digits=(6, 1),
                                      help='Approx radius from zone centre for geo-check.')
    center_lat        = fields.Float('Centre Latitude',  digits=(10, 7))
    center_lng        = fields.Float('Centre Longitude', digits=(10, 7))
    is_active         = fields.Boolean('Active', default=True, index=True)
    notes             = fields.Text('Notes')

    store_ids = fields.Many2many(
        'cargo.store',
        'cargo_store_zone_rel', 'zone_id', 'store_id',
        string='Stores in Zone',
    )

    def covers_coordinates(self, lat, lng):
        """Return True if (lat, lng) falls within this zone's radius."""
        self.ensure_one()
        if not (self.center_lat and self.center_lng):
            return True  # zone has no coordinates — assume it covers everywhere
        dist = _haversine(self.center_lat, self.center_lng, lat, lng)
        return dist <= self.max_radius_km

    @classmethod
    def find_for_coordinates(cls, env, lat, lng):
        """Return the first active zone that covers (lat, lng)."""
        zones = env['cargo.delivery.zone'].sudo().search([('is_active', '=', True)])
        for zone in zones:
            if zone.covers_coordinates(lat, lng):
                return zone
        return env['cargo.delivery.zone'].sudo().browse([])

    def to_zone_dict(self):
        self.ensure_one()
        return {
            'id':              self.id,
            'name':            self.name,
            'city':            self.city,
            'baseDeliveryFee': self.base_delivery_fee,
            'minOrderAmount':  self.min_order_amount,
            'isActive':        self.is_active,
        }
