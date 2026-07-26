# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
REMOVED: cargo.driver custom model.

The cargo.driver model was removed as part of the Native Odoo First refactoring.
Driver fields are now on res.users directly:
  * res.users.cargo_driver_vehicle_type / plate / color / year
  * res.users.cargo_driver_is_online
  * res.users.cargo_driver_current_lat / current_lng / location_at
  * res.users.cargo_driver_rating / rating_count
  * res.users.cargo_driver_total_deliveries / total_earnings
  * res.users.cargo_driver_go_online() / go_offline() / update_location()

Filter drivers via:  env['res.users'].search([('cargo_role', '=', 'driver')])

See models/res_users.py in this module.
This file is kept as a tombstone to aid git blame readability.
Do not re-add any model definitions here.
"""
