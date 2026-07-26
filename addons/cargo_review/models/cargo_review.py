# -*- coding: utf-8 -*-
"""
cargo.review — Star-rating review for a store or product.

After every write the module recomputes the rating and review_count
on the target record so Flutter home-screen cards always reflect
current aggregate scores.
"""
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CargoReview(models.Model):
    _name = 'cargo.review'
    _description = 'Cargo Review'
    _order = 'create_date desc'
    _rec_name = 'user_id'

    user_id    = fields.Many2one('res.users', 'Reviewer', required=True,
                                  ondelete='cascade', index=True)
    review_type = fields.Selection(
        [('store', 'Store'), ('product', 'Product')],
        'Type', required=True, index=True,
    )
    store_id   = fields.Many2one('cargo.store',   'Store',   ondelete='cascade', index=True)
    product_id = fields.Many2one('cargo.product', 'Product', ondelete='cascade', index=True)

    rating      = fields.Integer('Rating (1–5)', required=True)
    body        = fields.Text('Review Text')
    is_approved = fields.Boolean('Approved', default=True, index=True)

    create_date = fields.Datetime(readonly=True)

    # Computed helpers
    reviewer_name = fields.Char(related='user_id.name', store=True, readonly=True)

    _sql_constraints = [
        ('rating_range', 'CHECK(rating BETWEEN 1 AND 5)', 'Rating must be between 1 and 5.'),
    ]

    @api.constrains('review_type', 'store_id', 'product_id')
    def _check_target(self):
        for r in self:
            if r.review_type == 'store' and not r.store_id:
                raise ValidationError('A store review must reference a store.')
            if r.review_type == 'product' and not r.product_id:
                raise ValidationError('A product review must reference a product.')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._recompute_target_rating()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'rating' in vals or 'is_approved' in vals:
            self._recompute_target_rating()
        return res

    def unlink(self):
        targets = [(r.review_type, r.store_id.id, r.product_id.id) for r in self]
        res = super().unlink()
        for rtype, sid, pid in targets:
            if rtype == 'store' and sid:
                self._update_store_rating(sid)
            elif rtype == 'product' and pid:
                self._update_product_rating(pid)
        return res

    def _recompute_target_rating(self):
        for r in self:
            if r.review_type == 'store' and r.store_id:
                self._update_store_rating(r.store_id.id)
            elif r.review_type == 'product' and r.product_id:
                self._update_product_rating(r.product_id.id)

    def _update_store_rating(self, store_id):
        reviews = self.search([
            ('review_type', '=', 'store'),
            ('store_id', '=', store_id),
            ('is_approved', '=', True),
        ])
        if reviews:
            avg = sum(r.rating for r in reviews) / len(reviews)
            self.env['cargo.store'].sudo().browse(store_id).write({
                'rating': round(avg, 1), 'review_count': len(reviews),
            })

    def _update_product_rating(self, product_id):
        reviews = self.search([
            ('review_type', '=', 'product'),
            ('product_id', '=', product_id),
            ('is_approved', '=', True),
        ])
        if reviews:
            avg = sum(r.rating for r in reviews) / len(reviews)
            self.env['cargo.product'].sudo().browse(product_id).write({
                'rating': round(avg, 1), 'review_count': len(reviews),
            })

    def to_review_dict(self):
        self.ensure_one()
        return {
            'id':           self.id,
            'userId':       self.user_id.id,
            'reviewerName': self.reviewer_name,
            'rating':       self.rating,
            'body':         self.body,
            'createdAt':    self.create_date.isoformat() if self.create_date else None,
        }
