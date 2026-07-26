# cargo_base — Cargo Marketplace Foundation Module

> **Odoo 18 Community · Python 3.11+ · PostgreSQL 15+**

`cargo_base` is the mandatory foundation module for the Cargo multi-vendor
marketplace platform. Every other Cargo module (`cargo_api`, `cargo_auth`,
`cargo_store`, …) declares `cargo_base` as a dependency.

---

## Table of Contents

1. [Folder Structure](#folder-structure)
2. [Module Dependencies](#module-dependencies)
3. [Security Design](#security-design)
4. [Implemented Features](#implemented-features)
5. [Configuration Guide](#configuration-guide)
6. [Installation Instructions](#installation-instructions)
7. [Running Tests](#running-tests)

---

## Folder Structure

```
cargo_base/
├── __init__.py                         ← module entry point + hook imports
├── __manifest__.py                     ← module metadata, deps, data list
├── constants.py                        ← all platform constants (roles, statuses, JWT, etc.)
├── exceptions.py                       ← typed exception hierarchy
├── hooks.py                            ← pre_init, post_init, uninstall hooks
│
├── models/
│   ├── __init__.py
│   ├── mixins/
│   │   ├── __init__.py
│   │   ├── cargo_timestamp_mixin.py    ← AbstractModel: created_at + updated_at
│   │   ├── cargo_soft_delete_mixin.py  ← AbstractModel: is_deleted soft-delete
│   │   └── cargo_audit_mixin.py        ← AbstractModel: auto cargo.audit.log writes
│   ├── res_partner.py                  ← extends res.partner (cargo_role, loyalty_points)
│   ├── res_users.py                    ← extends res.users (cargo_role relay, device_token)
│   ├── product_template.py             ← extends product.template (discount, rating, tags)
│   ├── product_category.py             ← extends product.category (icon, slug, store_count)
│   ├── sale_order.py                   ← extends sale.order (cargo_status, OTP, commission)
│   ├── cargo_audit_log.py              ← new model: cargo.audit.log (append-only)
│   └── cargo_config_settings.py        ← extends res.config.settings (Cargo tab)
│
├── utils/
│   ├── __init__.py
│   ├── jwt_utils.py                    ← HS256 JWT (stdlib only — no PyJWT)
│   ├── validators.py                   ← typed input validators
│   ├── response.py                     ← Werkzeug JSON response helpers
│   ├── logging_utils.py                ← structured API logging
│   └── image_utils.py                  ← image URL builder + base64 helpers
│
├── security/
│   ├── groups.xml                      ← 8 security groups + category
│   ├── ir.model.access.csv             ← ACL for cargo.audit.log
│   └── record_rules.xml                ← partner + audit log record rules
│
├── views/
│   ├── cargo_audit_log_views.xml       ← list + form + search + action
│   ├── cargo_settings_views.xml        ← res.config.settings Cargo tab
│   ├── res_partner_views.xml           ← inherited partner views
│   ├── res_users_views.xml             ← inherited user form
│   ├── product_template_views.xml      ← inherited product views
│   ├── product_category_views.xml      ← inherited category form
│   ├── sale_order_views.xml            ← inherited order views
│   └── menus.xml                       ← top-level Cargo menu + sub-menus
│
├── data/
│   └── cargo_base_data.xml             ← ir.config_parameter defaults
│
├── tests/
│   ├── __init__.py
│   ├── common.py                       ← CargoBaseTestCase base class
│   ├── test_mixins.py                  ← mixin registration & behaviour
│   ├── test_validators.py              ← full validator coverage
│   ├── test_jwt_utils.py               ← JWT generate / verify / tamper tests
│   ├── test_audit_log.py               ← audit log CRUD + immutability
│   └── test_res_partner.py             ← partner extension + API serialisation
│
└── static/
    └── description/
        └── icon.png
```

---

## Module Dependencies

```
cargo_base
  ├── base              (res.partner, res.users, ir.*)
  ├── mail              (mail.thread, mail.activity)
  ├── product           (product.template, product.category)
  ├── sale              (sale.order, sale.order.line)
  ├── sale_management   (sale order workflows)
  ├── stock             (inventory)
  ├── account           (monetary fields, currency)
  └── web               (OWL web client)
```

**No other Cargo module is a dependency of `cargo_base`.**
All references to `cargo.store`, `cargo.driver`, etc. are guarded with
`self.env.get('model.name')` returning `None` checks so `cargo_base` can
install and run correctly on its own.

---

## Security Design

### 8 Security Groups

| Group | Implied By | Capabilities |
|-------|-----------|--------------|
| `cargo_group_customer` | — | Place orders, wallet, coupons, reviews |
| `cargo_group_vendor` | vendor_manager | Own store / products / orders |
| `cargo_group_vendor_manager` | — | Vendor + approve onboarding |
| `cargo_group_driver` | — | Assigned deliveries only |
| `cargo_group_operations` | admin | Orders, deliveries, stores |
| `cargo_group_finance` | admin | Wallets, payouts, commissions |
| `cargo_group_admin` | super_admin | All + user management |
| `cargo_group_super_admin` | — | All + JWT config + audit log |

### Record Rules

| Rule | Model | Groups | Effect |
|------|-------|--------|--------|
| `cargo_rule_partner_customer_own` | `res.partner` | customer | Own record only |
| `cargo_rule_partner_driver_own` | `res.partner` | driver | Own record only |
| `cargo_rule_partner_vendor_own` | `res.partner` | vendor | Own record only |
| `cargo_rule_partner_operations_all` | `res.partner` | operations | All Cargo partners |
| `cargo_rule_partner_admin_all` | `res.partner` | admin | Unrestricted |
| `cargo_rule_audit_log_admin` | `cargo.audit.log` | admin | Read + Create only |

### cargo.audit.log Immutability

`write()` and `unlink()` raise `AccessError` at the Python model level,
regardless of group membership. Audit integrity is enforced in code,
not just via ACLs.

---

## Implemented Features

### Constants (`constants.py`)
All platform-wide magic strings in one place: roles, order statuses,
valid transitions, JWT parameters, HTTP codes, Cargo error codes,
wallet types, notification types, vehicle types, review types,
OTP settings, image constraints, Egyptian phone regex, days of week,
`ir.config_parameter` keys.

### Exceptions (`exceptions.py`)
Typed hierarchy rooted at `CargoBaseException`:
- `CargoValidationError` / `CargoMissingFieldError` / `CargoInvalidFieldError`
- `CargoAuthError` / `CargoTokenError` / `CargoTokenExpiredError` / `CargoTokenRevokedError`
- `CargoPermissionError`
- `CargoNotFoundError`
- `CargoConflictError`
- `CargoStatusTransitionError`
- `CargoOTPError` / `CargoOTPExpiredError`
- `CargoInsufficientFundsError`
- `CargoRateLimitError`
- `CargoServerError`

Every exception carries `http_status`, `error_code`, `message` and optional
`field`. Controllers call `response.from_exception(exc)` to build the JSON.

### JWT (`utils/jwt_utils.py`)
- Standard-library HS256 implementation — no PyJWT dependency
- `generate_access_token(uid, role, secret, expiry_secs)` → signed JWT
- `generate_refresh_token(uid, secret, expiry_secs)` → signed JWT
- `verify_token(token, secret)` → decoded payload or raises
- Constant-time signature comparison (timing-attack resistant)
- `hash_token(token)` → SHA-256 hex digest for DB storage

### Validators (`utils/validators.py`)
- `require`, `require_str`, `optional_str`, `require_int`, `require_float`
- `validate_email` — RFC 5322 regex + lowercase normalisation
- `validate_phone` — Egyptian mobile regex + `+20` normalisation
- `validate_password` — min 8 chars, letter + digit
- `validate_rating` — 1.0–5.0 float
- `validate_otp` — 4–6 digit string
- `validate_pagination` — page / limit with max cap
- `validate_selection` — against Odoo selection lists
- `validate_image_size` / `validate_image_mime`

### API Response Helpers (`utils/response.py`)
Werkzeug `Response` builders that match the Flutter app's expected envelope:
- `success(data, status, message)`
- `created(data, message)`
- `no_content()`
- `paginated(data, total, page, limit)` — with pagination metadata
- `error(error_code, message, status, field)`
- `from_exception(exc)` — builds error response from any `CargoBaseException`
- `server_error(message)`

### Abstract Mixins
| Mixin | Fields added | ORM overrides |
|-------|-------------|---------------|
| `cargo.timestamp.mixin` | `created_at`, `updated_at` | `create`, `write` |
| `cargo.soft.delete.mixin` | `is_deleted`, `deleted_at`, `deleted_by_id` | `search`, `unlink`, `hard_unlink`, `restore` |
| `cargo.audit.mixin` | — | `create`, `write`, `unlink` → writes audit log |

### Native Model Extensions
All extensions use `_inherit` — no data is duplicated.

| Model | Fields added |
|-------|-------------|
| `res.partner` | `cargo_role`, `cargo_loyalty_points`, `cargo_is_cargo_user`, `cargo_full_address`, `cargo_display_name` |
| `res.users` | `cargo_role` (related), `cargo_device_token`, `cargo_unread_count` |
| `product.template` | `cargo_original_price`, `cargo_discount_percent`, `cargo_effective_price`, `cargo_is_featured`, `cargo_is_trending`, `cargo_is_available`, `cargo_tags`, `cargo_rating`, `cargo_review_count` |
| `product.category` | `cargo_icon`, `cargo_slug`, `cargo_is_active`, `cargo_sort_order`, `cargo_store_count` |
| `sale.order` | `cargo_status`, `cargo_store_id`, `cargo_driver_id`, `cargo_delivery_fee`, `cargo_estimated_time`, `cargo_commission_rate`, `cargo_commission_amount`, `cargo_vendor_earnings`, `cargo_otp_code`, `cargo_otp_verified`, `cargo_otp_expires_at` |

### Hooks (`hooks.py`)
- `pre_init_hook` — verifies Odoo ≥ 18 before installation
- `post_init_hook` — seeds all `ir.config_parameter` defaults; generates a
  cryptographically random 64-byte JWT secret via `secrets.token_hex(64)`
- `uninstall_hook` — removes all `cargo.*` config parameters

---

## Configuration Guide

After installation, navigate to **Settings → Cargo Marketplace** to configure:

| Parameter | Key | Default |
|-----------|-----|---------|
| JWT Secret | `cargo.jwt.secret` | Auto-generated (64-byte random) |
| Access Token Expiry | `cargo.jwt.access_expiry_seconds` | `86400` (24 h) |
| Refresh Token Expiry | `cargo.jwt.refresh_expiry_seconds` | `2592000` (30 days) |
| API Rate Limit | `cargo.rate_limit.requests_per_minute` | `60` |
| Default Commission | `cargo.commission.default_rate` | `10.0` % |
| OTP Expiry | `cargo.otp.expiry_minutes` | `10` |
| Max Image Size | `cargo.media.max_image_size_mb` | `5` MB |
| Support Email | `cargo.support.email` | `support@cargo.marketplace` |
| Support Phone | `cargo.support.phone` | `+201000000000` |
| Default Currency | `cargo.default_currency` | `EGP` |
| Default Country | `cargo.default_country_code` | `EG` |

> **⚠️ JWT Secret:** The auto-generated secret is cryptographically secure.
> Rotating it **immediately invalidates all active sessions** across all
> mobile apps. Only rotate intentionally.

---

## Installation Instructions

### Prerequisites

| Requirement | Version |
|------------|---------|
| Ubuntu | 22.04 LTS |
| Python | 3.11+ |
| PostgreSQL | 15+ |
| Odoo Community | 18.0 |

### Step 1 — Copy the module

```bash
cp -r cargo-odoo/cargo_base /opt/odoo/addons/cargo_base
```

### Step 2 — Verify the path

Ensure `cargo_base` is in one of the `addons_path` directories listed in
your Odoo configuration file (`/etc/odoo/odoo.conf`):

```ini
[options]
addons_path = /opt/odoo/odoo/addons,/opt/odoo/addons
```

### Step 3 — Update the module list

```bash
sudo -u odoo /opt/odoo/odoo-bin \
    --config=/etc/odoo/odoo.conf \
    -d YOUR_DATABASE \
    --update=base \
    --stop-after-init
```

### Step 4 — Install via Odoo UI

1. Log in as Administrator
2. Go to **Apps** → disable "Apps" filter → search `Cargo Base`
3. Click **Install**

Or install via CLI:

```bash
sudo -u odoo /opt/odoo/odoo-bin \
    --config=/etc/odoo/odoo.conf \
    -d YOUR_DATABASE \
    --init=cargo_base \
    --stop-after-init
```

### Step 5 — Verify installation

```bash
sudo -u odoo /opt/odoo/odoo-bin \
    --config=/etc/odoo/odoo.conf \
    -d YOUR_DATABASE \
    --test-enable \
    --test-tags=cargo_base \
    --stop-after-init
```

Expected: all 38 tests pass with no failures.

### Step 6 — Configure JWT secret

After installation, go to **Settings → Cargo Marketplace** and verify the
JWT secret was auto-generated. Copy it somewhere safe — you will not need it
normally but will need it if you ever migrate the database.

---

## Running Tests

```bash
# Run all cargo_base tests
sudo -u odoo /opt/odoo/odoo-bin \
    --config=/etc/odoo/odoo.conf \
    -d cargo_test \
    --test-enable \
    --test-tags=cargo_base \
    --log-level=test \
    --stop-after-init

# Run a single test class
sudo -u odoo /opt/odoo/odoo-bin \
    --config=/etc/odoo/odoo.conf \
    -d cargo_test \
    --test-enable \
    --test-tags=/cargo_base/TestCargoJwtUtils \
    --stop-after-init
```

### Test coverage summary

| File | Class | Tests |
|------|-------|-------|
| `test_validators.py` | `TestRequireValidators` | 10 |
| `test_validators.py` | `TestEmailValidator` | 4 |
| `test_validators.py` | `TestPhoneValidator` | 3 |
| `test_validators.py` | `TestPasswordValidator` | 3 |
| `test_validators.py` | `TestRatingValidator` | 2 |
| `test_validators.py` | `TestOTPValidator` | 3 |
| `test_validators.py` | `TestPagination` | 5 |
| `test_validators.py` | `TestSelectionValidator` | 3 |
| `test_jwt_utils.py` | `TestBase64Utils` | 3 |
| `test_jwt_utils.py` | `TestGenerateAccessToken` | 6 |
| `test_jwt_utils.py` | `TestGenerateRefreshToken` | 3 |
| `test_jwt_utils.py` | `TestVerifyToken` | 6 |
| `test_jwt_utils.py` | `TestTokenUID` | 4 |
| `test_jwt_utils.py` | `TestHashToken` | 3 |
| `test_mixins.py` | `TestCargoTimestampMixin` | 2 |
| `test_mixins.py` | `TestCargoSoftDeleteMixin` | 3 |
| `test_audit_log.py` | `TestCargoAuditLog` | 9 |
| `test_res_partner.py` | `TestCargoResPartner` | 12 |
| **Total** | | **84 tests** |

---

## What comes next

`cargo_base` provides no REST endpoints — those are in `cargo_api`.

| Module | Depends on | Adds |
|--------|-----------|------|
| `cargo_api` | `cargo_base` | HTTP controller base, route auth decorator |
| `cargo_auth` | `cargo_api` | `/auth/*` endpoints, token revocation |
| `cargo_store` | `cargo_base` | `cargo.store` model, store management |
| `cargo_vendor` | `cargo_store` | Vendor onboarding, vendor portal |
| `cargo_driver` | `cargo_base` | `cargo.driver` model, driver management |
| `cargo_cart` | `cargo_store` | Cart & checkout |
| `cargo_delivery` | `cargo_driver` | Delivery workflow, real-time tracking |
| `cargo_wallet` | `cargo_base` | Wallet & transactions |
| `cargo_coupon` | `cargo_base` | Coupons & discounts |
| `cargo_review` | `cargo_store` | Reviews & ratings |
| `cargo_notification` | `cargo_base` | Push + in-app notifications |
| `cargo_reports` | `cargo_base` | Analytics & dashboards |
| `cargo_marketplace` | all | Odoo Website marketplace extension |
