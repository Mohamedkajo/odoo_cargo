# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
REMOVED: cargo.vendor custom model.

The cargo.vendor model was removed as part of the Native Odoo First refactoring.
Vendor fields are now on res.partner (the native Odoo partner linked to each user):
  * res.partner.cargo_vendor_business_name
  * res.partner.cargo_vendor_tax_number
  * res.partner.cargo_vendor_bank_account
  * res.partner.cargo_vendor_commission_rate
  * res.partner.cargo_vendor_is_approved
  * res.partner.cargo_vendor_approve() / cargo_vendor_reject()

See models/res_partner.py in this module.
This file is kept as a tombstone to aid git blame readability.
Do not re-add any model definitions here.
"""
