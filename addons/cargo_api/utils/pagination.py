# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
Pagination utilities for Cargo REST API controllers.

Usage in a controller::

    from cargo_api.utils.pagination import PaginationParams

    def list_stores(self, **kwargs):
        params = PaginationParams.from_request()
        stores  = env['cargo.store'].search(domain,
                                             limit=params.limit,
                                             offset=params.offset,
                                             order=params.order_clause)
        total   = env['cargo.store'].search_count(domain)
        return paginated(
            [s.cargo_to_api_dict() for s in stores],
            total=total,
            page=params.page,
            limit=params.limit,
        )
"""

import math

from odoo.http import request

# Maximum and default page sizes
_MAX_LIMIT     = 100
_DEFAULT_LIMIT = 20
_DEFAULT_PAGE  = 1


class PaginationParams:
    """
    Parsed and validated pagination parameters from the HTTP request.

    Query parameters:
        page  : int ≥ 1 (default 1)
        limit : int 1–100 (default 20)
        sort  : field name, optionally prefixed with '-' for DESC
                e.g. sort=name, sort=-created_at
    """

    __slots__ = ('page', 'limit', 'sort_field', 'sort_asc', 'offset', 'order_clause')

    def __init__(self, page, limit, sort_field=None, sort_asc=True,
                 allowed_sort_fields=None):
        self.page       = max(1, int(page))
        self.limit      = min(_MAX_LIMIT, max(1, int(limit)))
        self.sort_asc   = bool(sort_asc)

        # Validate sort field against allowed list
        if sort_field and allowed_sort_fields and sort_field not in allowed_sort_fields:
            sort_field = None
        self.sort_field = sort_field

        self.offset = (self.page - 1) * self.limit

        # Build SQL-safe ORDER BY clause
        if self.sort_field:
            direction = 'ASC' if self.sort_asc else 'DESC'
            self.order_clause = f'{self.sort_field} {direction}'
        else:
            self.order_clause = None

    @classmethod
    def from_request(cls, allowed_sort_fields=None):
        """
        Parse pagination parameters from the current HTTP request's
        query string.  Handles type errors gracefully — invalid values
        fall back to defaults rather than raising.
        """
        params = request.params

        try:
            page = int(params.get('page', _DEFAULT_PAGE))
        except (TypeError, ValueError):
            page = _DEFAULT_PAGE

        try:
            limit = int(params.get('limit', _DEFAULT_LIMIT))
        except (TypeError, ValueError):
            limit = _DEFAULT_LIMIT

        # Sort: '-created_at' → sort_field='created_at', sort_asc=False
        sort_raw   = params.get('sort', '') or ''
        sort_asc   = True
        sort_field = None
        if sort_raw:
            if sort_raw.startswith('-'):
                sort_field = sort_raw[1:].strip()
                sort_asc   = False
            else:
                sort_field = sort_raw.strip()
                sort_asc   = True

        return cls(
            page=page,
            limit=limit,
            sort_field=sort_field,
            sort_asc=sort_asc,
            allowed_sort_fields=allowed_sort_fields,
        )

    def to_dict(self):
        return {
            'page':       self.page,
            'limit':      self.limit,
            'sort_field': self.sort_field,
            'sort_asc':   self.sort_asc,
            'offset':     self.offset,
        }


def build_pagination_meta(total, page, limit):
    """
    Build the pagination metadata dict included in every paginated response.

    Args:
        total : int  — total matching records (before pagination)
        page  : int  — current page number (1-based)
        limit : int  — page size

    Returns:
        dict with: page, limit, total, pages, hasNext, hasPrev
    """
    pages    = max(1, math.ceil(total / limit)) if limit else 1
    has_next = page < pages
    has_prev = page > 1

    return {
        'page':    page,
        'limit':   limit,
        'total':   total,
        'pages':   pages,
        'hasNext': has_next,
        'hasPrev': has_prev,
    }


def parse_filters(allowed_fields=None):
    """
    Parse ``filter[field]=value`` style query parameters from the current request.

    Returns a list of Odoo domain tuples suitable for use with ``search()``.

    Example:
        GET /api/v1/stores?filter[city]=Cairo&filter[is_open]=true

        Returns: [('city', '=', 'Cairo'), ('is_open', '=', True)]

    Only fields in ``allowed_fields`` are included; others are silently ignored.
    """
    params  = request.params
    domain  = []

    for key, value in params.items():
        if not key.startswith('filter[') or not key.endswith(']'):
            continue
        field = key[7:-1]
        if allowed_fields and field not in allowed_fields:
            continue
        # Coerce bool-like strings
        if value.lower() == 'true':
            value = True
        elif value.lower() == 'false':
            value = False
        else:
            # Try numeric coercion
            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    pass
        domain.append((field, '=', value))

    return domain


def parse_search(field='name'):
    """
    Parse the ``q`` (search) query parameter.

    Returns an Odoo domain tuple for a case-insensitive ILIKE search on
    the specified field, or an empty list if the ``q`` param is absent.

    Example:
        GET /api/v1/products?q=burger
        Returns: [('name', 'ilike', 'burger')]
    """
    q = (request.params.get('q') or '').strip()
    if not q:
        return []
    return [(field, 'ilike', q)]
