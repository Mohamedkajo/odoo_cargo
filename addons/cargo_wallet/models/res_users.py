# -*- coding: utf-8 -*-
"""
res.users extension for cargo_wallet.

Provides _get_cargo_wallet_balance() so cargo_auth can return the real
wallet balance without having a hard dependency on cargo_wallet.
"""
from odoo import models


class ResUsers(models.Model):
    _inherit = 'res.users'

    def _get_cargo_wallet_balance(self):
        """
        Return the current wallet balance for this user.
        Called from cargo_auth's cargo_to_auth_dict() via hasattr guard.
        """
        self.ensure_one()
        wallet = self.env['cargo.wallet'].sudo().search(
            [('user_id', '=', self.id)], limit=1,
        )
        return float(wallet.balance) if wallet else 0.0
