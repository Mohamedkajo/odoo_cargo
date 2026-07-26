# cargo_coupon

Coupon codes and promotional discounts for the Cargo Marketplace.

## Models

| Model | Description |
|---|---|
| `cargo.coupon` | Coupon definition — code, type (% or fixed), limits, expiry, store scope |
| `cargo.coupon.usage` | Per-user redemption log |

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/coupons/validate` | Customer JWT | Check if a code is valid and return discount amount |
| POST | `/api/coupons/apply` | Customer JWT | Apply code to cart, return discount |

## Dependencies

`cargo_cart`
