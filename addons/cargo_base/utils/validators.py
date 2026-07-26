# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
Cargo input validators.

All validation functions raise CargoValidationError (or a subclass) on failure
and return the (possibly cleaned) value on success.
Controllers call these before touching the ORM.
"""

import re

from ..constants import (
    EGYPT_PHONE_REGEX,
    PASSWORD_MIN_LENGTH,
    MAX_IMAGE_SIZE_MB,
    ALLOWED_IMAGE_MIMES,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
)
from ..exceptions import CargoMissingFieldError, CargoInvalidFieldError


# ── Core helpers ──────────────────────────────────────────────────────────────

def require(value, field: str):
    """Raise CargoMissingFieldError if value is None or empty string."""
    if value is None or value == '':
        raise CargoMissingFieldError(field)
    return value


def require_str(value, field: str, max_length: int = None) -> str:
    """Validate a required string field. Returns stripped string."""
    require(value, field)
    if not isinstance(value, str):
        raise CargoInvalidFieldError(field, 'must be a string')
    cleaned = value.strip()
    if not cleaned:
        raise CargoMissingFieldError(field)
    if max_length and len(cleaned) > max_length:
        raise CargoInvalidFieldError(field, f'must be at most {max_length} characters')
    return cleaned


def optional_str(value, field: str, max_length: int = None) -> str:
    """Validate an optional string. Returns stripped string or empty string."""
    if value is None or value == '':
        return ''
    if not isinstance(value, str):
        raise CargoInvalidFieldError(field, 'must be a string')
    cleaned = value.strip()
    if max_length and len(cleaned) > max_length:
        raise CargoInvalidFieldError(field, f'must be at most {max_length} characters')
    return cleaned


# ── Type validators ───────────────────────────────────────────────────────────

def require_int(value, field: str, min_val: int = None, max_val: int = None) -> int:
    """Validate and return a required integer."""
    require(value, field)
    try:
        v = int(value)
    except (TypeError, ValueError):
        raise CargoInvalidFieldError(field, 'must be an integer')
    if min_val is not None and v < min_val:
        raise CargoInvalidFieldError(field, f'must be >= {min_val}')
    if max_val is not None and v > max_val:
        raise CargoInvalidFieldError(field, f'must be <= {max_val}')
    return v


def require_float(value, field: str, min_val: float = None, max_val: float = None) -> float:
    """Validate and return a required float."""
    require(value, field)
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise CargoInvalidFieldError(field, 'must be a number')
    if min_val is not None and v < min_val:
        raise CargoInvalidFieldError(field, f'must be >= {min_val}')
    if max_val is not None and v > max_val:
        raise CargoInvalidFieldError(field, f'must be <= {max_val}')
    return v


def require_positive(value, field: str) -> float:
    """Validate that a numeric value is strictly positive."""
    v = require_float(value, field)
    if v <= 0:
        raise CargoInvalidFieldError(field, 'must be greater than 0')
    return v


# ── Domain-specific validators ────────────────────────────────────────────────

_EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')
_EG_PHONE = re.compile(EGYPT_PHONE_REGEX)


def validate_email(email: str, field: str = 'email') -> str:
    """Validate and normalise an email address."""
    cleaned = require_str(email, field, max_length=254)
    if not _EMAIL_RE.match(cleaned):
        raise CargoInvalidFieldError(field, 'is not a valid email address')
    return cleaned.lower()


def validate_phone(phone: str, field: str = 'phone') -> str:
    """
    Validate an Egyptian mobile number.
    Accepts: +201xxxxxxxxx, 00201xxxxxxxxx, 01xxxxxxxxx
    Returns the number normalised to +20 international format.
    """
    cleaned = require_str(phone, field, max_length=20)
    cleaned = re.sub(r'[\s\-()]', '', cleaned)
    if not _EG_PHONE.match(cleaned):
        raise CargoInvalidFieldError(
            field,
            'must be a valid Egyptian mobile number (e.g. +201012345678)'
        )
    # Normalise to +20 format
    if cleaned.startswith('00'):
        cleaned = '+' + cleaned[2:]
    elif cleaned.startswith('0') and not cleaned.startswith('00'):
        cleaned = '+2' + cleaned
    return cleaned


def validate_password(password: str, field: str = 'password') -> str:
    """
    Validate password strength.
    Rules: minimum 8 chars, at least one digit and one letter.
    """
    cleaned = require_str(password, field, max_length=128)
    if len(cleaned) < PASSWORD_MIN_LENGTH:
        raise CargoInvalidFieldError(
            field,
            f'must be at least {PASSWORD_MIN_LENGTH} characters'
        )
    if not re.search(r'[A-Za-z]', cleaned):
        raise CargoInvalidFieldError(field, 'must contain at least one letter')
    if not re.search(r'\d', cleaned):
        raise CargoInvalidFieldError(field, 'must contain at least one digit')
    return cleaned


def validate_rating(rating, field: str = 'rating') -> float:
    """Validate a 1–5 star rating."""
    v = require_float(rating, field)
    if v < 1.0 or v > 5.0:
        raise CargoInvalidFieldError(field, 'must be between 1 and 5')
    return round(v, 1)


def validate_discount_percent(value, field: str = 'discountPercent') -> float:
    """Validate a percentage value (0–100)."""
    v = require_float(value, field, min_val=0.0, max_val=100.0)
    return round(v, 2)


def validate_otp(otp: str, field: str = 'otp') -> str:
    """Validate a 4–6 digit OTP."""
    cleaned = require_str(otp, field)
    if not re.fullmatch(r'\d{4,6}', cleaned):
        raise CargoInvalidFieldError(field, 'must be a 4 to 6 digit code')
    return cleaned


# ── Pagination ────────────────────────────────────────────────────────────────

def validate_pagination(page=None, limit=None) -> tuple[int, int]:
    """
    Parse and validate pagination parameters.
    Returns (page, limit) as integers.
    """
    try:
        p = max(1, int(page or DEFAULT_PAGE_SIZE))
    except (TypeError, ValueError):
        p = 1
    try:
        lim = min(MAX_PAGE_SIZE, max(1, int(limit or DEFAULT_PAGE_SIZE)))
    except (TypeError, ValueError):
        lim = DEFAULT_PAGE_SIZE
    return p, lim


def pagination_offset(page: int, limit: int) -> int:
    """Return the SQL OFFSET for the given page and limit."""
    return (page - 1) * limit


# ── Image ─────────────────────────────────────────────────────────────────────

def validate_image_size(size_bytes: int, field: str = 'image') -> None:
    """Raise if image exceeds the configured maximum size."""
    max_bytes = MAX_IMAGE_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise CargoInvalidFieldError(
            field,
            f'file size {size_bytes / 1024 / 1024:.1f} MB exceeds '
            f'the maximum of {MAX_IMAGE_SIZE_MB} MB'
        )


def validate_image_mime(mime_type: str, field: str = 'image') -> None:
    """Raise if MIME type is not in the allowed set."""
    if mime_type not in ALLOWED_IMAGE_MIMES:
        allowed = ', '.join(sorted(ALLOWED_IMAGE_MIMES))
        raise CargoInvalidFieldError(
            field,
            f'unsupported image type "{mime_type}". Allowed: {allowed}'
        )


# ── Generic selection ─────────────────────────────────────────────────────────

def validate_selection(value, choices: list, field: str) -> str:
    """Validate that value is one of the allowed selection values."""
    allowed = {c[0] for c in choices}
    cleaned = require_str(value, field)
    if cleaned not in allowed:
        raise CargoInvalidFieldError(
            field,
            f'must be one of: {", ".join(sorted(allowed))}'
        )
    return cleaned
