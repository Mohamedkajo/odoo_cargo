# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
CargoProductController — Product catalogue endpoints for the Flutter apps.

Routes:
  GET /api/products              — paginated product list
  GET /api/products/trending     — trending / featured products
  GET /api/products/:productId   — product detail with variants and addons
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


def _page_params():
    try:
        limit  = max(1, min(int(request.httprequest.args.get('limit', 20)), 100))
        offset = max(0, int(request.httprequest.args.get('offset', 0)))
    except (TypeError, ValueError):
        limit, offset = 20, 0
    return limit, offset


class CargoProductController(CargoBaseController):

    @http.route(
        '/api/products',
        auth='none',
        methods=['GET'],
        type='http',
        csrf=False,
        save_session=False,
    )
    def cargo_list_products(self, **kwargs):
        """
        GET /api/products[?storeId=N&categoryId=N&search=text&limit=20&offset=0]
        """
        args = request.httprequest.args
        limit, offset = _page_params()

        domain = [('active', '=', True), ('is_available', '=', True)]
        if args.get('storeId'):
            try:
                domain.append(('store_id', '=', int(args['storeId'])))
            except (ValueError, TypeError):
                pass
        if args.get('categoryId'):
            try:
                domain.append(('category_id', '=', int(args['categoryId'])))
            except (ValueError, TypeError):
                pass
        if args.get('search', '').strip():
            domain.append(('name', 'ilike', args['search'].strip()))

        products = request.env['cargo.product'].sudo().search(domain, limit=limit, offset=offset)
        total    = request.env['cargo.product'].sudo().search_count(domain)
        data     = [p.to_product_dict() for p in products]

        return request.make_response(
            json.dumps({'data': data, 'total': total, 'limit': limit, 'offset': offset}),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )

    @http.route(
        '/api/products/trending',
        auth='none',
        methods=['GET'],
        type='http',
        csrf=False,
        save_session=False,
    )
    def cargo_trending_products(self, **kwargs):
        """GET /api/products/trending — featured/trending products."""
        limit, _ = _page_params()
        products = request.env['cargo.product'].sudo().search(
            [('active', '=', True), ('is_available', '=', True), ('is_featured', '=', True)],
            limit=limit,
        )
        data = [p.to_product_dict() for p in products]
        return request.make_response(
            json.dumps(data),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )

    @http.route(
        '/api/products/<int:product_id>',
        auth='none',
        methods=['GET'],
        type='http',
        csrf=False,
        save_session=False,
    )
    def cargo_get_product(self, product_id, **kwargs):
        """GET /api/products/:productId"""
        product = request.env['cargo.product'].sudo().browse(product_id)
        if not product.exists():
            return request.make_response(
                json.dumps({'error': ERR_NOT_FOUND, 'message': 'Product not found.'}),
                status=HTTP_404,
                headers=[('Content-Type', 'application/json')],
            )
        return request.make_response(
            json.dumps(product.to_product_detail_dict()),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )

    @http.route(
        '/api/flash-sales',
        auth='none',
        methods=['GET'],
        type='http',
        csrf=False,
        save_session=False,
    )
    def cargo_flash_sales(self, **kwargs):
        """GET /api/flash-sales — products currently on flash sale."""
        now = datetime.utcnow()
        products = request.env['cargo.product'].sudo().search([
            ('active', '=', True),
            ('is_available', '=', True),
            ('is_flash_sale', '=', True),
            '|',
            ('flash_sale_end', '=', False),
            ('flash_sale_end', '>=', now),
        ], limit=20)

        data = []
        for p in products:
            d = p.to_product_dict()
            d['flashSalePrice'] = p.flash_sale_price or p.price
            d['flashSaleEnd']   = p.flash_sale_end.isoformat() if p.flash_sale_end else None
            data.append(d)

        return request.make_response(
            json.dumps(data),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )
