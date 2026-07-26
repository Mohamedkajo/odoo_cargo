# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
REMOVED: cargo.wallet custom model.

The standalone cargo.wallet model was removed as part of the Native Odoo First
refactoring.  Wallet fields are now on res.users:
  * res.users.cargo_wallet_balance    — current balance (Monetary)
  * res.users.cargo_wallet_credit()   — add funds helper
  * res.users.cargo_wallet_debit()    — deduct funds helper (raises on insufficient balance)

Transaction history is in cargo.wallet.transaction (defined in res_users.py),
keyed by user_id instead of wallet_id.

This file is kept as a tombstone to aid git blame readability.
Do not re-add any model definitions here.
"""
