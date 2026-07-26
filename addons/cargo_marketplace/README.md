# cargo_marketplace

Meta-module — installs the complete Cargo Marketplace platform with a single `odoo -i cargo_marketplace`.

## What it does

- Declares **all other Cargo modules** as dependencies
- Owns `cargo.marketplace.settings` — a singleton record holding platform-wide configuration
- Exposes `GET /api/settings` so the Flutter app can read platform config on startup

## Models

| Model | Description |
|---|---|
| `cargo.marketplace.settings` | Singleton — platform name, support contacts, fees, feature flags |

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/settings` | Public | Platform config for the Flutter app |

## Install command

```bash
odoo-bin -i cargo_marketplace -d mydb
```

## Dependencies

All 19 other Cargo modules.
