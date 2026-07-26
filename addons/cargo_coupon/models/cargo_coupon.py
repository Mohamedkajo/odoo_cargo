# -*- coding: utf-8 -*-
"""cargo.coupon — Promotional coupon codes."""
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CargoCoupon(models.Model):
    _name = 'cargo.coupon'
    _description = 'Cargo Coupon'
    _rec_name = 'code'

    code  = fields.Char('Coupon Code', required=True, index=True)
    type  = fields.Selection(
        [('percentage', 'Percentage'), ('fixed', 'Fixed Amount')],
        'Discount Type', required=True, default='percentage',
    )
    discount_value   = fields.Float('Discount Value',      required=True, digits=(8, 2))
    max_discount     = fields.Float('Max Discount (EGP)', digits=(8, 2),
                                     help='Cap for percentage discounts. 0 = no cap.')
    min_order_amount = fields.Float('Min Order Amount (EGP)', digits=(8, 2), default=0.0)
    usage_limit      = fields.Integer('Usage Limit', default=0,
                                       help='Total uses allowed across all users. 0 = unlimited.')
    used_count       = fields.Integer('Times Used', default=0, readonly=True)
    per_user_limit   = fields.Integer('Per-User Limit', default=1)

    valid_from = fields.Datetime('Valid From')
    valid_to   = fields.Datetime('Valid To')
    is_active  = fields.Boolean('Active', default=True, index=True)

    # Optional: restrict to a specific store
    store_id = fields.Many2one('cargo.store', 'Restrict to Store', ondelete='set null')

    usage_ids = fields.One2many('cargo.coupon.usage', 'coupon_id', 'Usage Log')

    _sql_constraints = [
        ('unique_code', 'UNIQUE(code)', 'Coupon codes must be unique.'),
    ]

    @api.constrains('discount_value')
    def _check_discount_value(self):
        for c in self:
            if c.discount_value <= 0:
                raise ValidationError('Discount value must be greater than zero.')
            if c.type == 'percentage' and c.discount_value > 100:
                raise ValidationError('Percentage discount cannot exceed 100%.')

    def validate_for_cart(self, user_id, cart_subtotal, store_id=None):
        """
        Validate this coupon for a given user and cart subtotal.

        Returns {'valid': True, 'discountAmount': X} or
                {'valid': False, 'reason': '...'}.
        """
        self.ensure_one()
        now = fields.Datetime.now()

        if not self.is_active:
            return {'valid': False, 'reason': 'Coupon is no longer active.'}
        if self.valid_from and now < self.valid_from:
            return {'valid': False, 'reason': 'Coupon is not yet valid.'}
        if self.valid_to and now > self.valid_to:
            return {'valid': False, 'reason': 'Coupon has expired.'}
        if self.usage_limit and self.used_count >= self.usage_limit:
            return {'valid': False, 'reason': 'Coupon usage limit reached.'}
        if cart_subtotal < self.min_order_amount:
            return {'valid': False, 'reason': f'Minimum order of EGP {self.min_order_amount:.0f} required.'}
        if self.store_id and store_id and self.store_id.id != store_id:
            return {'valid': False, 'reason': 'Coupon is not valid for this store.'}

        # Per-user limit check
        if self.per_user_limit:
            user_uses = self.env['cargo.coupon.usage'].sudo().search_count(
                [('coupon_id', '=', self.id), ('user_id', '=', user_id)]
            )
            if user_uses >= self.per_user_limit:
                return {'valid': False, 'reason': 'You have already used this coupon.'}

        # Calculate discount
        if self.type == 'percentage':
            discount = cart_subtotal * self.discount_value / 100
            if self.max_discount:
                discount = min(discount, self.max_discount)
        else:
            discount = min(self.discount_value, cart_subtotal)

        return {'valid': True, 'discountAmount': round(discount, 2)}

    def redeem(self, user_id):
        """Record a redemption."""
        self.ensure_one()
        self.env['cargo.coupon.usage'].sudo().create({
            'coupon_id': self.id, 'user_id': user_id,
        })
        self.sudo().write({'used_count': self.used_count + 1})


class CargoCouponUsage(models.Model):
    _name = 'cargo.coupon.usage'
    _description = 'Cargo Coupon Usage'
    _rec_name = 'coupon_id'

    coupon_id  = fields.Many2one('cargo.coupon', required=True, ondelete='cascade', index=True)
    user_id    = fields.Many2one('res.users',    required=True, ondelete='cascade', index=True)
    used_at    = fields.Datetime(default=fields.Datetime.now, readonly=True)
    order_id   = fields.Many2one('cargo.order', ondelete='set null')
