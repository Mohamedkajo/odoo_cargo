# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
CargoWebsiteController — Public JSON APIs consumed by the React company website.

Routes:
  GET  /api/website/config       platform config + active banners
  GET  /api/flash-sales          active flash sale campaigns
  GET  /api/coupons              public active coupons
  GET  /api/blog                 published blog posts (paginated, filterable)
  GET  /api/blog/categories      blog categories
  GET  /api/blog/<slug>          single blog post by slug
  GET  /api/faq                  active FAQ items (filterable by category)
  GET  /api/faq/categories       FAQ categories
  GET  /api/careers              active job listings (filterable by department)
  POST /api/contact              submit contact form

All routes are public (auth='none').  No JWT required — this is the public
company website, not the authenticated Flutter app.
"""
import json
import logging
from datetime import date, datetime

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


def _ok(data, status=200):
    return request.make_response(
        json.dumps(data, default=str),
        status=status,
        headers=[('Content-Type', 'application/json'),
                 ('Access-Control-Allow-Origin', '*')],
    )


def _err(message, status=400, code='BAD_REQUEST'):
    return request.make_response(
        json.dumps({'success': False, 'error': code, 'message': message}),
        status=status,
        headers=[('Content-Type', 'application/json'),
                 ('Access-Control-Allow-Origin', '*')],
    )


def _page_args(default_limit=20):
    try:
        limit  = max(1, min(int(request.httprequest.args.get('limit',  default_limit)), 100))
        offset = max(0, int(request.httprequest.args.get('offset', 0)))
    except (TypeError, ValueError):
        limit, offset = default_limit, 0
    return limit, offset


class CargoWebsiteController(http.Controller):

    # ── Website config ────────────────────────────────────────────────────────

    @http.route('/api/website/config', auth='none', methods=['GET'],
                type='http', csrf=False)
    def website_config(self, **_kw):
        """Return platform config and active banners."""
        try:
            env = request.env(user=1)  # sudo

            config = env['cargo.website.config'].search([], limit=1)
            config_dict = config.to_config_dict() if config else {}

            today = date.today()
            domain = [
                ('is_active', '=', True),
                '|', ('valid_from',  '=', False), ('valid_from',  '<=', today),
                '|', ('valid_until', '=', False), ('valid_until', '>=', today),
            ]
            banners = env['cargo.website.banner'].search(domain)
            config_dict['banners'] = [b.to_banner_dict() for b in banners]

            return _ok({'success': True, 'data': config_dict})
        except Exception as exc:
            _logger.exception('website_config error: %s', exc)
            return _err('Server error', 500, 'SERVER_ERROR')

    # ── Flash sales ───────────────────────────────────────────────────────────

    @http.route('/api/flash-sales', auth='none', methods=['GET'],
                type='http', csrf=False)
    def flash_sales(self, **_kw):
        """Return currently active flash sale campaigns."""
        try:
            env = request.env(user=1)
            now = datetime.utcnow()
            domain = [
                ('is_active', '=', True),
                '|', ('valid_from',  '=', False), ('valid_from',  '<=', now),
                ('valid_until', '>=', now),
            ]
            sales = env['cargo.website.flash.sale'].search(domain)
            return _ok({'success': True, 'data': [s.to_flash_sale_dict() for s in sales]})
        except Exception as exc:
            _logger.exception('flash_sales error: %s', exc)
            return _err('Server error', 500, 'SERVER_ERROR')

    # ── Public coupons ────────────────────────────────────────────────────────

    @http.route('/api/coupons', auth='none', methods=['GET'],
                type='http', csrf=False)
    def public_coupons(self, **_kw):
        """Return active, non-expired coupons for display on the website."""
        try:
            env = request.env(user=1)
            today = date.today()
            domain = [
                ('is_active', '=', True),
                '|', ('valid_until', '=', False), ('valid_until', '>=', today),
            ]
            coupons = env['cargo.coupon'].search(domain, limit=50)
            data = [c.to_coupon_dict() for c in coupons]
            return _ok({'success': True, 'data': data})
        except Exception as exc:
            _logger.exception('public_coupons error: %s', exc)
            return _err('Server error', 500, 'SERVER_ERROR')

    # ── Blog categories ───────────────────────────────────────────────────────

    @http.route('/api/blog/categories', auth='none', methods=['GET'],
                type='http', csrf=False)
    def blog_categories(self, **_kw):
        try:
            env = request.env(user=1)
            cats = env['cargo.website.blog.category'].search([])
            return _ok({'success': True, 'data': [c.to_category_dict() for c in cats]})
        except Exception as exc:
            _logger.exception('blog_categories error: %s', exc)
            return _err('Server error', 500, 'SERVER_ERROR')

    # ── Blog post list ────────────────────────────────────────────────────────

    @http.route('/api/blog', auth='none', methods=['GET'],
                type='http', csrf=False)
    def blog_list(self, **_kw):
        """
        Query params:
          category  — category slug or id
          featured  — 'true' to return only featured/hero posts
          limit, offset
        """
        try:
            env    = request.env(user=1)
            limit, offset = _page_args(12)
            args   = request.httprequest.args

            domain = [('is_published', '=', True)]

            category_filter = args.get('category')
            if category_filter:
                cat = env['cargo.website.blog.category'].search(
                    ['|', ('slug', '=', category_filter),
                          ('id',   '=', category_filter)], limit=1)
                if cat:
                    domain.append(('category_id', '=', cat.id))

            if args.get('featured', '').lower() == 'true':
                domain.append(('is_featured', '=', True))

            total  = env['cargo.website.blog.post'].search_count(domain)
            posts  = env['cargo.website.blog.post'].search(domain, limit=limit, offset=offset)

            return _ok({
                'success': True,
                'data': [p.to_post_dict(full=False) for p in posts],
                'pagination': {
                    'total':   total,
                    'limit':   limit,
                    'offset':  offset,
                    'hasNext': offset + limit < total,
                },
            })
        except Exception as exc:
            _logger.exception('blog_list error: %s', exc)
            return _err('Server error', 500, 'SERVER_ERROR')

    # ── Blog post detail ──────────────────────────────────────────────────────

    @http.route('/api/blog/<string:slug>', auth='none', methods=['GET'],
                type='http', csrf=False)
    def blog_detail(self, slug, **_kw):
        try:
            env  = request.env(user=1)
            post = env['cargo.website.blog.post'].search(
                [('slug', '=', slug), ('is_published', '=', True)], limit=1)
            if not post:
                return _err('Post not found', 404, 'NOT_FOUND')
            return _ok({'success': True, 'data': post.to_post_dict(full=True)})
        except Exception as exc:
            _logger.exception('blog_detail error: %s', exc)
            return _err('Server error', 500, 'SERVER_ERROR')

    # ── FAQ categories ────────────────────────────────────────────────────────

    @http.route('/api/faq/categories', auth='none', methods=['GET'],
                type='http', csrf=False)
    def faq_categories(self, **_kw):
        try:
            env  = request.env(user=1)
            cats = env['cargo.website.faq.category'].search([])
            return _ok({'success': True, 'data': [c.to_category_dict() for c in cats]})
        except Exception as exc:
            _logger.exception('faq_categories error: %s', exc)
            return _err('Server error', 500, 'SERVER_ERROR')

    # ── FAQ list ──────────────────────────────────────────────────────────────

    @http.route('/api/faq', auth='none', methods=['GET'],
                type='http', csrf=False)
    def faq_list(self, **_kw):
        """
        Query params:
          category — category id to filter
          q        — search term (searches question text)
        """
        try:
            env    = request.env(user=1)
            args   = request.httprequest.args
            domain = [('is_active', '=', True)]

            cat_id = args.get('category')
            if cat_id:
                try:
                    domain.append(('category_id', '=', int(cat_id)))
                except (TypeError, ValueError):
                    pass

            q = args.get('q', '').strip()
            if q:
                domain.append(('question', 'ilike', q))

            faqs = env['cargo.website.faq'].search(domain)
            return _ok({'success': True, 'data': [f.to_faq_dict() for f in faqs]})
        except Exception as exc:
            _logger.exception('faq_list error: %s', exc)
            return _err('Server error', 500, 'SERVER_ERROR')

    # ── Careers ───────────────────────────────────────────────────────────────

    @http.route('/api/careers', auth='none', methods=['GET'],
                type='http', csrf=False)
    def careers(self, **_kw):
        """
        Query params:
          department — filter by department name
        """
        try:
            env    = request.env(user=1)
            args   = request.httprequest.args
            domain = [('is_active', '=', True)]

            dept = args.get('department', '').strip()
            if dept:
                domain.append(('department', 'ilike', dept))

            jobs = env['cargo.website.job'].search(domain)
            return _ok({'success': True, 'data': [j.to_job_dict() for j in jobs]})
        except Exception as exc:
            _logger.exception('careers error: %s', exc)
            return _err('Server error', 500, 'SERVER_ERROR')

    # ── Contact form ──────────────────────────────────────────────────────────

    @http.route('/api/contact', auth='none', methods=['POST'],
                type='http', csrf=False)
    def contact(self, **_kw):
        """
        Body (JSON):
          name*, email*, message*, phone?, subject?
        """
        try:
            env  = request.env(user=1)
            body = json.loads(request.httprequest.data or '{}')

            name    = (body.get('name')    or '').strip()
            email   = (body.get('email')   or '').strip()
            message = (body.get('message') or '').strip()
            phone   = (body.get('phone')   or '').strip()
            subject = body.get('subject', 'general')

            if not name:
                return _err('Name is required',    400, 'VALIDATION_ERROR')
            if not email or '@' not in email:
                return _err('Valid email required', 400, 'VALIDATION_ERROR')
            if not message:
                return _err('Message is required', 400, 'VALIDATION_ERROR')

            valid_subjects = [s[0] for s in env['cargo.website.contact']._fields['subject'].selection]
            if subject not in valid_subjects:
                subject = 'general'

            ip_addr   = request.httprequest.remote_addr
            user_agent = request.httprequest.user_agent.string if request.httprequest.user_agent else ''

            env['cargo.website.contact'].create({
                'name':       name,
                'email':      email,
                'phone':      phone or False,
                'subject':    subject,
                'message':    message,
                'source':     'website',
                'ip_address': ip_addr,
                'user_agent': user_agent,
            })

            return _ok({
                'success': True,
                'message': 'Thank you! We\'ll get back to you within 24 hours.',
            })
        except json.JSONDecodeError:
            return _err('Invalid JSON body', 400, 'BAD_REQUEST')
        except Exception as exc:
            _logger.exception('contact error: %s', exc)
            return _err('Server error', 500, 'SERVER_ERROR')

    # ── CORS preflight ────────────────────────────────────────────────────────

    @http.route([
        '/api/website/config',
        '/api/flash-sales',
        '/api/coupons',
        '/api/blog',
        '/api/blog/categories',
        '/api/faq',
        '/api/faq/categories',
        '/api/careers',
        '/api/contact',
    ], auth='none', methods=['OPTIONS'], type='http', csrf=False)
    def cors_preflight(self, **_kw):
        return request.make_response('', status=204, headers=[
            ('Access-Control-Allow-Origin',  '*'),
            ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
            ('Access-Control-Allow-Headers', 'Content-Type, Authorization'),
        ])
