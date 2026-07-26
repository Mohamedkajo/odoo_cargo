# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
CargoStoreController — Store-browsing REST endpoints.

Routes owned by this module:
  GET /api/stores
  GET /api/stores/featured
  GET /api/stores/nearby
  GET /api/stores/online
  GET /api/stores/:storeId
  GET /api/stores/:storeId/products
  GET /api/stores/:storeId/categories

Route NOT owned here:
  GET /api/categories   → cargo_category.controllers.categories

Product queries use product.template (the native model) filtered by
cargo_store_id.  Product categories are product.category records, accessed
via product.template.categ_id.
"""
import json
import logging

from odoo import http
from odoo.http import request

from odoo.addons.cargo_base.constants import HTTP_200, HTTP_404, ERR_NOT_FOUND
from odoo.addons.cargo_api.controllers.base import CargoBaseController

_logger = logging.getLogger(__name__)


def _page(default_limit=20):
    try:
        limit  = max(1, min(int(request.httprequest.args.get('limit',  default_limit)), 100))
        offset = max(0, int(request.httprequest.args.get('offset', 0)))
    except (TypeError, ValueError):
        limit, offset = default_limit, 0
    return limit, offset


def _float_arg(name):
    try:
        return float(request.httprequest.args.get(name))
    except (TypeError, ValueError):
        return None


def _ok(data):
    return request.make_response(
        json.dumps(data),
        status=HTTP_200,
        headers=[('Content-Type', 'application/json')],
    )


def _not_found(msg='Not found.'):
    return request.make_response(
        json.dumps({'error': ERR_NOT_FOUND, 'message': msg}),
        status=HTTP_404,
        headers=[('Content-Type', 'application/json')],
    )


class CargoStoreController(CargoBaseController):

    # ── Store list ────────────────────────────────────────────────────────────

    @http.route('/api/stores', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    def cargo_list_stores(self, **kw):
        """GET /api/stores[?categoryId=N&search=text&limit=20&offset=0]"""
        args   = request.httprequest.args
        limit, offset = _page()

        domain = [('active', '=', True)]
        if args.get('categoryId'):
            try:
                domain.append(('category_id', '=', int(args['categoryId'])))
            except (ValueError, TypeError):
                pass
        if (s := (args.get('search') or '').strip()):
            domain.append(('name', 'ilike', s))

        lat, lng = _float_arg('lat'), _float_arg('lng')
        stores   = request.env['cargo.store'].sudo().search(domain, limit=limit, offset=offset)
        total    = request.env['cargo.store'].sudo().search_count(domain)

        return _ok({
            'data':   [s.to_store_dict(lat=lat, lng=lng) for s in stores],
            'total':  total,
            'limit':  limit,
            'offset': offset,
        })

    @http.route('/api/stores/featured', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    def cargo_featured_stores(self, **kw):
        """GET /api/stores/featured"""
        limit, _ = _page()
        stores = request.env['cargo.store'].sudo().search(
            [('active', '=', True), ('is_featured', '=', True)], limit=limit,
        )
        return _ok([s.to_store_dict() for s in stores])

    @http.route('/api/stores/nearby', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    def cargo_nearby_stores(self, **kw):
        """GET /api/stores/nearby[?lat=&lng=&limit=20]"""
        lat, lng  = _float_arg('lat'), _float_arg('lng')
        limit, _  = _page()
        stores    = request.env['cargo.store'].sudo().search(
            [('active', '=', True), ('is_open', '=', True)], limit=limit * 3,
        )
        dicts = sorted(
            [s.to_store_dict(lat=lat, lng=lng) for s in stores],
            key=lambda d: d['distance'] if d['distance'] is not None else 9999,
        )
        return _ok(dicts[:limit])

    @http.route('/api/stores/online', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    def cargo_online_stores(self, **kw):
        """GET /api/stores/online"""
        limit, offset = _page()
        stores = request.env['cargo.store'].sudo().search(
            [('active', '=', True), ('is_online', '=', True)],
            limit=limit, offset=offset,
        )
        return _ok([s.to_store_dict() for s in stores])

    # ── Store detail ──────────────────────────────────────────────────────────

    @http.route('/api/stores/<int:store_id>', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    def cargo_get_store(self, store_id, **kw):
        """GET /api/stores/:storeId"""
        store = request.env['cargo.store'].sudo().browse(store_id)
        if not store.exists():
            return _not_found('Store not found.')
        return _ok(store.to_store_dict(lat=_float_arg('lat'), lng=_float_arg('lng')))

    @http.route('/api/stores/<int:store_id>/products', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    def cargo_store_products(self, store_id, **kw):
        """GET /api/stores/:storeId/products[?categoryId=N&limit=20&offset=0]

        Queries product.template filtered by cargo_store_id.  The cargo_is_available
        flag (added by cargo_base) is used to exclude out-of-stock items.
        """
        store = request.env['cargo.store'].sudo().browse(store_id)
        if not store.exists():
            return _not_found('Store not found.')

        limit, offset = _page()
        domain = [
            ('cargo_store_id', '=', store_id),
            ('active', '=', True),
            ('cargo_is_available', '=', True),
        ]
        if (cid := request.httprequest.args.get('categoryId')):
            try:
                domain.append(('categ_id', '=', int(cid)))
            except (ValueError, TypeError):
                pass

        products = request.env['product.template'].sudo().search(domain, limit=limit, offset=offset)
        total    = request.env['product.template'].sudo().search_count(domain)
        return _ok({'data': [p.cargo_to_api_dict() for p in products], 'total': total})

    @http.route('/api/stores/<int:store_id>/categories', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    def cargo_store_categories(self, store_id, **kw):
        """GET /api/stores/:storeId/categories

        Returns distinct product.category records used by products in this store.
        Category is read from product.template.categ_id (native Odoo field).
        """
        store = request.env['cargo.store'].sudo().browse(store_id)
        if not store.exists():
            return _not_found('Store not found.')

        products = request.env['product.template'].sudo().search(
            [('cargo_store_id', '=', store_id), ('categ_id', '!=', False)]
        )
        seen = {}
        for p in products:
            cid = p.categ_id.id
            if cid not in seen:
                seen[cid] = p.categ_id

        cats = sorted(seen.values(), key=lambda c: (c.cargo_sort_order, c.name))
        return _ok([c.cargo_to_api_dict() for c in cats])
