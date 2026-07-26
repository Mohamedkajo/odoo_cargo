# cargo_order

Order lifecycle management for the Cargo Marketplace.

## Models

| Model | Description |
|---|---|
| `cargo.order` | Customer order — status FSM, line items, totals, delivery address |
| `cargo.order.line` | One line per product — qty, unit price, subtotal |

## Status FSM

```
confirmed → preparing → ready → collecting → delivering → otp_check → delivered
         ↘ cancelled at any non-terminal stage
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/orders` | Customer's order history |
| POST | `/api/orders` | Place a new order from current cart |
| GET | `/api/orders/:id` | Order detail |
| POST | `/api/orders/:id/cancel` | Cancel an order |
| GET | `/api/orders/:id/tracking` | Live delivery tracking (delegates to cargo_delivery when installed) |

## Dependencies

`cargo_cart`
