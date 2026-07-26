# cargo_cart

Per-user shopping cart management for the Cargo Marketplace.

## Models

| Model | Description |
|---|---|
| `cargo.cart` | One cart per user — unique constraint, links to store |
| `cargo.cart.line` | One line per product in the cart — qty, unit price, selected variants/addons |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/cart` | Get current user's cart |
| DELETE | `/api/cart` | Clear the cart |
| POST | `/api/cart/items` | Add a product to the cart |
| PATCH | `/api/cart/items/:id` | Update item quantity |
| DELETE | `/api/cart/items/:id` | Remove an item |

## Dependencies

`cargo_auth` → `cargo_product` → `cargo_store`
