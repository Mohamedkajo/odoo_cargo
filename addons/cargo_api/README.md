# cargo_api — Cargo REST API Infrastructure

## Overview

`cargo_api` is the infrastructure layer for all Cargo Marketplace REST APIs.
It provides zero business logic of its own — every business endpoint
(`/api/v1/auth/*`, `/api/v1/stores/*`, `/api/v1/orders/*`, etc.) is
implemented by its respective Cargo module, which inherits from
`CargoBaseController`.

## Module Dependencies

```
cargo_base ← cargo_api ← cargo_auth
                       ← cargo_store
                       ← cargo_order
                       ← cargo_driver
                       ← cargo_notification
                       ← cargo_wallet
                       ← cargo_admin
```

## Architecture

### HTTP Controllers

All routes use `auth='none'` — JWT authentication is handled at the
application layer by the `@require_cargo_auth()` decorator or
by calling `_cargo_get_current_user()` directly.

```
GET  /api/v1/health        — Liveness probe (no auth)
GET  /api/v1/version       — API version info (no auth)
GET  /api/v1/openapi.json  — OpenAPI 3.0.3 specification (no auth)
GET  /api/v1/docs          — Swagger UI (no auth)
```

### Authentication Flow

```
Flutter App                    Odoo API Server
    │                               │
    │── POST /api/v1/auth/login ───▶│
    │                               │── verify password
    │                               │── generate access token (24h JWT)
    │                               │── generate refresh token (30d JWT)
    │                               │── store hashed refresh token in cargo.api.token
    │◀── { accessToken, refreshToken, user } ──│
    │                               │
    │── GET /api/v1/stores ────────▶│
    │   Authorization: Bearer <tok>  │
    │                               │── _cargo_check_rate_limit()
    │                               │── verify JWT signature
    │                               │── check not revoked
    │                               │── check user active
    │◀── { success: true, data: [...] } ──│
```

### JWT Token Structure

**Access Token payload:**
```json
{
  "sub": "42",
  "uid": 42,
  "role": "customer",
  "iss": "cargo.marketplace",
  "aud": "cargo.api",
  "iat": 1706745600,
  "exp": 1706832000,
  "type": "access"
}
```

**Refresh Token payload:**
```json
{
  "sub": "42",
  "uid": 42,
  "iss": "cargo.marketplace",
  "aud": "cargo.api",
  "iat": 1706745600,
  "exp": 1709337600,
  "type": "refresh"
}
```

Note: Refresh tokens intentionally carry no `role` claim — the role is
re-read from the database when a new access token is issued.

### Rate Limiting

Per-IP, per-minute request counting using atomic PostgreSQL UPSERTs.
Default limit: **60 requests/minute** (configurable via Cargo settings).

```
First request  → INSERT (ip, window, count=1)
Second request → UPDATE SET count = count + 1   (atomic, race-condition free)
```

Cleanup: expired windows (>1 hour old) are deleted by `ir.cron` hourly.

### Response Envelope

All responses follow the Flutter-compatible envelope defined in `cargo_base`:

```json
// Success
{ "success": true, "data": <payload>, "message": "Optional" }

// Paginated
{ "success": true, "data": [...], "pagination": { "page": 1, "limit": 20,
  "total": 154, "pages": 8, "hasNext": true, "hasPrev": false } }

// Error
{ "success": false, "error": "ERR_VALIDATION", "message": "Email is required.",
  "field": "email" }
```

### Pagination

Query parameters: `page`, `limit` (1-100), `sort` (prefix `-` for DESC), `q` (search)

```python
from cargo_api.utils.pagination import PaginationParams, build_pagination_meta

params = PaginationParams.from_request(allowed_sort_fields={'name', 'created_at'})
records = env['cargo.store'].search(domain, limit=params.limit, offset=params.offset,
                                    order=params.order_clause)
total   = env['cargo.store'].search_count(domain)
meta    = build_pagination_meta(total, params.page, params.limit)
```

### Writing a New Endpoint

```python
from odoo import http
from odoo.http import request
from cargo_api.controllers.base import CargoBaseController
from cargo_api.utils.decorators import require_cargo_auth
from cargo_base.utils.response import success, paginated, from_exception

class CargoStoreController(CargoBaseController):

    @http.route('/api/v1/stores', auth='none', methods=['GET'],
                type='http', csrf=False)
    @require_cargo_auth()   # any authenticated user
    def list_stores(self, **kwargs):
        from cargo_api.utils.pagination import PaginationParams, build_pagination_meta
        params = PaginationParams.from_request(
            allowed_sort_fields={'name', 'rating', 'created_at'}
        )
        domain = [('active', '=', True)]
        stores = request.env['cargo.store'].search(
            domain, limit=params.limit, offset=params.offset,
            order=params.order_clause or 'rating desc',
        )
        total = request.env['cargo.store'].search_count(domain)
        return paginated(
            [s.cargo_to_api_dict() for s in stores],
            total=total, page=params.page, limit=params.limit,
        )
```

### File Uploads

```python
from cargo_api.utils.upload import read_image_upload

@http.route('/api/v1/vendor/products/<int:product_id>/image',
            auth='none', methods=['POST'], type='http', csrf=False)
@require_cargo_auth('vendor', 'admin')
def upload_image(self, product_id, **kwargs):
    b64_data, mime_type = read_image_upload('image')
    product.write({'image_1920': b64_data})
    return success({'imageUrl': get_image_url(product, 'image_128')})
```

## Models

### `cargo.api.token`

Stores hashed refresh tokens for revocation.

| Field          | Type          | Description                              |
|----------------|---------------|------------------------------------------|
| `user_id`      | Many2one      | Token owner                              |
| `token_hash`   | Char (unique) | SHA-256 of raw refresh token             |
| `expires_at`   | Datetime      | Token expiry timestamp                   |
| `is_revoked`   | Boolean       | Explicitly revoked flag                  |
| `is_valid`     | Computed      | Not revoked AND not expired              |
| `ip_address`   | Char          | Issuing IP address                       |
| `device_info`  | Char          | Device name from client                  |

### `cargo.rate.limit`

Per-IP-per-minute request counter.

| Field           | Type     | Description                      |
|-----------------|----------|----------------------------------|
| `ip_address`    | Char     | Source IP                        |
| `window_start`  | Datetime | Minute bucket start time         |
| `request_count` | Integer  | Requests in this minute window   |

UNIQUE constraint on `(ip_address, window_start)`.

## Configuration

All config via Odoo → Cargo → Configuration → API Settings:

| Parameter                          | Default | Description                 |
|------------------------------------|---------|------------------------------|
| `cargo.rate_limit.requests_per_minute` | 60  | Per-IP rate limit            |
| `cargo.jwt.access_expiry_seconds`  | 86400   | Access token TTL (24 h)      |
| `cargo.jwt.refresh_expiry_seconds` | 2592000 | Refresh token TTL (30 d)     |

## OpenAPI / Swagger

- **Spec:** `GET /api/v1/openapi.json` — full OpenAPI 3.0.3 document
- **UI:** `GET /api/v1/docs` — Swagger UI (Swagger UI 5 from unpkg CDN)

Downstream modules extend the spec via:

```python
from cargo_api.utils.openapi import extend_cargo_openapi_spec

extend_cargo_openapi_spec(
    paths={'/stores/{id}/reviews': { ... }},
    schemas={'StoreReview': { ... }},
    tags=[{'name': 'Reviews', 'description': '...'}],
)
```

## Security

- **Transport:** All API traffic must be over HTTPS in production
- **Tokens:** Access tokens are stateless (not stored). Refresh tokens are stored as SHA-256 hashes only
- **Revocation:** Individual tokens revokable via `cargo.api.token`; all user tokens via `cargo_revoke_all_for_user()`
- **Rate limiting:** Per-IP atomic DB counters, race-condition free
- **Audit logging:** Every authenticated API call written to `cargo.audit.log`

## Admin UI

Accessible in Odoo backend under **Cargo → API Management**:

- **API Tokens** — view and revoke active refresh tokens
- **Rate Limit Monitor** — live traffic counters per IP
