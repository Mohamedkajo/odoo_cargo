# cargo_store

Vendor store profiles and store-browsing API for the Cargo Marketplace.

## Models

| Model | Description |
|---|---|
| `cargo.store` | Vendor store profile (name, slug, category, delivery settings, flags, GPS) |
| `cargo.store.tag` | Descriptive tags attached to stores (Halal, Free Delivery, Trending …) |

> **Not here:** `cargo.store.category` and `cargo.product.category` are owned by `cargo_category`.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/stores` | Paginated store list with optional filters |
| GET | `/api/stores/featured` | Featured stores |
| GET | `/api/stores/nearby` | Stores sorted by distance (requires `lat` + `lng` params) |
| GET | `/api/stores/online` | Stores that accept online orders |
| GET | `/api/stores/:id` | Store detail |
| GET | `/api/stores/:id/products` | Products in this store |
| GET | `/api/stores/:id/categories` | Product categories available in this store |

> **Not here:** `GET /api/categories` is owned by `cargo_category`.

## Dependencies

`cargo_api` → `cargo_auth` → `cargo_category` → `cargo_product`
