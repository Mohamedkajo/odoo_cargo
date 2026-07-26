# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo.favorite — User-favourited stores and products.

Flutter contract:
  GET  /api/favorites         → { stores: [StoreDict], products: [ProductDict] }
  POST /api/favorites/toggle  → { isFavorite: bool, type: 'store'|'product', id: int }

product_id FK references product.template (the native marketplace product model).
"""
from odoo import api, fields, models
from odoo.addons.cargo_base.constants import FAVORITE_TYPES


class CargoFavorite(models.Model):
    _name = 'cargo.favorite'
    _description = 'Cargo Favourite'
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
    # FK to product.template (native model — replaces removed cargo.product)
    product_id = fields.Many2one(
        'product.template', 'Product',
        ondelete='cascade',
        domain=[('cargo_store_id', '!=', False)],
        help='Marketplace product (product.template with cargo_store_id set).',
    )

    _sql_constraints = [
        ('unique_store_fav',
         'UNIQUE(user_id, store_id)',
         'User can only favourite a store once.'),
        ('unique_product_fav',
         'UNIQUE(user_id, product_id)',
         'User can only favourite a product once.'),
    ]

    @api.model
    def toggle(self, user_id, fav_type, ref_id):
        """
        Toggle favourite for user_id + type + ref_id.
        Returns True if the item is now favourited, False if removed.
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

    def to_favorite_dict(self) -> dict:
        self.ensure_one()
        d = {
            'id':   self.id,
            'type': self.type,
        }
        if self.store_id:
            d['store']   = self.store_id.to_store_dict()
        if self.product_id:
            d['product'] = self.product_id.cargo_to_api_dict()
        return d
