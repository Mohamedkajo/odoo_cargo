# cargo_wallet

Digital wallet — top-up, balance management, and transaction history for Cargo customers.

## Models

| Model | Description |
|---|---|
| `cargo.wallet` | One wallet per user — non-negative balance, unique constraint |
| `cargo.wallet.transaction` | Immutable transaction log — topup, purchase, refund, reward, etc. |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/wallet` | Get wallet balance and summary |
| GET | `/api/wallet/transactions` | Transaction history |
| POST | `/api/wallet/topup` | Add funds (max EGP 10,000 per transaction) |

## Dependencies

`cargo_auth`
