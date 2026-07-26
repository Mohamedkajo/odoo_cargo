# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
res.users extension — Cargo wallet fields.

Extends the native res.users model with an in-app wallet balance.
Wallet transactions are recorded in cargo.wallet.transaction.

The balance field is NOT computed from transactions to keep reads O(1).
It is updated transactionally by _credit() / _debit() with a balance check
to prevent overdrafts.
"""
from odoo import api, fields, models
from odoo.exceptions import UserError


class CargoWalletUser(models.Model):
    """Add wallet balance to res.users."""

    _inherit = 'res.users'

    cargo_wallet_balance = fields.Monetary(
        string='Wallet Balance (EGP)',
        currency_field='cargo_wallet_currency_id',
        default=0.0,
    )
    cargo_wallet_currency_id = fields.Many2one(
        'res.currency', 'Wallet Currency',
        default=lambda self: self.env.ref('base.EGP', raise_if_not_found=False),
    )

    def cargo_wallet_credit(self, amount: float, note='', order=None):
        """Add funds to the wallet and create a transaction record."""
        self.ensure_one()
        if amount <= 0:
            raise UserError('Credit amount must be positive.')
        self.sudo().write({
            'cargo_wallet_balance': self.cargo_wallet_balance + amount,
        })
        self._create_wallet_tx('credit', amount, note, order)
        return self.cargo_wallet_balance

    def cargo_wallet_debit(self, amount: float, note='', order=None):
        """Deduct funds from the wallet (raises if insufficient balance)."""
        self.ensure_one()
        if amount <= 0:
            raise UserError('Debit amount must be positive.')
        if self.cargo_wallet_balance < amount:
            raise UserError(
                f'Insufficient wallet balance. '
                f'Available: EGP {self.cargo_wallet_balance:.2f}, '
                f'Required: EGP {amount:.2f}.'
            )
        self.sudo().write({
            'cargo_wallet_balance': self.cargo_wallet_balance - amount,
        })
        self._create_wallet_tx('debit', amount, note, order)
        return self.cargo_wallet_balance

    def _create_wallet_tx(self, tx_type: str, amount: float, note='', order=None):
        self.env['cargo.wallet.transaction'].sudo().create({
            'user_id':   self.id,
            'type':      tx_type,
            'amount':    amount,
            'note':      note,
            'order_id':  order.id if order else False,
            'balance_after': self.cargo_wallet_balance,
        })


class CargoWalletTransaction(models.Model):
    """Immutable audit log of wallet credits and debits."""

    _name = 'cargo.wallet.transaction'
    _description = 'Cargo Wallet Transaction'
    _order = 'create_date desc'

    user_id = fields.Many2one(
        'res.users', 'User',
        required=True, ondelete='cascade', index=True,
    )
    type = fields.Selection(
        [('credit', 'Credit'), ('debit', 'Debit')],
        'Type', required=True,
    )
    amount        = fields.Monetary('Amount', currency_field='currency_id')
    currency_id   = fields.Many2one('res.currency', default=lambda s: s.env.ref('base.EGP', False))
    balance_after = fields.Monetary('Balance After', currency_field='currency_id')
    note          = fields.Char('Note')
    order_id      = fields.Many2one(
        'sale.order', 'Related Order',
        ondelete='set null', index=True,
        domain=[('cargo_status', '!=', False)],
    )

    def to_tx_dict(self) -> dict:
        self.ensure_one()
        return {
            'id':           self.id,
            'type':         self.type,
            'amount':       self.amount,
            'balanceAfter': self.balance_after,
            'note':         self.note or '',
            'orderId':      self.order_id.id if self.order_id else None,
            'date':         self.create_date.isoformat() if self.create_date else None,
        }
