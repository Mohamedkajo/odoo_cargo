# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
Cargo Marketplace — Base exceptions.

All custom exceptions used across Cargo modules are defined here.
Controllers catch these and convert them to structured JSON error responses.
"""

from .constants import (
    HTTP_400, HTTP_401, HTTP_403, HTTP_404, HTTP_409, HTTP_422, HTTP_429, HTTP_500,
    ERR_VALIDATION, ERR_AUTH, ERR_TOKEN, ERR_EXPIRED, ERR_REVOKED,
    ERR_PERMISSION, ERR_NOT_FOUND, ERR_CONFLICT, ERR_RATE_LIMIT,
    ERR_SERVER, ERR_TRANSITION, ERR_OTP, ERR_OTP_EXPIRED,
)


class CargoBaseException(Exception):
    """Base exception for all Cargo errors. Carries HTTP status and error code."""

    http_status: int = HTTP_500
    error_code: str  = ERR_SERVER

    def __init__(self, message: str = 'An unexpected error occurred', field: str = None):
        super().__init__(message)
        self.message = message
        self.field   = field   # Optional: field that caused the error

    def to_dict(self) -> dict:
        """Serialise to the standard Cargo error response body."""
        payload = {
            'error':   self.error_code,
            'message': self.message,
        }
        if self.field:
            payload['field'] = self.field
        return payload


# ── Validation ────────────────────────────────────────────────────────────────

class CargoValidationError(CargoBaseException):
    """Raised when request data fails validation."""
    http_status = HTTP_422
    error_code  = ERR_VALIDATION

    def __init__(self, message: str, field: str = None):
        super().__init__(message, field)


class CargoMissingFieldError(CargoValidationError):
    """Raised when a required field is missing."""

    def __init__(self, field: str):
        super().__init__(f"Field '{field}' is required.", field)


class CargoInvalidFieldError(CargoValidationError):
    """Raised when a field value is invalid."""

    def __init__(self, field: str, reason: str):
        super().__init__(f"Invalid value for '{field}': {reason}", field)


# ── Authentication ────────────────────────────────────────────────────────────

class CargoAuthError(CargoBaseException):
    """Raised when credentials are wrong."""
    http_status = HTTP_401
    error_code  = ERR_AUTH


class CargoTokenError(CargoBaseException):
    """Raised when a JWT is malformed or has an invalid signature."""
    http_status = HTTP_401
    error_code  = ERR_TOKEN


class CargoTokenExpiredError(CargoBaseException):
    """Raised when a JWT access token has expired."""
    http_status = HTTP_401
    error_code  = ERR_EXPIRED

    def __init__(self):
        super().__init__('Access token has expired. Please refresh.')


class CargoTokenRevokedError(CargoBaseException):
    """Raised when a JWT has been revoked (logout)."""
    http_status = HTTP_401
    error_code  = ERR_REVOKED

    def __init__(self):
        super().__init__('Token has been revoked. Please log in again.')


# ── Authorisation ─────────────────────────────────────────────────────────────

class CargoPermissionError(CargoBaseException):
    """Raised when the authenticated user lacks permission for an action."""
    http_status = HTTP_403
    error_code  = ERR_PERMISSION

    def __init__(self, message: str = 'You do not have permission to perform this action.'):
        super().__init__(message)


# ── Not Found ─────────────────────────────────────────────────────────────────

class CargoNotFoundError(CargoBaseException):
    """Raised when a requested resource does not exist."""
    http_status = HTTP_404
    error_code  = ERR_NOT_FOUND

    def __init__(self, resource: str = 'Resource', resource_id=None):
        msg = f"{resource} not found."
        if resource_id is not None:
            msg = f"{resource} with id '{resource_id}' not found."
        super().__init__(msg)


# ── Conflict ──────────────────────────────────────────────────────────────────

class CargoConflictError(CargoBaseException):
    """Raised for duplicate / conflicting data (e.g. email already registered)."""
    http_status = HTTP_409
    error_code  = ERR_CONFLICT


# ── Business Logic ────────────────────────────────────────────────────────────

class CargoStatusTransitionError(CargoBaseException):
    """Raised when an order status transition is not allowed."""
    http_status = HTTP_400
    error_code  = ERR_TRANSITION

    def __init__(self, current: str, requested: str):
        super().__init__(
            f"Cannot transition order from '{current}' to '{requested}'."
        )


class CargoOTPError(CargoBaseException):
    """Raised when OTP verification fails."""
    http_status = HTTP_400
    error_code  = ERR_OTP

    def __init__(self):
        super().__init__('OTP verification failed. Invalid code.')


class CargoOTPExpiredError(CargoBaseException):
    """Raised when OTP has expired."""
    http_status = HTTP_400
    error_code  = ERR_OTP_EXPIRED

    def __init__(self):
        super().__init__('OTP has expired. Please request a new one.')


class CargoInsufficientFundsError(CargoBaseException):
    """Raised when wallet balance is insufficient."""
    http_status = HTTP_400
    error_code  = 'INSUFFICIENT_FUNDS'

    def __init__(self, required: float, available: float):
        super().__init__(
            f"Insufficient wallet balance. Required: {required:.2f}, Available: {available:.2f}."
        )


# ── Rate Limiting ─────────────────────────────────────────────────────────────

class CargoRateLimitError(CargoBaseException):
    """Raised when a client exceeds the request rate limit."""
    http_status = HTTP_429
    error_code  = ERR_RATE_LIMIT

    def __init__(self, retry_after: int = 60):
        super().__init__(f'Rate limit exceeded. Retry after {retry_after} seconds.')
        self.retry_after = retry_after

    def to_dict(self) -> dict:
        d = super().to_dict()
        d['retry_after'] = self.retry_after
        return d


# ── Server ────────────────────────────────────────────────────────────────────

class CargoServerError(CargoBaseException):
    """Raised for unexpected internal server errors."""
    http_status = HTTP_500
    error_code  = ERR_SERVER
