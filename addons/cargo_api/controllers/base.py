# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
CargoBaseController — Base HTTP controller for all Cargo REST API routes.

All Cargo module controllers inherit this class to obtain:
  - JWT authentication via _cargo_get_current_user()
  - Per-IP rate limiting via _cargo_check_rate_limit()
  - Request/response audit logging via _cargo_log_api_call()
  - Pagination helpers via the pagination utils
  - Consistent error wrapping

Infrastructure routes provided by this module:
  GET  /api/v1/health        — liveness probe (no auth required)
  GET  /api/v1/version       — API and Odoo version info (no auth)
  GET  /api/v1/openapi.json  — OpenAPI 3.0.3 specification (no auth)
  GET  /api/v1/docs          — Swagger UI HTML page (no auth)
"""

import json
import logging
import time

from odoo import http
from odoo.http import request
from odoo.release import version as odoo_version
from werkzeug.wrappers import Response as WerkzeugResponse

from cargo_base.constants import (
    HTTP_200,
    HTTP_429,
    HTTP_500,
    ERR_SERVER,
    ERR_RATE_LIMIT,
)
from cargo_base.exceptions import (
    CargoBaseException,
    CargoAuthError,
    CargoTokenError,
    CargoTokenExpiredError,
    CargoServerError,
    CargoRateLimitError,
)
from cargo_base.utils.jwt_utils import verify_token, token_uid, hash_token
from cargo_base.utils.response import success, error, from_exception, server_error

from cargo_api.utils.openapi import get_cargo_openapi_spec

_logger = logging.getLogger(__name__)

# Cache the serialised OpenAPI spec in memory (it's static per worker startup)
_OPENAPI_JSON_CACHE = None

# Swagger UI HTML served at /api/v1/docs
_SWAGGER_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Cargo API — Documentation</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
  <style>
    body { margin: 0; background: #fafafa; }
    .swagger-ui .topbar { background-color: #1a1a2e; }
    .swagger-ui .topbar .download-url-wrapper { display: none; }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    SwaggerUIBundle({
      url: '/api/v1/openapi.json',
      dom_id: '#swagger-ui',
      presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
      layout: 'BaseLayout',
      deepLinking: true,
      displayRequestDuration: true,
      filter: true,
    });
  </script>
</body>
</html>
"""


class CargoBaseController(http.Controller):
    """
    Base HTTP controller inherited by every Cargo API controller.

    Subclasses register their own routes with @http.route(..., auth='none',
    type='http', csrf=False) and then call the helpers below for auth,
    rate limiting, and response serialisation.
    """

    # =========================================================================
    # Authentication helpers
    # =========================================================================

    def _cargo_get_current_user(self):
        """
        Extract and verify the JWT from the ``Authorization: Bearer …`` header.

        Returns:
            Tuple[res.users, dict] — (user record, decoded JWT payload)

        Raises:
            CargoAuthError          — missing or malformed Authorization header
            CargoTokenError         — invalid signature or structure
            CargoTokenExpiredError  — token has expired
            CargoAuthError          — user not found or deactivated
            CargoTokenError         — token has been explicitly revoked
        """
        auth_header = request.httprequest.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            raise CargoAuthError(
                'Authorization header missing or malformed. '
                'Expected: Authorization: Bearer <token>'
            )

        raw_token = auth_header[7:].strip()
        if not raw_token:
            raise CargoAuthError('Bearer token is empty.')

        ICP = request.env['ir.config_parameter'].sudo()
        secret = ICP.get_param('cargo.jwt.secret', '')
        if not secret:
            _logger.critical('cargo.jwt.secret is not configured! Check post_init_hook.')
            raise CargoServerError(
                'JWT configuration error. Please contact the platform administrator.'
            )

        # Verify signature, structure, and expiry
        payload = verify_token(raw_token, secret)

        # Resolve user ID from payload
        uid = token_uid(payload)

        # Check revocation list (only for access tokens; refresh tokens are
        # revoked by their own flow in cargo_auth)
        token_hash = hash_token(raw_token)
        revoked = request.env['cargo.api.token'].sudo().search_count([
            ('token_hash', '=', token_hash),
            ('is_revoked', '=', True),
        ])
        if revoked:
            raise CargoTokenError('This token has been revoked. Please log in again.')

        # Load and validate the user record
        user = request.env['res.users'].sudo().browse(uid)
        if not user.exists():
            raise CargoAuthError(f'User account (id={uid}) not found.')
        if not user.active:
            raise CargoAuthError('User account is deactivated.')

        return user, payload

    # =========================================================================
    # Rate limiting
    # =========================================================================

    def _cargo_check_rate_limit(self):
        """
        Enforce the per-IP rate limit configured in cargo.rate_limit.requests_per_minute.

        Uses an atomic PostgreSQL UPSERT so it is safe across all Odoo worker
        processes.  Raises CargoRateLimitError (→ 429) if the limit is exceeded.
        """
        ip = (
            request.httprequest.headers.get('X-Forwarded-For', '')
            .split(',')[0]
            .strip()
            or request.httprequest.remote_addr
            or '0.0.0.0'
        )

        # Read limit from config (default 60 req/min if not configured)
        try:
            limit_rpm = int(
                request.env['ir.config_parameter'].sudo()
                .get_param('cargo.rate_limit.requests_per_minute', '60')
            )
        except (TypeError, ValueError):
            limit_rpm = 60

        count = request.env['cargo.rate.limit'].sudo().cargo_increment(ip)

        if count > limit_rpm:
            _logger.warning('Rate limit exceeded for IP %s (%d req/min)', ip, count)
            raise CargoRateLimitError(
                f'Rate limit exceeded ({limit_rpm} requests/minute). '
                f'Please slow down and retry after a moment.'
            )

    # =========================================================================
    # Audit logging
    # =========================================================================

    def _cargo_log_api_call(self, user, payload):
        """
        Write an audit log entry for the current authenticated API request.
        Failures are caught and logged — never propagated to the response.
        """
        try:
            method   = request.httprequest.method
            path     = request.httprequest.path
            request.env['cargo.audit.log'].sudo().cargo_log_api(
                user_id=user.id,
                action='api_call',
                model_name='http.request',
                record_id=0,
                description=f'{method} {path}',
            )
        except Exception as exc:
            _logger.debug('Audit log write failed for API call (non-fatal): %s', exc)

    # =========================================================================
    # Infrastructure routes
    # =========================================================================

    @http.route(
        '/api/v1/health',
        auth='none',
        methods=['GET'],
        type='http',
        csrf=False,
        save_session=False,
    )
    def cargo_health(self, **kwargs):
        """
        GET /api/v1/health — Liveness probe.

        Returns 200 OK when the server is running.  Used by load balancers,
        Docker health checks, and monitoring systems.  No authentication required.
        """
        try:
            # Quick DB connectivity check
            request.env.cr.execute('SELECT 1')
            db_ok = True
        except Exception:
            db_ok = False

        data = {
            'status':    'ok' if db_ok else 'degraded',
            'db':        'ok' if db_ok else 'unavailable',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        }
        status_code = HTTP_200 if db_ok else HTTP_500
        return success(data, status=status_code)

    @http.route(
        '/api/v1/version',
        auth='none',
        methods=['GET'],
        type='http',
        csrf=False,
        save_session=False,
    )
    def cargo_version(self, **kwargs):
        """
        GET /api/v1/version — API and platform version information.

        Returns Cargo API version, Odoo version, and the active module list.
        No authentication required.
        """
        ICP = request.env['ir.config_parameter'].sudo()
        data = {
            'api':            '1.0.0',
            'odoo':           odoo_version,
            'modules': {
                'cargo_base': _module_installed('cargo_base'),
                'cargo_api':  _module_installed('cargo_api'),
            },
            'environment': 'production' if not request.env.registry.in_test_mode() else 'test',
        }
        return success(data)

    @http.route(
        '/api/v1/openapi.json',
        auth='none',
        methods=['GET'],
        type='http',
        csrf=False,
        save_session=False,
    )
    def cargo_openapi_json(self, **kwargs):
        """
        GET /api/v1/openapi.json — OpenAPI 3.0.3 specification.

        Returns the complete Cargo API specification as a JSON document.
        No authentication required.  Served with CORS headers to allow
        consumption by external Swagger UI instances.
        """
        global _OPENAPI_JSON_CACHE
        if _OPENAPI_JSON_CACHE is None:
            spec = get_cargo_openapi_spec()
            # Inject the live server URL
            base_url = (
                request.env['ir.config_parameter']
                .sudo()
                .get_param('web.base.url', '')
                .rstrip('/')
            )
            spec['servers'] = [
                {'url': f'{base_url}/api/v1', 'description': 'Cargo API v1'},
            ]
            _OPENAPI_JSON_CACHE = json.dumps(spec, ensure_ascii=False, indent=2)

        return WerkzeugResponse(
            _OPENAPI_JSON_CACHE,
            status=200,
            content_type='application/json; charset=utf-8',
            headers={
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'public, max-age=300',
            },
        )

    @http.route(
        '/api/v1/docs',
        auth='none',
        methods=['GET'],
        type='http',
        csrf=False,
        save_session=False,
    )
    def cargo_swagger_ui(self, **kwargs):
        """
        GET /api/v1/docs — Swagger UI.

        Renders the Swagger UI HTML page, which loads the OpenAPI spec from
        /api/v1/openapi.json.  Uses Swagger UI 5 from unpkg CDN.
        """
        return WerkzeugResponse(
            _SWAGGER_HTML,
            status=200,
            content_type='text/html; charset=utf-8',
        )


# ── Module-level helper ───────────────────────────────────────────────────────

def _module_installed(module_name):
    """Return True if the given Odoo module is installed."""
    try:
        mod = request.env['ir.module.module'].sudo().search(
            [('name', '=', module_name), ('state', '=', 'installed')],
            limit=1,
        )
        return bool(mod)
    except Exception:
        return False
