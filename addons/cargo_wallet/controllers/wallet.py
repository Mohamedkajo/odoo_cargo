# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
CargoWalletController — Wallet endpoints for the Cargo Flutter app.

Wallet data lives on res.users (extended by cargo_wallet module):
  res.users.cargo_wallet_balance   — current balance
  res.users.cargo_wallet_credit()  — add funds
  res.users.cargo_wallet_debit()   — deduct funds

Transaction history is in cargo.wallet.transaction (user_id FK).

Routes:
  GET  /api/wallet               — wallet balance
  GET  /api/wallet/transactions  — transaction history
  POST /api/wallet/topup         — add funds
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


def _ok(data, status=HTTP_200):
    return request.make_response(
        json.dumps(data), status=status,
        headers=[('Content-Type', 'application/json')],
    )


class CargoWalletController(CargoBaseController):

    @http.route('/api/wallet', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth()
    def cargo_get_wallet(self, **kwargs):
        """GET /api/wallet — current user's wallet balance."""
        user = request.cargo_user
        return _ok({
            'balance':  user.cargo_wallet_balance,
            'currency': 'EGP',
        })

    @http.route('/api/wallet/transactions', auth='none', methods=['GET'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth()
    def cargo_wallet_transactions(self, **kwargs):
        """GET /api/wallet/transactions[?limit=20&offset=0]"""
        user = request.cargo_user
        try:
            limit  = max(1, min(int(request.httprequest.args.get('limit', 20)), 100))
            offset = max(0, int(request.httprequest.args.get('offset', 0)))
        except (TypeError, ValueError):
            limit, offset = 20, 0

        txns = request.env['cargo.wallet.transaction'].sudo().search(
            [('user_id', '=', user.id)],
            order='id desc',
            limit=limit,
            offset=offset,
        )
        total = request.env['cargo.wallet.transaction'].sudo().search_count(
            [('user_id', '=', user.id)]
        )
        return _ok({'data': [t.to_tx_dict() for t in txns], 'total': total})

    @http.route('/api/wallet/topup', auth='none', methods=['POST'],
                type='http', csrf=False, save_session=False)
    @require_cargo_auth()
    def cargo_wallet_topup(self, **kwargs):
        """
        POST /api/wallet/topup

        Body: { amount, paymentMethod?, reference? }
        Returns: { balance, currency, transaction }
        """
        user = request.cargo_user
        body = _json_body()

        try:
            amount = float(body.get('amount', 0))
        except (ValueError, TypeError):
            amount = 0.0

        if amount <= 0:
            return _ok({'error': ERR_VALIDATION, 'message': 'Amount must be positive.'}, HTTP_400)
        if amount > 10_000:
            return _ok({'error': ERR_VALIDATION,
                        'message': 'Maximum single top-up is EGP 10,000.'}, HTTP_400)

        try:
            note = (f'Top-up via {body.get("paymentMethod", "card")} — EGP {amount:.2f} '
                    f'{body.get("reference", "")}').strip()
            new_balance = user.cargo_wallet_credit(amount, note=note)
        except Exception as exc:
            _logger.exception('Wallet top-up failed')
            return _ok({'error': 'ERR_TOPUP', 'message': str(exc)}, HTTP_400)

        last_tx = request.env['cargo.wallet.transaction'].sudo().search(
            [('user_id', '=', user.id)], order='id desc', limit=1,
        )
        return _ok({
            'balance':     new_balance,
            'currency':    'EGP',
            'transaction': last_tx.to_tx_dict() if last_tx else None,
        })
