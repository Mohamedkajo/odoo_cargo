# Cargo Marketplace — Module Reference

## Implemented Modules

### cargo_base `v18.0.1.0.0` ✅ Production-ready
**Foundation module — zero business endpoints.**

| Component | Description |
|-----------|-------------|
| `res.partner` extension | `cargo_role`, loyalty points, full address, API dict |
| `res.users` extension | FCM device token, unread count, `cargo_has_role()` |
| `product.template` extension | Discount, effective price, featured/trending flags, ratings |
| `product.category` extension | Slug (unique, auto-generated), icon, sort order |
| `sale.order` extension | 8-state machine, OTP, delivery fee, commission |
| `cargo.audit.log` | Append-only audit trail, immutable at Python level |
| `CargoTimestampMixin` | `created_at` (immutable) + `updated_at` (auto) |
| `CargoSoftDeleteMixin` | `active` field pattern, `restore()`, `hard_unlink()` |
| `CargoAuditMixin` | Auto-writes audit log on create/write/unlink |
| `jwt_utils` | HMAC-SHA256, verify, refresh, hash, no external deps |
| `validators` | Egyptian phone, email, password, OTP, pagination |
| `response` | Werkzeug JSON helpers: success, paginated, error |
| **Tests** | **121 tests, 22 classes** |

**Security**: 8 groups, 4-row ACL, 6 record rules, 11 config parameters

---

### cargo_api `v18.0.1.0.0` ✅ Production-ready
**REST API infrastructure — no business logic.**

| Component | Description |
|-----------|-------------|
| `CargoBaseController` | Base controller with auth, rate limit, logging helpers |
| `cargo.api.token` | Refresh token storage + revocation, SHA-256 hashed |
| `cargo.rate.limit` | Atomic per-IP-per-minute counter (PostgreSQL UPSERT) |
| `@require_cargo_auth()` | JWT auth + role check decorator for route methods |
| `PaginationParams` | `page`, `limit`, `sort`, `q`, `filter[field]=value` |
| `read_image_upload()` | Multipart upload validator (MIME, size, base64 encode) |
| OpenAPI 3.0.3 spec | 44 documented paths, 14 schemas, 11 tags |
| `GET /api/v1/health` | Liveness probe (DB ping) |
| `GET /api/v1/version` | API + Odoo version info |
| `GET /api/v1/openapi.json` | Full OpenAPI spec |
| `GET /api/v1/docs` | Swagger UI 5 |
| **Tests** | **58 tests, 6 classes** |

---

## Planned Modules

### cargo_auth `v18.0.1.0.0` 🔜 Next
**Authentication endpoints for all Flutter apps.**

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/auth/register` | Customer registration |
| `POST /api/v1/auth/login` | Login (returns access + refresh tokens) |
| `POST /api/v1/auth/refresh` | Rotate tokens |
| `POST /api/v1/auth/logout` | Revoke refresh token |
| `GET  /api/v1/auth/me` | Get profile |
| `PATCH /api/v1/auth/me` | Update profile |
| `PATCH /api/v1/auth/password` | Change password |
| `POST /api/v1/auth/avatar` | Upload avatar image |

---

### cargo_store `v18.0.1.0.0` 🔜
**Store and category management.**

Models: `cargo.store`, extends `product.category`
Endpoints: `/api/v1/stores`, `/api/v1/categories`, `/api/v1/stores/{id}/products`

---

### cargo_order `v18.0.1.0.0` 🔜
**Order lifecycle, OTP delivery, commissions.**

Endpoints: `/api/v1/orders`, `/api/v1/orders/{id}`, `/api/v1/orders/{id}/cancel`,
`/api/v1/orders/{id}/rate`, `/api/v1/orders/{id}/track`

---

### cargo_driver `v18.0.1.0.0` 🔜
**Driver profiles and delivery workflow.**

Models: `cargo.driver`, `cargo.driver.location`
Endpoints: `/api/v1/driver/*`

---

### cargo_wallet `v18.0.1.0.0` 🔜
**Digital wallet and transaction history.**

Models: `cargo.wallet`, `cargo.wallet.transaction`
Endpoints: `/api/v1/wallet`, `/api/v1/wallet/history`

---

### cargo_notification `v18.0.1.0.0` 🔜
**FCM push notifications.**

Models: `cargo.notification`
Endpoints: `/api/v1/notifications`, `/api/v1/notifications/{id}/read`

---

### cargo_admin `v18.0.1.0.0` 🔜
**Platform analytics and admin API.**

Endpoints: `/api/v1/admin/*`

---

### cargo_marketplace `v18.0.1.0.0` 🔜
**Meta-module that installs the complete Cargo suite.**
Depends on all other cargo modules.

## Test Summary

| Module | Classes | Tests | Status |
|--------|:-------:|:-----:|--------|
| cargo_base | 22 | 121 | ✅ |
| cargo_api | 6 | 58 | ✅ |
| **Total** | **28** | **179** | |
