# -*- coding: utf-8 -*-
"""cargo_wallet — wallet model tests.

Wallet balance is a field on res.users (cargo_wallet_balance).
Transactions are cargo.wallet.transaction records keyed by user_id.
"""
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestCargoWallet(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env['res.users'].sudo().create({
            'name':       'Wallet User',
            'login':      'walletuser@cargo.test',
            'email':      'walletuser@cargo.test',
            'password':   'Test1234!',
            'cargo_role': 'customer',
        })

    def test_initial_balance_is_zero(self):
        self.assertEqual(self.user.cargo_wallet_balance, 0.0)

    def test_credit_increases_balance(self):
        self.user.sudo().write({'cargo_wallet_balance': 0.0})
        self.user.cargo_wallet_credit(500.0, note='Test top-up')
        self.assertAlmostEqual(self.user.cargo_wallet_balance, 500.0)

    def test_debit_decreases_balance(self):
        self.user.sudo().write({'cargo_wallet_balance': 300.0})
        self.user.cargo_wallet_debit(100.0, note='Test purchase')
        self.assertAlmostEqual(self.user.cargo_wallet_balance, 200.0)

    def test_debit_raises_if_insufficient_funds(self):
        self.user.sudo().write({'cargo_wallet_balance': 0.0})
        with self.assertRaises(UserError):
            self.user.cargo_wallet_debit(100.0, note='Should fail')

    def test_credit_creates_transaction(self):
        before = self.env['cargo.wallet.transaction'].sudo().search_count(
            [('user_id', '=', self.user.id)]
        )
        self.user.cargo_wallet_credit(50.0, note='Tx test')
        after = self.env['cargo.wallet.transaction'].sudo().search_count(
            [('user_id', '=', self.user.id)]
        )
        self.assertEqual(after, before + 1)

    def test_transaction_dict_shape(self):
        self.user.sudo().write({'cargo_wallet_balance': 200.0})
        self.user.cargo_wallet_debit(50.0, note='Dict test')
        tx = self.env['cargo.wallet.transaction'].sudo().search(
            [('user_id', '=', self.user.id)], order='id desc', limit=1,
        )
        d = tx.to_tx_dict()
        for key in ('id', 'type', 'amount', 'balanceAfter', 'note'):
            self.assertIn(key, d, f'Missing key: {key}')
