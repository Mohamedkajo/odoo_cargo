# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
JWT authentication decorator for Cargo API controllers.

Usage::

    from odoo import http
    from cargo_api.utils.decorators import require_cargo_auth

    class MyController(CargoBaseController):

        # Public route — anyone can call it
        @http.route('/api/v1/products', auth='none', methods=['GET'],
                    type='http', csrf=False)
        def list_products(self, **kwargs):
            ...

        # Authenticated route — any valid JWT
        @http.route('/api/v1/orders', auth='none', methods=['GET'],
                    type='http', csrf=False)
        @require_cargo_auth()
        def list_my_orders(self, **kwargs):
            user = request.cargo_user
            ...

        # Role-restricted route
        @http.route('/api/v1/vendor/orders', auth='none', methods=['GET'],
                    type='http', csrf=False)
        @require_cargo_auth('vendor', 'vendor_manager', 'admin', 'super_admin')
        def list_vendor_orders(self, **kwargs):
            ...

The decorator:
  1. Checks the per-IP rate limit (raises 429 if exceeded)
  2. Extracts and verifies the JWT from 'Authorization: Bearer …'
  3. Checks the token has not been revoked in cargo.api.token
  4. Verifies the user exists and is active
  5. Checks the user's role is in the allowed roles (if any)
  6. Attaches request.cargo_user and request.cargo_payload
  7. Logs the request to cargo.audit.log
  8. Wraps all CargoBaseException subclasses and returns correct HTTP responses

The decorator MUST be placed BELOW @http.route in source code (applied first).
"""

import functools
import logging

from odoo.http import request

from cargo_base.exceptions import CargoBaseException, CargoPermissionError
from cargo_base.utils.response import from_exception, server_error

_logger = logging.getLogger(__name__)


def require_cargo_auth(*roles):
    """
    Decorator factory that gates an HTTP route behind JWT authentication.

    Args:
        *roles: Optional whitelist of cargo_role strings.  If provided, the
                authenticated user's role must be one of them.  Omit to
                allow any valid token holder.

    The authenticated user is available inside the decorated method via::

        user    = request.cargo_user     # res.users recordset
        payload = request.cargo_payload  # raw JWT payload dict
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(controller_self, **kwargs):
            try:
                # 1. Rate limit check (uses controller's _cargo_check_rate_limit)
                controller_self._cargo_check_rate_limit()

                # 2. JWT authentication (uses controller's _cargo_get_current_user)
                user, payload = controller_self._cargo_get_current_user()

                # 3. Role check
                if roles:
                    user_role = payload.get('role', '')
                    if user_role not in roles:
                        raise CargoPermissionError(
                            f'Access denied. This endpoint requires one of the '
                            f'following roles: {", ".join(roles)}. '
                            f'Your role: {user_role or "none"}.'
                        )

                # 4. Attach to request for downstream access
                request.cargo_user    = user
                request.cargo_payload = payload

                # 5. Log the API call
                try:
                    controller_self._cargo_log_api_call(user, payload)
                except Exception as log_exc:
                    _logger.warning('API call logging failed (non-fatal): %s', log_exc)

                # 6. Execute the actual handler
                return func(controller_self, **kwargs)

            except CargoBaseException as exc:
                return from_exception(exc)
            except Exception as exc:
                _logger.exception('Unhandled exception in cargo API route %s: %s',
                                  func.__name__, exc)
                return server_error()

        # Preserve Odoo's routing attributes so the dispatcher still works
        if hasattr(func, 'routing'):
            wrapper.routing = func.routing
        if hasattr(func, 'original_func'):
            wrapper.original_func = func.original_func

        return wrapper
    return decorator


def require_cargo_admin(func):
    """
    Shorthand decorator that requires admin or super_admin role.
    Equivalent to @require_cargo_auth('admin', 'super_admin').
    """
    return require_cargo_auth('admin', 'super_admin')(func)


def require_cargo_vendor(func):
    """
    Shorthand for vendor or higher.
    Equivalent to @require_cargo_auth('vendor', 'vendor_manager', 'admin', 'super_admin').
    """
    return require_cargo_auth('vendor', 'vendor_manager', 'admin', 'super_admin')(func)


def require_cargo_driver(func):
    """
    Shorthand for driver role.
    """
    return require_cargo_auth('driver', 'admin', 'super_admin')(func)
