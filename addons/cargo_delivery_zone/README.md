# cargo_delivery_zone

Geographic delivery zones with per-zone fees and store assignments.

## Models

| Model | Description |
|---|---|
| `cargo.delivery.zone` | Named coverage area — city, delivery fee, min order, radius, linked stores |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/delivery-zones` | List all active zones |
| POST | `/api/delivery-zones/check` | Given `lat`/`lng`, return matching zone and fee |

## Dependencies

`cargo_store`
