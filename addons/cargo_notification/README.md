# cargo_notification

In-app push notifications for the Cargo Marketplace.

## Models

| Model | Description |
|---|---|
| `cargo.notification` | Notification record — user, type, title, body, read status |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/notifications` | Get current user's notifications |
| POST | `/api/notifications/:id/read` | Mark a notification as read |
| POST | `/api/notifications/read-all` | Mark all notifications as read |

## Class Method

`cargo.notification.send_to_user(user_id, notif_type, title, body)` — used by other modules (order, wallet) to send in-app messages.

## Dependencies

`cargo_auth`
