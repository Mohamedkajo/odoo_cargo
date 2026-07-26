# cargo_review

Customer star ratings and text reviews for stores and products.

## Models

| Model | Description |
|---|---|
| `cargo.review` | Star-rating (1–5) + text review for a store or product |

## Behaviour

After every create/write, the module recomputes `rating` and `review_count` on the target `cargo.store` or `cargo.product` record so Flutter home-screen cards always reflect current averages.

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/stores/:id/reviews` | Public | List approved reviews for a store |
| POST | `/api/stores/:id/reviews` | Customer JWT | Submit a store review |
| GET | `/api/products/:id/reviews` | Public | List approved reviews for a product |
| POST | `/api/products/:id/reviews` | Customer JWT | Submit a product review |

## Dependencies

`cargo_auth` → `cargo_store` → `cargo_product`
