# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
CargoFavoriteController — Favorites endpoints for the Flutter Customer App.

Routes:
  GET  /api/favorites          — list my favorited stores and products
  POST /api/favorites/toggle   — add or remove a favorite
"""
import json
import logging

from odoo import http
from odoo.http import request

from odoo.addons.cargo_base.constants import HTTP_200, HTTP_400, ERR_VALIDATION
from odoo.addons.cargo_api.controllers.base import CargoBaseController
from odoo.addons.cargo_api.utils.decorators import require_cargo_auth

_logger = logging.getLogger(__name__)


def _json_body():
    try:
        raw = request.httprequest.get_data(as_text=True)
        return json.loads(raw) if raw else {}
    except Exception:
        return {}


class CargoFavoriteController(CargoBaseController):

    @http.route(
        '/api/favorites',
        auth='none',
        methods=['GET'],
        type='http',
        csrf=False,
        save_session=False,
    )
    @require_cargo_auth()
    def cargo_list_favorites(self, **kwargs):
        """GET /api/favorites — list all favorited stores and products."""
        user = request.cargo_user
        favs = request.env['cargo.favorite'].sudo().search([('user_id', '=', user.id)])

        stores   = []
        products = []
        for fav in favs:
            if fav.type == 'store' and fav.store_id:
                stores.append(fav.store_id.to_store_dict())
            elif fav.type == 'product' and fav.product_id:
                products.append(fav.product_id.to_product_dict())

        return request.make_response(
            json.dumps({'stores': stores, 'products': products}),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )

    @http.route(
        '/api/favorites/toggle',
        auth='none',
        methods=['POST'],
        type='http',
        csrf=False,
        save_session=False,
    )
    @require_cargo_auth()
    def cargo_toggle_favorite(self, **kwargs):
        """
        POST /api/favorites/toggle

        Body: { type: 'store' | 'product', id: int }
        Returns: { isFavorite: bool, type: str, id: int }
        """
        user = request.cargo_user
        body = _json_body()

        fav_type = body.get('type', '').strip()
        ref_id   = body.get('id')

        if fav_type not in ('store', 'product'):
            return request.make_response(
                json.dumps({'error': ERR_VALIDATION, 'message': 'type must be "store" or "product".'}),
                status=HTTP_400,
                headers=[('Content-Type', 'application/json')],
            )
        if not ref_id:
            return request.make_response(
                json.dumps({'error': ERR_VALIDATION, 'message': 'id is required.'}),
                status=HTTP_400,
                headers=[('Content-Type', 'application/json')],
            )

        try:
            ref_id = int(ref_id)
        except (ValueError, TypeError):
            return request.make_response(
                json.dumps({'error': ERR_VALIDATION, 'message': 'id must be an integer.'}),
                status=HTTP_400,
                headers=[('Content-Type', 'application/json')],
            )

        is_favorite = request.env['cargo.favorite'].sudo().toggle(user.id, fav_type, ref_id)
        return request.make_response(
            json.dumps({'isFavorite': is_favorite, 'type': fav_type, 'id': ref_id}),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )
