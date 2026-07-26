# cargo_reports

Analytics, revenue reports, and admin statistics for the Cargo Marketplace.

## Models

None — all data is aggregated from `cargo.order`, `cargo.wallet.transaction`, and `cargo.store` using ORM queries.

## Admin API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/admin/reports/summary` | Admin JWT | Key platform metrics (orders, revenue, customers, stores) |
| GET | `/api/admin/reports/orders?days=30` | Admin JWT | Orders grouped by day for the last N days |

## Odoo Backend Views

- **Order Analytics** — bar chart and pivot of orders by day and status
- **Wallet Analytics** — pivot of wallet transactions by type

## Dependencies

`cargo_order` → `cargo_wallet` → `cargo_store`
