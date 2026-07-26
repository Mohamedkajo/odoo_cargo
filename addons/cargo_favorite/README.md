# cargo_favorite

User favourites (saved stores and products) for the Cargo Marketplace.

## Models

| Model | Description |
|---|---|
| `cargo.favorite` | Favourite entry — user × (store or product), with unique constraints |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/favorites` | Get current user's favourites |
| POST | `/api/favorites/toggle` | Toggle favourite status for a store or product |

## Dependencies

`cargo_auth` → `cargo_product` → `cargo_store`
