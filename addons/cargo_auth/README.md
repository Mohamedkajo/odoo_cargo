# cargo_auth

JWT-based authentication and user profile management for the Cargo Marketplace.

## Models

Extends `res.users` with:
- `cargo_avatar_url` — profile photo URL
- `cargo_to_auth_dict()` — serialiser matching Flutter's `User.fromJson()` contract

Owns `cargo.api.token` — hashed refresh token records.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/register` | Register a new customer |
| POST | `/api/auth/login` | Login and receive JWT pair |
| POST | `/api/auth/refresh` | Exchange refresh token for new access token |
| POST | `/api/auth/logout` | Revoke refresh token |
| GET | `/api/users/profile` | Get current user's profile |
| PATCH | `/api/users/profile` | Update name/phone/address |
| PATCH | `/api/users/password` | Change password |
| POST | `/api/users/avatar` | Upload avatar image |

## Dependencies

`cargo_api`
