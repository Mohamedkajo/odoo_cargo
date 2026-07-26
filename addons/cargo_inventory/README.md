# cargo_inventory

Real-time stock tracking per product per store. Automatically keeps `cargo.product.is_available` in sync.

## Models

| Model | Description |
|---|---|
| `cargo.inventory` | One record per product × store — tracks quantity, reserved qty, and low-stock threshold |

## Behaviour

- When `available_qty` (= quantity − reserved_qty) drops to **0**, `cargo.product.is_available` is set to `False` automatically.
- When stock is replenished above 0, `is_available` is set back to `True`.

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/vendor/inventory` | Vendor JWT | List stock for all vendor stores |
| PATCH | `/api/vendor/inventory/:id` | Vendor JWT | Adjust qty or set alert threshold |

## Dependencies

`cargo_product` → `cargo_store`
