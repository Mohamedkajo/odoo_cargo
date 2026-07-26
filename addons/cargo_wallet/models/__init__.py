# -*- coding: utf-8 -*-
# cargo_wallet extends res.users with wallet balance and owns cargo.wallet.transaction.
# No standalone cargo.wallet model — balance lives on res.users.cargo_wallet_balance.
from . import res_users
