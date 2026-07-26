# -*- coding: utf-8 -*-
"""cargo_wallet — wallet model tests."""
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestCargoWallet(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env['res.users'].sudo().create({
            'name': 'Wallet User', 'login': 'walletuser@cargo.test',
            'email': 'walletuser@cargo.test', 'password': 'Test1234!', 'cargo_role': 'customer',
        })

    def _get_wallet(self):
        wallet = self.env['cargo.wallet'].sudo().search(
            [('user_id', '=', self.user.id)], limit=1
        )
        if not wallet:
            wallet = self.env['cargo.wallet'].sudo().create({'user_id': self.user.id})
        return wallet

    def test_topup_increases_balance(self):
        wallet = self._get_wallet()
        before = wallet.balance
        wallet.topup(amount=500.0, description='Test top-up')
        self.assertAlmostEqual(wallet.balance, before + 500.0)

    def test_debit_decreases_balance(self):
        wallet = self._get_wallet()
        wallet.topup(amount=300.0, description='Seed balance')
        before = wallet.balance
        wallet.debit(amount=100.0, description='Test purchase', tx_type='purchase')
        self.assertAlmostEqual(wallet.balance, before - 100.0)

    def test_debit_raises_if_insufficient_funds(self):
        wallet = self._get_wallet()
        wallet.write({'balance': 0.0})
        with self.assertRaises(Exception):
            wallet.debit(amount=100.0, description='Should fail', tx_type='purchase')

    def test_balance_non_negative_constraint(self):
        with self.assertRaises(Exception):
            self.env['cargo.wallet'].sudo().create({
                'user_id': self.user.id, 'balance': -50.0,
            })
