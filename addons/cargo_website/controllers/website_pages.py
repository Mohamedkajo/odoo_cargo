# -*- coding: utf-8 -*-
"""
cargo_website — QWeb page controllers
======================================
Serves every Cargo website page as a server-rendered Odoo QWeb template.

Routes mirror the React website's client-side routes:
  / /about /services /marketplace /promotions
  /blog /blog/<slug> /faq /careers /contact
  /download /privacy /terms
"""
import logging
from datetime import datetime, timezone

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


def _time_left(dt_end):
    """Return a human-readable countdown string for a datetime."""
    if not dt_end:
        return ''
    now = datetime.now(timezone.utc)
    if hasattr(dt_end, 'tzinfo') and dt_end.tzinfo is None:
        dt_end = dt_end.replace(tzinfo=timezone.utc)
    diff = (dt_end - now).total_seconds()
    if diff <= 0:
        return 'Ended'
    d = int(diff // 86400)
    h = int((diff % 86400) // 3600)
    m = int((diff % 3600) // 60)
    if d > 0:
        return f'{d}d {h}h remaining'
    if h > 0:
        return f'{h}h {m}m remaining'
    return f'{m}m remaining'


class CargoWebsitePages(http.Controller):

    # ── helpers ────────────────────────────────────────────────────────────────

    def _cfg(self):
        """Return the singleton website config (or empty record)."""
        return request.env['cargo.website.config'].sudo().search([], limit=1)

    # ── home ───────────────────────────────────────────────────────────────────

    @http.route('/', auth='public', website=True, sitemap=True)
    def home(self, **kw):
        env = request.env
        flash_sales = env['cargo.website.flash.sale'].sudo().search(
            [('is_active', '=', True)], order='sequence', limit=3)
        stores = env['cargo.store'].sudo().search(
            [('is_featured', '=', True), ('active', '=', True)], limit=6)
        return request.render('cargo_website.page_home', {
            'flash_sales': flash_sales,
            'stores': stores,
        })

    # ── static informational pages ─────────────────────────────────────────────

    @http.route('/about', auth='public', website=True, sitemap=True)
    def about(self, **kw):
        return request.render('cargo_website.page_about', {})

    @http.route('/services', auth='public', website=True, sitemap=True)
    def services(self, **kw):
        return request.render('cargo_website.page_services', {})

    @http.route('/download', auth='public', website=True, sitemap=True)
    def download(self, **kw):
        return request.render('cargo_website.page_download', {'cfg': self._cfg()})

    @http.route('/privacy', auth='public', website=True, sitemap=True)
    def privacy(self, **kw):
        return request.render('cargo_website.page_privacy', {})

    @http.route('/terms', auth='public', website=True, sitemap=True)
    def terms(self, **kw):
        return request.render('cargo_website.page_terms', {})

    # ── marketplace ────────────────────────────────────────────────────────────

    @http.route('/marketplace', auth='public', website=True, sitemap=True)
    def marketplace(self, search='', category='', **kw):
        env = request.env
        domain = [('active', '=', True)]
        if search:
            domain.append(('name', 'ilike', search))
        if category:
            domain.append(('category_name', '=', category))
        stores = env['cargo.store'].sudo().search(domain, limit=48)
        categories = env['cargo.category'].sudo().search([])
        return request.render('cargo_website.page_marketplace', {
            'stores': stores,
            'categories': categories,
            'search': search,
            'current_category': category,
        })

    # ── promotions ─────────────────────────────────────────────────────────────

    @http.route('/promotions', auth='public', website=True, sitemap=True)
    def promotions(self, **kw):
        env = request.env
        flash_sales = env['cargo.website.flash.sale'].sudo().search(
            [('is_active', '=', True)], order='sequence')
        # Attach pre-computed countdown string so templates stay logic-free
        sales_data = []
        for s in flash_sales:
            sales_data.append({
                'rec': s,
                'time_left': _time_left(s.valid_until),
            })
        coupons = env['cargo.coupon'].sudo().search(
            [('is_active', '=', True)], limit=24)
        return request.render('cargo_website.page_promotions', {
            'sales_data': sales_data,
            'coupons': coupons,
        })

    # ── blog ───────────────────────────────────────────────────────────────────

    @http.route('/blog', auth='public', website=True, sitemap=True)
    def blog(self, category='', **kw):
        env = request.env
        domain = [('is_published', '=', True)]
        current_cat = None
        if category:
            current_cat = env['cargo.website.blog.category'].sudo().search(
                [('slug', '=', category)], limit=1)
            if current_cat:
                domain.append(('category_id', '=', current_cat.id))
        posts = env['cargo.website.blog.post'].sudo().search(
            domain, order='is_featured desc, published_date desc')
        categories = env['cargo.website.blog.category'].sudo().search([])
        return request.render('cargo_website.page_blog', {
            'posts': posts,
            'categories': categories,
            'current_category': category,
        })

    @http.route('/blog/<string:slug>', auth='public', website=True, sitemap=False)
    def blog_post(self, slug, **kw):
        post = request.env['cargo.website.blog.post'].sudo().search(
            [('slug', '=', slug), ('is_published', '=', True)], limit=1)
        if not post:
            return request.not_found()
        return request.render('cargo_website.page_blog_post', {'post': post})

    # ── faq ────────────────────────────────────────────────────────────────────

    @http.route('/faq', auth='public', website=True, sitemap=True)
    def faq(self, category_id='', **kw):
        env = request.env
        domain = [('is_active', '=', True)]
        cat_id_int = 0
        if category_id:
            try:
                cat_id_int = int(category_id)
                domain.append(('category_id', '=', cat_id_int))
            except (ValueError, TypeError):
                pass
        faqs = env['cargo.website.faq'].sudo().search(domain, order='category_id, sequence')
        faq_categories = env['cargo.website.faq.category'].sudo().search(
            [], order='sequence')
        return request.render('cargo_website.page_faq', {
            'faqs': faqs,
            'faq_categories': faq_categories,
            'current_category_id': cat_id_int,
        })

    # ── careers ────────────────────────────────────────────────────────────────

    @http.route('/careers', auth='public', website=True, sitemap=True)
    def careers(self, department='', **kw):
        env = request.env
        all_jobs = env['cargo.website.job'].sudo().search(
            [('is_active', '=', True)], order='department, title')
        departments = sorted(set(all_jobs.mapped('department')))
        if department:
            jobs = all_jobs.filtered(lambda j: j.department == department)
        else:
            jobs = all_jobs
        return request.render('cargo_website.page_careers', {
            'jobs': jobs,
            'departments': departments,
            'current_department': department,
            'total_jobs': len(all_jobs),
        })

    # ── contact ────────────────────────────────────────────────────────────────

    @http.route('/contact', auth='public', website=True, sitemap=True,
                methods=['GET', 'POST'])
    def contact(self, **kw):
        if request.httprequest.method == 'POST':
            name    = kw.get('name', '').strip()
            email   = kw.get('email', '').strip()
            phone   = kw.get('phone', '').strip()
            subject = kw.get('subject', 'general')
            message = kw.get('message', '').strip()

            if not (name and email and message):
                return request.render('cargo_website.page_contact', {
                    'error': 'Please fill in Name, Email, and Message.',
                    'form': kw,
                })
            # Validate subject against allowed values
            allowed = {'general', 'support', 'partnership', 'vendor',
                       'driver', 'billing', 'other'}
            if subject not in allowed:
                subject = 'general'

            try:
                request.env['cargo.website.contact'].sudo().create({
                    'name':       name,
                    'email':      email,
                    'phone':      phone or False,
                    'subject':    subject,
                    'message':    message,
                    'source':     'website',
                    'ip_address': request.httprequest.remote_addr,
                    'user_agent': request.httprequest.user_agent.string,
                })
            except Exception:
                _logger.exception('Failed to save contact form submission')
                return request.render('cargo_website.page_contact', {
                    'error': 'Failed to send your message. Please try again.',
                    'form': kw,
                })
            return request.render('cargo_website.page_contact', {'sent': True})

        return request.render('cargo_website.page_contact', {})
