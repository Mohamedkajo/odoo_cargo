# cargo_driver

Delivery driver profiles, live location tracking, and status management.

## Models

| Model | Description |
|---|---|
| `cargo.driver` | Driver profile — vehicle info, live GPS, online status, earnings, rating |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/driver/profile` | Get driver's own profile |
| PATCH | `/api/driver/profile` | Update vehicle details |
| POST | `/api/driver/status` | Go online or offline |
| PATCH | `/api/driver/location` | Push live GPS coordinates |
| GET | `/api/driver/earnings` | Earnings and delivery count |

## Dependencies

`cargo_auth` only — intentionally thin to avoid coupling.
