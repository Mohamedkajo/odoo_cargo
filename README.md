# 🚚 Cargo Marketplace — Odoo 18 Backend

A multi-vendor delivery marketplace backend built on **Odoo 18 Community**, targeting the Egyptian market. Comparable to Talabat / Uber Eats.

[![Odoo](https://img.shields.io/badge/Odoo-18.0-875A7B?logo=odoo)](https://www.odoo.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791?logo=postgresql)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-LGPL--3-blue)](LICENSE)

---

## Overview

Cargo replaces a Node.js/Express backend with a fully native Odoo 18 implementation, providing:

- **REST API** (`/api/v1/*`) compatible with the existing Flutter Customer App — zero Flutter UI changes
- **Odoo Admin Backend** — replaces a custom React admin dashboard
- **Vendor App API** — new Flutter Vendor App (to be built)
- **Driver App API** — new Flutter Driver App (to be built)

---

## Quick Start

### Docker (Development)

```bash
git clone https://github.com/Mohamedkajo/odoo_cargo.git
cd odoo_cargo
cp .env.example .env          # edit passwords
docker compose up -d
# Open http://localhost:8069
```

### Ubuntu Server (Production)

```bash
git clone https://github.com/Mohamedkajo/odoo_cargo.git
cd odoo_cargo
sudo bash install.sh
```

---

## Repository Structure

```
odoo_cargo/
├── addons/                  # Cargo custom Odoo modules
│   ├── cargo_base/          # ✅ Foundation: models, security, JWT, utils
│   └── cargo_api/           # ✅ REST API: auth middleware, pagination, OpenAPI
│   # (further modules added as development progresses)
│
├── config/
│   └── odoo.conf            # Docker Odoo configuration
│
├── docs/
│   ├── architecture.md      # System architecture and design decisions
│   ├── modules.md           # Module reference and status
│   └── deployment.md        # Deployment guide (Docker + bare-metal)
│
├── scripts/
│   ├── update_modules.sh    # Upgrade Odoo modules safely
│   ├── create_db.sh         # Fresh database initialisation
│   └── backup.sh            # Timestamped PostgreSQL backup
│
├── tests/
│   └── run_tests.sh         # Run Cargo test suites via Odoo test runner
│
├── .env.example             # Environment variable template
├── .gitignore
├── docker-compose.yml       # Docker: Odoo 18 + PostgreSQL 15 + pgAdmin
├── install.sh               # One-shot Ubuntu installer
├── odoo.conf.example        # Odoo configuration template (bare-metal)
├── requirements.txt         # Python dependencies
└── README.md
```

---

## Modules

| Module | Version | Status | Description |
|--------|---------|--------|-------------|
| `cargo_base` | 18.0.1.0.0 | ✅ Done | Models, security groups, JWT utils, audit log, mixins |
| `cargo_api` | 18.0.1.0.0 | ✅ Done | HTTP controller base, rate limiting, OpenAPI spec, pagination |
| `cargo_auth` | 18.0.1.0.0 | 🔜 Next | Auth endpoints: register, login, refresh, logout, profile |
| `cargo_store` | 18.0.1.0.0 | 🔜 Planned | Stores, categories, menus |
| `cargo_order` | 18.0.1.0.0 | 🔜 Planned | Orders, OTP, commissions |
| `cargo_driver` | 18.0.1.0.0 | 🔜 Planned | Driver profiles, delivery workflow |
| `cargo_wallet` | 18.0.1.0.0 | 🔜 Planned | Digital wallet, transactions |
| `cargo_notification` | 18.0.1.0.0 | 🔜 Planned | FCM push notifications |
| `cargo_admin` | 18.0.1.0.0 | 🔜 Planned | Analytics, admin API |
| `cargo_marketplace` | 18.0.1.0.0 | 🔜 Planned | Meta-module (installs all) |

---

## API Endpoints

| Route | Auth | Description |
|-------|------|-------------|
| `GET /api/v1/health` | None | Liveness probe |
| `GET /api/v1/version` | None | API version info |
| `GET /api/v1/openapi.json` | None | OpenAPI 3.0.3 spec |
| `GET /api/v1/docs` | None | Swagger UI |
| `POST /api/v1/auth/register` | None | Customer registration |
| `POST /api/v1/auth/login` | None | Login → JWT tokens |
| `GET /api/v1/stores` | Bearer | Store list |
| `GET /api/v1/orders` | Bearer | Customer orders |
| `POST /api/v1/orders` | Bearer | Place order |
| `GET /api/v1/vendor/orders` | Bearer (vendor) | Vendor order queue |
| `GET /api/v1/driver/orders` | Bearer (driver) | Driver delivery queue |
| *(44 documented endpoints — see /api/v1/docs)* | | |

---

## Architecture Highlights

- **JWT Auth**: HMAC-SHA256 via Python stdlib — zero external deps, timing-attack resistant
- **Odoo-native security**: 8 groups, ACLs, record rules — no custom role checks in business logic
- **Rate limiting**: Atomic PostgreSQL `ON CONFLICT DO UPDATE` — safe across all Odoo workers
- **Audit log**: Append-only, immutable at Python level (`write()`/`unlink()` raise `AccessError`)
- **Soft delete**: Odoo-native `active` field — no `search()` override, works with Odoo's ORM automatically
- **Multi-company ready**: All models use native `company_id`; Integer FK placeholders upgraded to `Many2one` by their respective modules

→ See [docs/architecture.md](docs/architecture.md) for the complete architecture document.

---

## Test Coverage

```
cargo_base:  121 tests  (22 classes)
cargo_api:    58 tests  ( 6 classes)
─────────────────────────────────
Total:       179 tests  (28 classes)
```

Run all tests:
```bash
./tests/run_tests.sh
```

---

## Flutter App Compatibility

The existing Flutter Customer App requires **only one change**: update the API base URL in `lib/core/config/api_config.dart`. All endpoint paths and JSON response shapes are preserved from the original Node.js API.

---

## Development Workflow

```bash
# Clone
git clone https://github.com/Mohamedkajo/odoo_cargo.git

# Start Docker environment
docker compose --profile dev up -d    # includes pgAdmin at :5050

# Make changes to addons/cargo_*/
# ...

# Update modules in running Odoo
./scripts/update_modules.sh cargo_base

# Run tests
./tests/run_tests.sh cargo_base

# Commit
git add addons/cargo_base/
git commit -m "feat(cargo_base): add store category slug validation"
git push
```

---

## Contributing

1. Create a feature branch: `git checkout -b feat/cargo-store-model`
2. Make changes inside `addons/`
3. Run tests: `./tests/run_tests.sh`
4. Commit with conventional commits: `feat:`, `fix:`, `docs:`, `test:`
5. Push and open a PR

---

## License

LGPL-3.0 — see [LICENSE](LICENSE) file.
