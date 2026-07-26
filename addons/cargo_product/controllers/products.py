# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
CargoProductController — Product catalogue endpoints for the Flutter apps.

All queries run against product.template (native Odoo model), filtered by
cargo_store_id != False to scope to marketplace products.

Routes:
  GET /api/products              — paginated product list
  GET /api/products/trending     — featured products
  GET /api/products/:productId   — product detail with add-ons and variants
  GET /api/flash-sales           — products currently on flash sale
"""
import json
import logging
from datetime import datetime

from odoo import http
from odoo.http import request

from cargo_base.constants import HTTP_200, HTTP_404, ERR_NOT_FOUND
from cargo_api.controllers.base import CargoBaseController

_logger = logging.getLogger(__name__)

# Domain fragment that restricts queries to marketplace products
_CARGO_PRODUCT_DOMAIN = [
    ('active', '=', True),
    ('cargo_store_id', '!=', False),
    ('cargo_is_available', '=', True),
]


def _page_params():
    try:
        limit  = max(1, min(int(request.httprequest.args.get('limit', 20)), 100))
        offset = max(0, int(request.httprequest.args.get('offset', 0)))
    except (TypeError, ValueError):
        limit, offset = 20, 0
    return limit, offset


def _ok(data, status=HTTP_200):
    return request.make_response(
        json.dumps(data),
        status=status,
        headers=[('Content-Type', 'application/json')],
    )


class CargoProductController(CargoBaseController):

    @http.route(
        '/api/products',
        auth='none', methods=['GET'],
        type='http', csrf=False, save_session=False,
    )
    def cargo_list_products(self, **kwargs):
        """GET /api/products[?storeId=N&categoryId=N&search=text&limit=20&offset=0]"""
        args          = request.httprequest.args
        limit, offset = _page_params()

        domain = list(_CARGO_PRODUCT_DOMAIN)
        if args.get('storeId'):
            try:
                domain.append(('cargo_store_id', '=', int(args['storeId'])))
            except (ValueError, TypeError):
                pass
        if args.get('categoryId'):
            try:
                domain.append(('categ_id', '=', int(args['categoryId'])))
            except (ValueError, TypeError):
                pass
        if args.get('search', '').strip():
            domain.append(('name', 'ilike', args['search'].strip()))

        products = request.env['product.template'].sudo().search(domain, limit=limit, offset=offset)
        total    = request.env['product.template'].sudo().search_count(domain)

        return _ok({
            'data':   [p.cargo_to_api_dict() for p in products],
            'total':  total,
            'limit':  limit,
            'offset': offset,
        })

    @http.route(
        '/api/products/trending',
        auth='none', methods=['GET'],
        type='http', csrf=False, save_session=False,
    )
    def cargo_trending_products(self, **kwargs):
        """GET /api/products/trending — featured / trending products."""
        limit, _ = _page_params()
        domain   = list(_CARGO_PRODUCT_DOMAIN) + [('cargo_is_featured', '=', True)]
        products = request.env['product.template'].sudo().search(domain, limit=limit)
        return _ok([p.cargo_to_api_dict() for p in products])

    @http.route(
        '/api/products/<int:product_id>',
        auth='none', methods=['GET'],
        type='http', csrf=False, save_session=False,
    )
    def cargo_get_product(self, product_id, **kwargs):
        """GET /api/products/:productId — detail with add-ons and variants."""
        product = request.env['product.template'].sudo().browse(product_id)
        if not product.exists() or not product.cargo_store_id:
            return _ok({'error': ERR_NOT_FOUND, 'message': 'Product not found.'}, HTTP_404)
        return _ok(product.cargo_to_api_detail_dict())

    @http.route(
        '/api/flash-sales',
        auth='none', methods=['GET'],
        type='http', csrf=False, save_session=False,
    )
    def cargo_flash_sales(self, **kwargs):
        """GET /api/flash-sales — products currently on flash sale."""
        now  = datetime.utcnow()
        domain = [
            ('active', '=', True),
            ('cargo_store_id', '!=', False),
            ('cargo_is_available', '=', True),
            ('cargo_is_flash_sale', '=', True),
            '|',
            ('cargo_flash_sale_end', '=', False),
            ('cargo_flash_sale_end', '>=', now),
        ]
        products = request.env['product.template'].sudo().search(domain, limit=20)
        return _ok([p.cargo_to_api_detail_dict() for p in products])
