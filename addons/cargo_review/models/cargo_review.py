# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo.review — Customer reviews for stores and products.

FKs use native Odoo models:
  product_id → product.template  (marketplace product)
  order_id   → sale.order        (the order being reviewed)

After a review is saved, rating aggregates are refreshed on the target
(store or product.template).
"""
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

REVIEW_TYPES = [
    ('store',   'Store Review'),
    ('product', 'Product Review'),
]


class CargoReview(models.Model):
    _name = 'cargo.review'
    _description = 'Cargo Review'
    _order = 'create_date desc'

    # ── Who and what ──────────────────────────────────────────────────────────
    user_id = fields.Many2one(
        'res.users', 'Reviewer',
        required=True, ondelete='cascade', index=True,
    )
    review_type = fields.Selection(REVIEW_TYPES, 'Type', required=True, index=True)

    store_id = fields.Many2one(
        'cargo.store', 'Store',
        ondelete='set null', index=True,
        help='Store being reviewed (review_type="store").',
    )
    product_id = fields.Many2one(
        'product.template', 'Product',
        ondelete='set null', index=True,
        domain=[('cargo_store_id', '!=', False)],
        help='product.template being reviewed (review_type="product").',
    )
    order_id = fields.Many2one(
        'sale.order', 'Order',
        ondelete='set null', index=True,
        domain=[('cargo_status', '!=', False)],
        help='The sale.order that prompted this review.',
    )

    # ── Content ───────────────────────────────────────────────────────────────
    rating  = fields.Integer('Rating (1–5)', required=True)
    comment = fields.Text('Comment')
    images  = fields.Char('Image URLs (JSON)')

    # ── Moderation ────────────────────────────────────────────────────────────
    is_approved  = fields.Boolean('Approved', default=True, index=True)
    approved_at  = fields.Datetime('Approved At')
    is_anonymous = fields.Boolean('Anonymous', default=False)

    # ── Denormalised reviewer info ────────────────────────────────────────────
    reviewer_name   = fields.Char(related='user_id.name',           store=True, readonly=True)
    reviewer_avatar = fields.Char('Reviewer Avatar URL')

    _sql_constraints = [
        ('rating_range',
         'CHECK(rating BETWEEN 1 AND 5)',
         'Rating must be between 1 and 5.'),
    ]

    # ── ORM hooks ─────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._refresh_target_ratings()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'rating' in vals or 'is_approved' in vals:
            self._refresh_target_ratings()
        return res

    def unlink(self):
        targets = self._get_targets()
        res = super().unlink()
        for target in targets:
            if target.exists():
                target._refresh_cargo_rating()
        return res

    def _get_targets(self):
        targets = []
        for review in self:
            if review.store_id:
                targets.append(review.store_id)
            if review.product_id:
                targets.append(review.product_id)
        return targets

    def _refresh_target_ratings(self):
        """Recompute rating averages on touched stores and products."""
        for review in self.filtered('is_approved'):
            if review.store_id:
                review.store_id._refresh_cargo_rating()
            if review.product_id:
                review.product_id._refresh_cargo_rating()

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_review_dict(self) -> dict:
        import json as _json
        self.ensure_one()
        try:
            images = _json.loads(self.images or '[]')
        except Exception:
            images = []
        return {
            'id':           self.id,
            'reviewType':   self.review_type,
            'storeId':      self.store_id.id if self.store_id else None,
            'productId':    self.product_id.id if self.product_id else None,
            'orderId':      self.order_id.id if self.order_id else None,
            'rating':       self.rating,
            'comment':      self.comment or '',
            'images':       images,
            'reviewerName': None if self.is_anonymous else (self.reviewer_name or ''),
            'createdAt':    self.create_date.isoformat() if self.create_date else None,
        }


class CargoRatingMixin(models.AbstractModel):
    """
    Mixin for models that aggregate cargo reviews.

    Add _inherit = 'cargo.rating.mixin' and provide a _cargo_review_field
    class attribute pointing to the review FK field name.
    """
    _name = 'cargo.rating.mixin'
    _description = 'Cargo Rating Mixin'

    def _refresh_cargo_rating(self):
        """
        Refresh cargo_rating / cargo_review_count from approved reviews.

        Subclasses must define _cargo_review_field (e.g. 'store_id' or 'product_id').
        """
        field = getattr(self, '_cargo_review_field', None)
        if not field:
            return
        for rec in self:
            reviews = self.env['cargo.review'].sudo().search([
                (field, '=', rec.id),
                ('is_approved', '=', True),
            ])
            count  = len(reviews)
            avg    = sum(r.rating for r in reviews) / count if count else 0.0
            rec.write({
                'cargo_rating':       round(avg, 1),
                'cargo_review_count': count,
            })
