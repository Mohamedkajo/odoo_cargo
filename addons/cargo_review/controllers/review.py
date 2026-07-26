# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""CargoReviewController — Store and product review endpoints.

Product lookups use product.template (native model, filtered by cargo_store_id).
"""
import json
import logging

from odoo import http
from odoo.http import request

from cargo_base.constants import HTTP_200, HTTP_201, HTTP_400, HTTP_404, ERR_VALIDATION, ERR_NOT_FOUND
from cargo_api.controllers.base import CargoBaseController
from cargo_api.utils.decorators import require_cargo_auth

_logger = logging.getLogger(__name__)


def _body():
    try:
        return json.loads(request.httprequest.get_data(as_text=True) or '{}')
    except Exception:
        return {}


def _ok(data, status=HTTP_200):
    return request.make_response(
        json.dumps(data), status=status,
        headers=[('Content-Type', 'application/json')],
    )


class CargoReviewController(CargoBaseController):

    # ── Store reviews ─────────────────────────────────────────────────────────

    @http.route('/api/stores/<int:store_id>/reviews', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    def list_store_reviews(self, store_id, **kw):
        store = request.env['cargo.store'].sudo().browse(store_id)
        if not store.exists():
            return _ok({'error': ERR_NOT_FOUND, 'message': 'Store not found.'}, HTTP_404)
        reviews = request.env['cargo.review'].sudo().search([
            ('review_type', '=', 'store'),
            ('store_id',    '=', store_id),
            ('is_approved', '=', True),
        ])
        return _ok([r.to_review_dict() for r in reviews])

    @http.route('/api/stores/<int:store_id>/reviews', auth='none', methods=['POST'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth()
    def create_store_review(self, store_id, **kw):
        store = request.env['cargo.store'].sudo().browse(store_id)
        if not store.exists():
            return _ok({'error': ERR_NOT_FOUND, 'message': 'Store not found.'}, HTTP_404)
        body = _body()
        try:
            rating = int(body.get('rating', 0))
            if not 1 <= rating <= 5:
                raise ValueError
        except (TypeError, ValueError):
            return _ok({'error': ERR_VALIDATION,
                        'message': 'rating must be an integer between 1 and 5.'}, HTTP_400)
        review = request.env['cargo.review'].sudo().create({
            'user_id':     request.cargo_user.id,
            'review_type': 'store',
            'store_id':    store_id,
            'rating':      rating,
            'comment':     body.get('comment', ''),
        })
        return _ok(review.to_review_dict(), HTTP_201)

    # ── Product reviews ───────────────────────────────────────────────────────

    @http.route('/api/products/<int:product_id>/reviews', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    def list_product_reviews(self, product_id, **kw):
        """product_id is a product.template id."""
        product = request.env['product.template'].sudo().browse(product_id)
        if not product.exists() or not product.cargo_store_id:
            return _ok({'error': ERR_NOT_FOUND, 'message': 'Product not found.'}, HTTP_404)
        reviews = request.env['cargo.review'].sudo().search([
            ('review_type', '=', 'product'),
            ('product_id',  '=', product_id),
            ('is_approved', '=', True),
        ])
        return _ok([r.to_review_dict() for r in reviews])

    @http.route('/api/products/<int:product_id>/reviews', auth='none', methods=['POST'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth()
    def create_product_review(self, product_id, **kw):
        """product_id is a product.template id."""
        product = request.env['product.template'].sudo().browse(product_id)
        if not product.exists() or not product.cargo_store_id:
            return _ok({'error': ERR_NOT_FOUND, 'message': 'Product not found.'}, HTTP_404)
        body = _body()
        try:
            rating = int(body.get('rating', 0))
            if not 1 <= rating <= 5:
                raise ValueError
        except (TypeError, ValueError):
            return _ok({'error': ERR_VALIDATION,
                        'message': 'rating must be an integer between 1 and 5.'}, HTTP_400)
        review = request.env['cargo.review'].sudo().create({
            'user_id':     request.cargo_user.id,
            'review_type': 'product',
            'product_id':  product_id,
            'rating':      rating,
            'comment':     body.get('comment', ''),
        })
        return _ok(review.to_review_dict(), HTTP_201)
