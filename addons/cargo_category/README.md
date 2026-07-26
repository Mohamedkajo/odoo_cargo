# cargo_category

Owns all category models for the Cargo Marketplace platform.

## Models

| Model | Description |
|---|---|
| `cargo.store.category` | Top-level marketplace tabs (Food, Grocery, Pharmacy …) shown on the Flutter home screen |
| `cargo.product.category` | Menu sections inside a store catalogue (Burgers, Drinks, Sides …) |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/categories` | List all active store categories |

## Design Decisions

- **No store FK on `cargo.product.category`** — the store↔category link is resolved through `cargo.product.store_id`, keeping this module free of a dependency on `cargo_store` and avoiding circular imports.
- **Single responsibility** — no routes for stores or products live here.

## Dependencies

`cargo_base` only — the lightest possible dependency footprint.
