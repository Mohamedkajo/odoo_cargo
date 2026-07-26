# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo.cart and cargo.cart.line — Per-user shopping cart.

Cart lines reference product.template (the marketplace product) so that
one-to-one lookups against cargo_store_id, cargo_is_available and categ_id
work without any joins to a custom model.

When an order is placed, the controller converts each cargo.cart.line into
a sale.order.line (using the first product.product variant of the template).

Flutter contract (GET /api/cart):
  { id, items, storeId, storeName, subtotal, deliveryFee, discount, total, couponCode }

Each CartItem:
  { id, productId, name, price, quantity, image, storeId, storeName }
"""
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class CargoCart(models.Model):
    _name = 'cargo.cart'
    _description = 'Cargo Shopping Cart'
    _rec_name = 'user_id'

    user_id = fields.Many2one(
        'res.users', 'Customer',
        required=True, ondelete='cascade', index=True,
        help='One active cart per user.',
    )
    store_id = fields.Many2one('cargo.store', 'Store', ondelete='set null')
    store_name  = fields.Char('Store Name')
    delivery_fee = fields.Float('Delivery Fee (EGP)', default=15.0, digits=(10, 2))
    discount     = fields.Float('Discount (EGP)',     default=0.0,  digits=(10, 2))
    coupon_code  = fields.Char('Coupon Code')

    line_ids = fields.One2many('cargo.cart.line', 'cart_id', string='Cart Items')

    subtotal = fields.Float('Subtotal', compute='_compute_totals', store=False, digits=(10, 2))
    total    = fields.Float('Total',    compute='_compute_totals', store=False, digits=(10, 2))

    _sql_constraints = [
        ('unique_user_cart', 'UNIQUE(user_id)', 'Each user may have only one active cart.'),
    ]

    @api.depends('line_ids.price', 'line_ids.quantity', 'delivery_fee', 'discount')
    def _compute_totals(self):
        for cart in self:
            subtotal      = sum(l.price * l.quantity for l in cart.line_ids)
            cart.subtotal = subtotal
            cart.total    = subtotal + (cart.delivery_fee or 0) - (cart.discount or 0)

    @api.model
    def get_or_create_for_user(self, user_id):
        """Return the cart for user_id, creating one if it doesn't exist."""
        cart = self.sudo().search([('user_id', '=', user_id)], limit=1)
        if not cart:
            cart = self.sudo().create({'user_id': user_id, 'delivery_fee': 15.0})
        return cart

    def to_cart_dict(self) -> dict:
        self.ensure_one()
        lines    = [l.to_line_dict() for l in self.line_ids]
        subtotal = sum(l['price'] * l['quantity'] for l in lines)
        total    = subtotal + (self.delivery_fee or 0) - (self.discount or 0)
        return {
            'id':          self.id,
            'items':       lines,
            'storeId':     self.store_id.id if self.store_id else None,
            'storeName':   self.store_name or (self.store_id.name if self.store_id else None),
            'subtotal':    subtotal,
            'deliveryFee': self.delivery_fee or 0.0,
            'discount':    self.discount or 0.0,
            'total':       total,
            'couponCode':  self.coupon_code or None,
        }

    def clear(self):
        """Remove all lines and reset store/coupon."""
        self.ensure_one()
        self.line_ids.unlink()
        self.write({
            'store_id':   False,
            'store_name': False,
            'discount':   0.0,
            'coupon_code': False,
        })


class CargoCartLine(models.Model):
    _name = 'cargo.cart.line'
    _description = 'Cargo Cart Line Item'
    _order = 'id'

    cart_id = fields.Many2one(
        'cargo.cart', 'Cart',
        required=True, ondelete='cascade', index=True,
    )
    # product.template (the marketplace product — one template per menu item)
    product_id = fields.Many2one(
        'product.template', 'Product',
        ondelete='cascade', required=True,
        domain=[('cargo_store_id', '!=', False)],
    )
    name  = fields.Char('Product Name', required=True)
    image = fields.Char('Image URL',
                        help='Cached from product.template.cargo_image_url at add-to-cart time.')
    price    = fields.Float('Unit Price (EGP)', required=True, digits=(10, 2))
    quantity = fields.Integer('Quantity', default=1)
    store_id   = fields.Many2one('cargo.store', 'Store', ondelete='set null')
    store_name = fields.Char('Store Name')
    variant    = fields.Char('Variant (JSON)')
    special_instructions = fields.Char('Special Instructions')

    def to_line_dict(self) -> dict:
        self.ensure_one()
        return {
            'id':        self.id,
            'productId': self.product_id.id if self.product_id else None,
            'name':      self.name or '',
            'price':     self.price,
            'quantity':  self.quantity,
            'image':     self.image or None,
            'storeId':   self.store_id.id if self.store_id else None,
            'storeName': self.store_name or None,
        }
