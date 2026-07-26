# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
cargo.wallet and cargo.wallet.transaction — Digital wallet.

Flutter contract:
  GET /api/wallet → { balance, currency, loyaltyPoints }
  GET /api/wallet/transactions → [{ id, type, amount, description, createdAt, reference }]
  POST /api/wallet/topup → { balance, transaction }
"""
import logging

from odoo import api, fields, models

from cargo_base.constants import WALLET_TRANSACTION_TYPES, WALLET_TOPUP

_logger = logging.getLogger(__name__)


class CargoWallet(models.Model):
    _name = 'cargo.wallet'
    _description = 'Cargo Customer Wallet'
    _rec_name = 'user_id'

    user_id = fields.Many2one(
        'res.users', 'Customer',
        required=True, ondelete='cascade', index=True,
    )
    balance = fields.Float(
        'Balance (EGP)',
        digits=(10, 2),
        default=0.0,
    )
    currency = fields.Char('Currency', default='EGP')
    transaction_ids = fields.One2many(
        'cargo.wallet.transaction', 'wallet_id', string='Transactions',
    )

    _sql_constraints = [
        ('unique_user_wallet', 'UNIQUE(user_id)', 'Each user may have only one wallet.'),
        ('balance_non_negative', 'CHECK(balance >= 0)', 'Wallet balance cannot go negative.'),
    ]

    @api.model
    def get_or_create_for_user(self, user_id):
        wallet = self.sudo().search([('user_id', '=', user_id)], limit=1)
        if not wallet:
            wallet = self.sudo().create({'user_id': user_id, 'balance': 0.0})
        return wallet

    def topup(self, amount, reference=None, description=None):
        """
        Credit the wallet by `amount` and create a transaction record.
        Returns the new transaction record.
        """
        self.ensure_one()
        if amount <= 0:
            raise ValueError('Top-up amount must be positive.')
        self.sudo().write({'balance': self.balance + amount})
        txn = self.env['cargo.wallet.transaction'].sudo().create({
            'wallet_id':   self.id,
            'type':        WALLET_TOPUP,
            'amount':      amount,
            'description': description or f'Wallet top-up of EGP {amount:.2f}',
            'reference':   reference or '',
            'balance_after': self.balance,
        })
        return txn

    def debit(self, amount, txn_type, description=None, reference=None):
        """Debit the wallet for a purchase or payout."""
        self.ensure_one()
        if amount > self.balance:
            raise ValueError('Insufficient wallet balance.')
        self.sudo().write({'balance': self.balance - amount})
        return self.env['cargo.wallet.transaction'].sudo().create({
            'wallet_id':     self.id,
            'type':          txn_type,
            'amount':        -amount,
            'description':   description or f'Debit EGP {amount:.2f}',
            'reference':     reference or '',
            'balance_after': self.balance,
        })

    def to_wallet_dict(self):
        self.ensure_one()
        loyalty = self.user_id.partner_id.cargo_loyalty_points or 0
        return {
            'balance':       self.balance,
            'currency':      self.currency or 'EGP',
            'loyaltyPoints': loyalty,
        }


class CargoWalletTransaction(models.Model):
    _name = 'cargo.wallet.transaction'
    _description = 'Cargo Wallet Transaction'
    _order = 'id desc'

    wallet_id = fields.Many2one(
        'cargo.wallet', 'Wallet',
        required=True, ondelete='cascade', index=True,
    )
    type = fields.Selection(
        WALLET_TRANSACTION_TYPES,
        string='Transaction Type',
        required=True,
    )
    amount = fields.Float('Amount (EGP)', required=True, digits=(10, 2),
                          help='Positive = credit, Negative = debit')
    description = fields.Char('Description')
    reference = fields.Char('Reference')
    balance_after = fields.Float('Balance After', digits=(10, 2))
    created_at = fields.Datetime('Date', default=fields.Datetime.now, readonly=True)

    def to_transaction_dict(self):
        self.ensure_one()
        return {
            'id':          self.id,
            'type':        self.type,
            'amount':      self.amount,
            'description': self.description or '',
            'reference':   self.reference or '',
            'createdAt':   self.created_at.isoformat() if self.created_at else None,
            'balanceAfter': self.balance_after,
        }
