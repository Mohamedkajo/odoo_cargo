# cargo_category

**Odoo 18 Community · Cargo Marketplace**

Single-responsibility module that owns all category models for the platform.

---

## Models

### `cargo.store.category` (custom)

Top-level marketplace navigation tabs shown on the Flutter home screen —
Food, Grocery, Pharmacy, Sweets, Coffee, Electronics, …

No FK to `cargo.store`; stores reference this model via `cargo.store.category_id`.

| Field | Type | Purpose |
|---|---|---|
| `name` | Char | Display name (translatable) |
| `icon` | Char | Emoji / icon identifier |
| `image` | Char | Optional banner URL |
| `sequence` | Integer | Display order (lower = first) |
| `active` | Boolean | Soft-delete flag |

### `product.category` (native Odoo — extended in `cargo_base`)

Menu sections within a store's catalogue — Burgers, Drinks, Salads, …

`cargo_base` extends the native `product.category` with:

| Field | Type | Purpose |
|---|---|---|
| `cargo_icon` | Char | Emoji icon |
| `cargo_slug` | Char | URL-friendly slug (auto-generated, unique) |
| `cargo_is_active` | Boolean | Visible on marketplace |
| `cargo_sort_order` | Integer | Flutter sort position |
| `cargo_store_count` | Integer | Computed — stores in this category |

This module **creates the seed records** for standard menu sections and
provides the Odoo backend menu entry pointing to the native model.

---

## REST Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/categories` | None | List all active `cargo.store.category` records |

Product categories (menu sections) are **not** served via a dedicated endpoint.
They are returned contextually by `GET /api/stores/:id/categories`
(owned by `cargo_store`), which reads `product.template.categ_id` for products
belonging to the requested store.

---

## Dependencies

```
cargo_base
```

---

## Architecture Decision

`cargo.product.category` was removed in favour of the native `product.category`
model (already extended by `cargo_base`). This eliminates a duplicate category
hierarchy and lets Odoo's built-in product tree serve as the single source of
truth for menu sections. All FKs previously pointing to `cargo.product.category`
now point to `product.category`.
