# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo.website.faq.category / cargo.website.faq

Consumed by:
  GET /api/faq
  GET /api/faq/categories
"""
from odoo import fields, models


class CargoWebsiteFaqCategory(models.Model):
    _name        = 'cargo.website.faq.category'
    _description = 'FAQ Category'
    _order       = 'sequence, name'

    name     = fields.Char('Category Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=10)
    icon     = fields.Char('Icon (lucide name)')

    def to_category_dict(self) -> dict:
        self.ensure_one()
        return {
            'id':       self.id,
            'name':     self.name,
            'sequence': self.sequence,
            'icon':     self.icon or '',
        }


class CargoWebsiteFaq(models.Model):
    _name        = 'cargo.website.faq'
    _description = 'FAQ Item'
    _order       = 'category_id, sequence'

    question    = fields.Char('Question', required=True, translate=True)
    answer      = fields.Text('Answer',   required=True, translate=True)
    category_id = fields.Many2one(
        'cargo.website.faq.category', 'Category', ondelete='set null',
    )
    sequence  = fields.Integer('Sequence', default=10)
    is_active = fields.Boolean('Active', default=True)

    def to_faq_dict(self) -> dict:
        self.ensure_one()
        return {
            'id':       self.id,
            'question': self.question,
            'answer':   self.answer,
            'sequence': self.sequence,
            'category': {
                'id':   self.category_id.id,
                'name': self.category_id.name,
            } if self.category_id else None,
        }
