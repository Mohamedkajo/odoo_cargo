# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
REMOVED: cargo.order and cargo.order.line custom models.

These models were removed as part of the Native Odoo First refactoring.
sale.order (extended by cargo_base with cargo_status and by this module with
delivery address, payment method, discount and coupon fields) IS the Cargo order.

Key field mapping (old → new):
  cargo.order.user_id           → sale.order.partner_id          (customer)
  cargo.order.store_id (Int)    → sale.order.cargo_store_id      (Many2one cargo.store)
  cargo.order.driver_id (Int)   → sale.order.cargo_driver_id     (Integer, res.users id)
  cargo.order.status            → sale.order.cargo_status        (Selection — cargo_base)
  cargo.order.delivery_fee      → sale.order.cargo_delivery_fee  (Monetary — cargo_base)
  cargo.order.delivery_address  → sale.order.cargo_delivery_address
  cargo.order.payment_method    → sale.order.cargo_payment_method
  cargo.order.coupon_code       → sale.order.cargo_coupon_code
  cargo.order.discount          → sale.order.cargo_discount
  cargo.order.total             → sale.order.amount_total        (native)

  cargo.order.line.product_id   → sale.order.line.product_id     (product.product)
  cargo.order.line.quantity     → sale.order.line.product_uom_qty
  cargo.order.line.price        → sale.order.line.price_unit

See models/sale_order.py in this module.
This file is kept as a tombstone to aid git blame readability.
Do not re-add any model definitions here.
"""
