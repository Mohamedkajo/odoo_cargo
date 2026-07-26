# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
Cargo JWT Utilities — Standard Library only (no PyJWT dependency).

Implements HS256 JWT using Python's built-in hmac, hashlib, base64 and json.
All functions are pure and stateless — callers pass the secret in.

Token structure:
    Header:  {"alg": "HS256", "typ": "JWT"}
    Payload: {"sub": uid, "uid": uid, "role": role, "iat": iat,
               "exp": exp, "iss": "cargo-marketplace", "aud": "cargo-mobile"}
    Sig:     HMAC-SHA256(base64url(header) + "." + base64url(payload), secret)
"""

import base64
import hashlib
import hmac
import json
import time

from ..constants import (
    JWT_ISSUER,
    JWT_AUDIENCE,
    JWT_ACCESS_EXPIRY_SECS,
    JWT_REFRESH_EXPIRY_SECS,
)
from ..exceptions import CargoTokenError, CargoTokenExpiredError, CargoTokenRevokedError


# ── Low-level helpers ─────────────────────────────────────────────────────────

def _b64url_encode(data: bytes) -> str:
    """Base64-URL encode without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def _b64url_decode(s: str) -> bytes:
    """Base64-URL decode, adding padding as required."""
    padding = 4 - len(s) % 4
    if padding != 4:
        s += '=' * padding
    return base64.urlsafe_b64decode(s)


def _sign(message: str, secret: str) -> str:
    """HMAC-SHA256 signature → base64url string."""
    sig = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256,
    ).digest()
    return _b64url_encode(sig)


def _build_token(payload: dict, secret: str) -> str:
    """Encode header + payload + signature into a JWT string."""
    header  = {'alg': 'HS256', 'typ': 'JWT'}
    h_enc   = _b64url_encode(json.dumps(header,  separators=(',', ':')).encode())
    p_enc   = _b64url_encode(json.dumps(payload, separators=(',', ':')).encode())
    signing = f'{h_enc}.{p_enc}'
    sig     = _sign(signing, secret)
    return f'{signing}.{sig}'


# ── Public API ────────────────────────────────────────────────────────────────

def generate_access_token(uid: int, role: str, secret: str,
                           expiry_secs: int = JWT_ACCESS_EXPIRY_SECS) -> str:
    """
    Generate a signed JWT access token.

    Args:
        uid:        Odoo res.users.id
        role:       'customer' | 'vendor' | 'driver'
        secret:     HMAC secret (from ir.config_parameter)
        expiry_secs: Token lifetime in seconds

    Returns:
        Signed JWT string
    """
    now = int(time.time())
    payload = {
        'sub':  str(uid),
        'uid':  uid,
        'role': role,
        'type': 'access',
        'iat':  now,
        'exp':  now + expiry_secs,
        'iss':  JWT_ISSUER,
        'aud':  JWT_AUDIENCE,
    }
    return _build_token(payload, secret)


def generate_refresh_token(uid: int, secret: str,
                            expiry_secs: int = JWT_REFRESH_EXPIRY_SECS) -> str:
    """
    Generate a signed JWT refresh token.

    The refresh token contains a minimal payload (no role) to reduce
    the attack surface. It is stored hashed in cargo.auth.token.
    """
    now = int(time.time())
    payload = {
        'sub':  str(uid),
        'uid':  uid,
        'type': 'refresh',
        'iat':  now,
        'exp':  now + expiry_secs,
        'iss':  JWT_ISSUER,
        'aud':  JWT_AUDIENCE,
    }
    return _build_token(payload, secret)


def verify_token(token: str, secret: str) -> dict:
    """
    Verify a JWT token's signature and expiry.

    Args:
        token:  JWT string from Authorization header
        secret: HMAC secret

    Returns:
        Decoded payload dict

    Raises:
        CargoTokenError:        Malformed token or invalid signature
        CargoTokenExpiredError: Token has expired
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise CargoTokenError('Token format is invalid.')

        h_enc, p_enc, sig = parts
        signing   = f'{h_enc}.{p_enc}'
        expected  = _sign(signing, secret)

        # Constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(expected, sig):
            raise CargoTokenError('Token signature verification failed.')

        payload = json.loads(_b64url_decode(p_enc))

        exp = payload.get('exp', 0)
        if exp and int(time.time()) > exp:
            raise CargoTokenExpiredError()

        return payload

    except (CargoTokenError, CargoTokenExpiredError):
        raise
    except Exception as exc:
        raise CargoTokenError(f'Token is malformed: {exc}') from exc


def decode_unsafe(token: str) -> dict:
    """
    Decode a JWT without verifying the signature.
    Use ONLY for debugging / logging — never for authorisation.
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return {}
        return json.loads(_b64url_decode(parts[1]))
    except Exception:
        return {}


def token_uid(payload: dict) -> int:
    """Extract and validate the user ID from a decoded payload."""
    uid = payload.get('uid') or payload.get('sub')
    try:
        return int(uid)
    except (TypeError, ValueError):
        raise CargoTokenError('Token payload missing valid user ID.')


def hash_token(token: str) -> str:
    """
    One-way hash of a token for storage in cargo.auth.token.
    We never store raw tokens — only their SHA-256 digest.
    """
    return hashlib.sha256(token.encode('utf-8')).hexdigest()
