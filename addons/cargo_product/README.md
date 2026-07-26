# cargo_product

Product catalogue, flash sales, and product-browsing API for the Cargo Marketplace.

## Models

| Model | Description |
|---|---|
| `cargo.product` | Marketplace product listing (price, discount, rating, availability) |
| `cargo.product.variant` | Size/colour/option variants for a product |
| `cargo.product.addon` | Extra add-on items (e.g. extra cheese, ketchup) |
| `cargo.product.image` | Gallery images for a product |
| `cargo.product.tag` | Descriptive tags on products |

> **Not here:** `cargo.product.category` is owned by `cargo_category` to avoid a circular dependency with `cargo_store`.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/products` | Paginated product catalogue (filters: storeId, categoryId, search) |
| GET | `/api/products/trending` | Featured/trending products |
| GET | `/api/products/:id` | Product detail with gallery, variants, add-ons |
| GET | `/api/flash-sales` | Active flash-sale products |

## Dependencies

`cargo_api` → `cargo_category`
