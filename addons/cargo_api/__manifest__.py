# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
{
    'name':        'Cargo API',
    'summary':     'Versioned REST API infrastructure for all Cargo mobile and web clients.',
    'description': """
Cargo API (cargo_api)
=====================
Provides the HTTP controller base class, JWT authentication middleware,
rate limiting, pagination helpers, OpenAPI 3.0.3 specification endpoint,
and Swagger UI for all Cargo REST APIs.

This module is a PURE INFRASTRUCTURE module — it defines no business
endpoints itself.  All business routes (/api/v1/auth/*, /api/v1/stores/*,
etc.) are added by their respective Cargo modules which inherit from
CargoBaseController.

Features
--------
* Versioned REST APIs under /api/v1/
* JWT authentication via @require_cargo_auth decorator
* Per-IP rate limiting with atomic DB counters
* Standardised JSON response envelope (compatible with Flutter app)
* Pagination: page/limit with totalPages, hasNext, hasPrev metadata
* Filtering, sorting and search parameter helpers
* File and image upload utilities (multipart/form-data)
* Consistent error handling with typed error codes
* Request/response logging to cargo.audit.log
* OpenAPI 3.0.3 specification at /api/v1/openapi.json
* Swagger UI at /api/v1/docs
* Refresh token storage and revocation (cargo.api.token)
* ir.cron jobs for expired token cleanup
    """,
    'category':    'Technical',
    'version':     '18.0.1.0.0',
    'author':      'Cargo Marketplace',
    'license':      'LGPL-3',

    'depends': [
        'cargo_base',
    ],

    'data': [
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'data/cargo_api_data.xml',
        'views/cargo_api_token_views.xml',
        'views/cargo_rate_limit_views.xml',
        'views/menus.xml',
    ],

    'assets': {
        'web.assets_backend': [],
    },

    'installable':    True,
    'auto_install':   False,
    'application':    False,

    'external_dependencies': {
        'python': [],   # zero external dependencies
    },
}
