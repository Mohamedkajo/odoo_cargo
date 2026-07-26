# cargo_vendor

Vendor profile management for the Cargo Marketplace.

## Models

| Model | Description |
|---|---|
| `cargo.vendor` | Vendor business profile — business name, tax number, bank account, approval status, commission rate |

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/vendor/register` | Customer JWT | Register as a vendor |
| GET | `/api/vendor/profile` | Vendor JWT | Get vendor profile |
| PATCH | `/api/vendor/profile` | Vendor JWT | Update profile |
| GET | `/api/vendor/stats` | Vendor JWT | Order count and revenue summary |

## Dependencies

`cargo_auth` → `cargo_store`
