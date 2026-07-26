# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo.favorite — User-favorited stores and products.

Flutter contract:
  GET /api/favorites → { stores: [StoreDict], products: [ProductDict] }
  POST /api/favorites/toggle → { isFavorite: bool, type: 'store'|'product', id: int }
"""
from odoo import api, fields, models
from cargo_base.constants import FAVORITE_TYPES


class CargoFavorite(models.Model):
    _name = 'cargo.favorite'
    _description = 'Cargo Favorite'
    _rec_name = 'user_id'
    _order = 'id desc'

    user_id = fields.Many2one(
        'res.users', 'User',
        required=True, ondelete='cascade', index=True,
    )
    type = fields.Selection(
        FAVORITE_TYPES,
        string='Type',
        required=True,
        index=True,
    )
    store_id = fields.Many2one(
        'cargo.store', 'Store',
        ondelete='cascade',
    )
    product_id = fields.Many2one(
        'cargo.product', 'Product',
        ondelete='cascade',
    )

    _sql_constraints = [
        ('unique_store_fav',
         'UNIQUE(user_id, store_id)',
         'User can only favorite a store once.'),
        ('unique_product_fav',
         'UNIQUE(user_id, product_id)',
         'User can only favorite a product once.'),
    ]

    @api.model
    def toggle(self, user_id, fav_type, ref_id):
        """
        Toggle the favorite for user_id+type+ref_id.
        Returns (is_favorite_now: bool).
        """
        domain = [('user_id', '=', user_id), ('type', '=', fav_type)]
        if fav_type == 'store':
            domain.append(('store_id', '=', ref_id))
        else:
            domain.append(('product_id', '=', ref_id))

        existing = self.sudo().search(domain, limit=1)
        if existing:
            existing.unlink()
            return False
        else:
            vals = {'user_id': user_id, 'type': fav_type}
            if fav_type == 'store':
                vals['store_id'] = ref_id
            else:
                vals['product_id'] = ref_id
            self.sudo().create(vals)
            return True
