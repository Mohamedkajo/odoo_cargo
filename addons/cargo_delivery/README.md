# cargo_delivery

Driver assignment, OTP handshake, and live delivery tracking.

## Models

| Model | Description |
|---|---|
| `cargo.delivery` | One record per order — driver FK, status FSM, pickup/delivery OTPs, live GPS, ETA |

## Status FSM

```
assigned → picked_up → on_the_way → delivered
                     ↘ failed
```

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/orders/:id/tracking` | Customer JWT | Live tracking for order |
| GET | `/api/deliveries/:id` | Driver/Admin JWT | Full delivery detail |
| PATCH | `/api/deliveries/:id/status` | Driver/Admin JWT | Advance delivery status |

## Dependencies

`cargo_order` → `cargo_driver`
