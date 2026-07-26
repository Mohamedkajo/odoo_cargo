# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo.website.blog.category / cargo.website.blog.post

Consumed by:
  GET /api/blog/categories
  GET /api/blog
  GET /api/blog/:slug
"""
import re
from odoo import api, fields, models


def _slugify(text: str) -> str:
    """Simple slug: lowercase, replace non-alnum with dash, collapse dashes."""
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[\s_-]+', '-', slug).strip('-')
    return slug


class CargoWebsiteBlogCategory(models.Model):
    _name        = 'cargo.website.blog.category'
    _description = 'Blog Category'
    _order       = 'name'

    name = fields.Char('Category Name', required=True, translate=True)
    slug = fields.Char('Slug', compute='_compute_slug', store=True, readonly=False)
    icon = fields.Char('Icon (lucide name)', help='e.g. "tag", "package", "star"')

    @api.depends('name')
    def _compute_slug(self):
        for rec in self:
            if not rec.slug and rec.name:
                rec.slug = _slugify(rec.name)

    def to_category_dict(self) -> dict:
        self.ensure_one()
        return {
            'id':   self.id,
            'name': self.name,
            'slug': self.slug or _slugify(self.name),
            'icon': self.icon or '',
        }


class CargoWebsiteBlogPost(models.Model):
    _name        = 'cargo.website.blog.post'
    _description = 'Blog Post'
    _order       = 'published_date desc, id desc'
    _rec_name    = 'title'

    title       = fields.Char('Title', required=True)
    slug        = fields.Char('Slug', required=True, index=True, copy=False)
    summary     = fields.Text('Summary / Excerpt')
    content     = fields.Html('Content', sanitize=True)
    image_url   = fields.Char('Cover Image URL')
    read_time   = fields.Integer('Read Time (min)', default=5)

    category_id = fields.Many2one(
        'cargo.website.blog.category', 'Category', ondelete='set null',
    )
    author_id = fields.Many2one(
        'res.users', 'Author', default=lambda self: self.env.user, ondelete='set null',
    )
    author_name = fields.Char(
        related='author_id.name', store=True, readonly=True, translate=False,
    )

    is_published   = fields.Boolean('Published', default=False, index=True)
    published_date = fields.Date('Publish Date')
    is_featured    = fields.Boolean('Featured / Hero Post', default=False)

    # ── SEO ───────────────────────────────────────────────────────────────────
    meta_title       = fields.Char('Meta Title')
    meta_description = fields.Char('Meta Description')

    _sql_constraints = [
        ('unique_slug', 'UNIQUE(slug)', 'Blog slug must be unique.'),
    ]

    def action_toggle_published(self):
        for rec in self:
            rec.is_published = not rec.is_published
            if rec.is_published and not rec.published_date:
                rec.published_date = fields.Date.today()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('slug') and vals.get('title'):
                vals['slug'] = _slugify(vals['title'])
        return super().create(vals_list)

    def to_post_dict(self, full=False) -> dict:
        self.ensure_one()
        d = {
            'id':            self.id,
            'title':         self.title,
            'slug':          self.slug,
            'summary':       self.summary or '',
            'imageUrl':      self.image_url or '',
            'readTime':      self.read_time,
            'publishedDate': str(self.published_date) if self.published_date else None,
            'isFeatured':    self.is_featured,
            'author': {
                'id':   self.author_id.id,
                'name': self.author_name or '',
            } if self.author_id else None,
            'category': {
                'id':   self.category_id.id,
                'name': self.category_id.name,
                'slug': self.category_id.slug or '',
            } if self.category_id else None,
            'seo': {
                'title':       self.meta_title or self.title,
                'description': self.meta_description or self.summary or '',
            },
        }
        if full:
            d['content'] = self.content or ''
        return d
