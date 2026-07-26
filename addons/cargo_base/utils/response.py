# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
Cargo API response helpers.

All HTTP controllers use these helpers to build consistent JSON responses.
The envelope format is compatible with the existing Flutter app's expectations.

Success envelope::

    {
        "success": true,
        "data": <payload>,
        "message": "Optional message"
    }

Paginated envelope::

    {
        "success": true,
        "data": [...],
        "pagination": {
            "page": 1,
            "limit": 20,
            "total": 120,
            "pages": 6,
            "hasNext": true,
            "hasPrev": false
        }
    }

Error envelope::

    {
        "success": false,
        "error": "ERROR_CODE",
        "message": "Human-readable message",
        "field": "field_name"  # optional
    }
"""

import json
import math

from werkzeug.wrappers import Response as WerkzeugResponse

from ..constants import HTTP_200, HTTP_201, HTTP_400, ERR_SERVER
from ..exceptions import CargoBaseException


# ── Internal builder ──────────────────────────────────────────────────────────

def _json_response(body: dict, status: int = HTTP_200) -> WerkzeugResponse:
    """Build a Werkzeug JSON response from a dict."""
    return WerkzeugResponse(
        response=json.dumps(body, ensure_ascii=False, default=str),
        status=status,
        mimetype='application/json',
    )


# ── Success responses ─────────────────────────────────────────────────────────

def success(data, status: int = HTTP_200, message: str = None) -> WerkzeugResponse:
    """
    Standard success response.

    Args:
        data:    Any JSON-serialisable value (dict, list, scalar)
        status:  HTTP status code (default 200)
        message: Optional human-readable message
    """
    body = {'success': True, 'data': data}
    if message:
        body['message'] = message
    return _json_response(body, status)


def created(data, message: str = 'Created successfully') -> WerkzeugResponse:
    """201 Created response."""
    return success(data, status=HTTP_201, message=message)


def no_content() -> WerkzeugResponse:
    """204 No Content response (empty body)."""
    return WerkzeugResponse(status=204)


def paginated(
    data: list,
    total: int,
    page: int,
    limit: int,
) -> WerkzeugResponse:
    """
    Paginated list response.

    Args:
        data:  Current page of items
        total: Total matching records across all pages
        page:  Current page (1-based)
        limit: Items per page
    """
    pages = math.ceil(total / limit) if limit > 0 else 1
    body = {
        'success': True,
        'data':    data,
        'pagination': {
            'page':    page,
            'limit':   limit,
            'total':   total,
            'pages':   pages,
            'hasNext': page < pages,
            'hasPrev': page > 1,
        },
    }
    return _json_response(body, HTTP_200)


# ── Error responses ───────────────────────────────────────────────────────────

def error(
    error_code: str,
    message: str,
    status: int = HTTP_400,
    field: str = None,
) -> WerkzeugResponse:
    """
    Standard error response.

    Args:
        error_code: Machine-readable error constant (e.g. 'VALIDATION_ERROR')
        message:    Human-readable explanation
        status:     HTTP status code
        field:      Optional field that caused the error
    """
    body: dict = {
        'success': False,
        'error':   error_code,
        'message': message,
    }
    if field:
        body['field'] = field
    return _json_response(body, status)


def from_exception(exc: CargoBaseException) -> WerkzeugResponse:
    """
    Build an error response directly from a CargoBaseException.
    Used in controller try/except blocks.
    """
    return _json_response(
        {'success': False, **exc.to_dict()},
        exc.http_status,
    )


def server_error(message: str = 'An unexpected error occurred') -> WerkzeugResponse:
    """500 Internal Server Error response."""
    return error(ERR_SERVER, message, status=500)
