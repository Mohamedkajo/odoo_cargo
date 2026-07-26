# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
CargoWalletController — Wallet endpoints for the Cargo Flutter app.

Routes:
  GET  /api/wallet                 — wallet balance + loyalty points
  GET  /api/wallet/transactions    — transaction history
  POST /api/wallet/topup           — add funds
"""
import json
import logging

from odoo import http
from odoo.http import request

from cargo_base.constants import HTTP_200, HTTP_400, ERR_VALIDATION
from cargo_api.controllers.base import CargoBaseController
from cargo_api.utils.decorators import require_cargo_auth

_logger = logging.getLogger(__name__)


def _json_body():
    try:
        raw = request.httprequest.get_data(as_text=True)
        return json.loads(raw) if raw else {}
    except Exception:
        return {}


class CargoWalletController(CargoBaseController):

    @http.route(
        '/api/wallet',
        auth='none',
        methods=['GET'],
        type='http',
        csrf=False,
        save_session=False,
    )
    @require_cargo_auth()
    def cargo_get_wallet(self, **kwargs):
        """GET /api/wallet"""
        user   = request.cargo_user
        wallet = request.env['cargo.wallet'].sudo().get_or_create_for_user(user.id)
        return request.make_response(
            json.dumps(wallet.to_wallet_dict()),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )

    @http.route(
        '/api/wallet/transactions',
        auth='none',
        methods=['GET'],
        type='http',
        csrf=False,
        save_session=False,
    )
    @require_cargo_auth()
    def cargo_wallet_transactions(self, **kwargs):
        """GET /api/wallet/transactions[?limit=20&offset=0]"""
        user = request.cargo_user
        try:
            limit  = max(1, min(int(request.httprequest.args.get('limit', 20)), 100))
            offset = max(0, int(request.httprequest.args.get('offset', 0)))
        except (TypeError, ValueError):
            limit, offset = 20, 0

        wallet = request.env['cargo.wallet'].sudo().get_or_create_for_user(user.id)
        txns   = request.env['cargo.wallet.transaction'].sudo().search(
            [('wallet_id', '=', wallet.id)],
            order='id desc',
            limit=limit,
            offset=offset,
        )
        total = request.env['cargo.wallet.transaction'].sudo().search_count(
            [('wallet_id', '=', wallet.id)]
        )

        data = [t.to_transaction_dict() for t in txns]
        return request.make_response(
            json.dumps({'data': data, 'total': total}),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )

    @http.route(
        '/api/wallet/topup',
        auth='none',
        methods=['POST'],
        type='http',
        csrf=False,
        save_session=False,
    )
    @require_cargo_auth()
    def cargo_wallet_topup(self, **kwargs):
        """
        POST /api/wallet/topup

        Body: { amount, paymentMethod?, reference? }
        Returns: { balance, currency, loyaltyPoints, transaction }
        """
        user = request.cargo_user
        body = _json_body()

        try:
            amount = float(body.get('amount', 0))
        except (ValueError, TypeError):
            amount = 0.0

        if amount <= 0:
            return request.make_response(
                json.dumps({'error': ERR_VALIDATION, 'message': 'Amount must be a positive number.'}),
                status=HTTP_400,
                headers=[('Content-Type', 'application/json')],
            )

        # Maximum single top-up: EGP 10,000
        if amount > 10_000:
            return request.make_response(
                json.dumps({'error': ERR_VALIDATION, 'message': 'Maximum single top-up is EGP 10,000.'}),
                status=HTTP_400,
                headers=[('Content-Type', 'application/json')],
            )

        wallet = request.env['cargo.wallet'].sudo().get_or_create_for_user(user.id)

        try:
            txn = wallet.topup(
                amount=amount,
                reference=body.get('reference'),
                description=f'Top-up via {body.get("paymentMethod", "card")} — EGP {amount:.2f}',
            )
        except Exception as exc:
            return request.make_response(
                json.dumps({'error': 'ERR_TOPUP', 'message': str(exc)}),
                status=HTTP_400,
                headers=[('Content-Type', 'application/json')],
            )

        result = wallet.to_wallet_dict()
        result['transaction'] = txn.to_transaction_dict()
        return request.make_response(
            json.dumps(result),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )
