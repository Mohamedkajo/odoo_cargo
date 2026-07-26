# Cargo Marketplace — System Architecture

## Overview

Cargo is a multi-vendor delivery marketplace built on **Odoo 18 Community**, targeting the Egyptian market (comparable to Talabat / Uber Eats).

The system is composed of three layers:

```
┌──────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
│   Flutter Customer App   Flutter Vendor App   Flutter Driver App │
│   (existing, frozen)      (to be built)        (to be built)    │
└───────────────────────────────┬─────────────────────────────────┘
                                │  REST API  /api/v1/*
┌───────────────────────────────▼─────────────────────────────────┐
│                        API LAYER                                │
│   cargo_api  ← JWT auth, rate limiting, OpenAPI spec           │
│   cargo_auth ← register/login/refresh/logout endpoints         │
│   Module-specific controllers (cargo_store, cargo_order, ...)  │
└───────────────────────────────┬─────────────────────────────────┘
                                │  Odoo ORM
┌───────────────────────────────▼─────────────────────────────────┐
│                       BUSINESS LAYER                            │
│   cargo_base       ← models, security, audit, JWT utils        │
│   cargo_store      ← vendor stores, menus, categories          │
│   cargo_order      ← order lifecycle, OTP, commissions         │
│   cargo_driver     ← driver profiles, delivery workflow        │
│   cargo_wallet     ← digital wallets, transactions             │
│   cargo_notification← FCM push notifications                   │
│   cargo_admin      ← platform analytics, admin dashboards      │
└───────────────────────────────┬─────────────────────────────────┘
                                │  PostgreSQL
┌───────────────────────────────▼─────────────────────────────────┐
│                         DATA LAYER                              │
│   Odoo native models (res.partner, sale.order, product, ...)   │
│   Custom Cargo models (cargo.store, cargo.wallet, ...)         │
└─────────────────────────────────────────────────────────────────┘
```

## Module Dependency Graph

```
base ← mail ← product ← sale ← sale_management ← stock ← account
                                        │
                              cargo_base (v18.0.1.0.0)
                              ├─ models: res.partner, res.users,
                              │          sale.order, product.template,
                              │          product.category, cargo.audit.log
                              ├─ utils: jwt_utils, validators, response,
                              │         logging_utils, image_utils
                              └─ mixins: timestamp, soft_delete, audit
                                        │
                              cargo_api (v18.0.1.0.0)
                              ├─ models: cargo.api.token, cargo.rate.limit
                              ├─ controllers: CargoBaseController
                              ├─ utils: decorators, pagination, upload,
                              │         openapi
                              └─ routes: /api/v1/health, /version,
                                         /openapi.json, /docs
                                        │
                    ┌───────────────────┴────────────────────┐
                    │                                        │
              cargo_auth                              cargo_store
              ├─ /api/v1/auth/*                      ├─ cargo.store model
              └─ register, login,                    ├─ /api/v1/stores/*
                 refresh, logout                     └─ /api/v1/categories/*
                    │                                        │
                    └───────────────────┬────────────────────┘
                                        │
                              cargo_order
                              ├─ order lifecycle (8 statuses)
                              ├─ OTP delivery verification
                              ├─ commission engine
                              └─ /api/v1/orders/*
                                        │
                    ┌───────────────────┴────────────────────┐
                    │                                        │
              cargo_driver                           cargo_wallet
              ├─ cargo.driver model                  ├─ cargo.wallet model
              ├─ delivery workflow                   ├─ transactions
              └─ /api/v1/driver/*                    └─ /api/v1/wallet/*
                                        │
                              cargo_notification
                              ├─ cargo.notification model
                              ├─ FCM integration
                              └─ /api/v1/notifications/*
                                        │
                              cargo_admin
                              ├─ analytics dashboards
                              └─ /api/v1/admin/*
```

## Key Design Decisions

### 1. Native Odoo Security as Primary Authorization
All data access is controlled by Odoo's native security system:
- **8 Security Groups**: `super_admin → admin → (operations, finance)`, `vendor_manager → vendor`, `customer`, `driver`
- **ACLs** (`ir.model.access.csv`) define CRUD permissions per group
- **Record Rules** restrict row-level access (customers see only their own records)
- `cargo_has_role()` on `res.users` is a UI helper only — not a security gate

### 2. JWT Authentication (Stateless + Revocable)
- **Access tokens**: short-lived (24h), stateless JWTs — not stored in DB
- **Refresh tokens**: long-lived (30d), hashed SHA-256 — stored in `cargo.api.token` for revocation
- **Algorithm**: HMAC-SHA256 via Python stdlib (no external dependency)
- **Secret**: 512-bit CSPRNG via `secrets.token_hex(64)`, generated on install
- **Security**: `hmac.compare_digest` for timing-attack resistance

### 3. Odoo-Native Soft Delete
Uses Odoo's built-in `active` field pattern — no `search()` override needed.
- `active = False` → soft-deleted (hidden from all standard searches)
- `is_deleted` → computed alias for `not active` (API convenience)
- `restore()` sets `active = True`
- `hard_unlink()` available to superusers only

### 4. Immutable Audit Log
`cargo.audit.log` is append-only at the Python level:
- `write()` raises `AccessError`
- `unlink()` raises `AccessError`
- `_log_access = False` (no tracking columns)
- ACL: read + create only (no write/unlink grants anywhere)
- No recursion: `cargo.audit.log` does NOT inherit `cargo.audit.mixin`

### 5. Rate Limiting (Atomic, Multi-Worker Safe)
Per-IP-per-minute counters using PostgreSQL `ON CONFLICT DO UPDATE`:
```sql
INSERT INTO cargo_rate_limit (ip, window, count) VALUES (?, ?, 1)
ON CONFLICT (ip, window) DO UPDATE SET count = count + 1
RETURNING count
```
Race-condition free across all Odoo worker processes.

### 6. Multi-Company / Multi-Store Expansion
- All extended native models (`sale.order`, `res.partner`, etc.) already have Odoo's `company_id`
- `cargo_store_id` / `cargo_driver_id` are Integer FKs in `cargo_base`, upgraded to proper `Many2one` by `cargo_store` / `cargo_driver` modules (avoids forward-reference errors)
- No schema changes needed to add multi-company support later

## API Design

### Response Envelope (Flutter-compatible)
```json
// Success
{"success": true, "data": <payload>}

// Paginated
{"success": true, "data": [...], "pagination": {"page": 1, "limit": 20, "total": 154, "pages": 8, "hasNext": true, "hasPrev": false}}

// Error
{"success": false, "error": "ERR_VALIDATION", "message": "Email is required.", "field": "email"}
```

### Authentication Flow
```
POST /api/v1/auth/login → {accessToken, refreshToken, user}
GET  /api/v1/stores     Authorization: Bearer <accessToken>
POST /api/v1/auth/refresh {refreshToken} → {accessToken, refreshToken, user}
POST /api/v1/auth/logout  → revokes refreshToken in cargo.api.token
```

### Pagination
```
GET /api/v1/stores?page=2&limit=20&sort=-rating&q=burger&filter[isOpen]=true
```
