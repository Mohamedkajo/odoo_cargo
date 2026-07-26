# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
OpenAPI 3.0.3 specification for the Cargo Marketplace REST API.

The spec is built as a Python dict and serialised to JSON on each request
to /api/v1/openapi.json.  Downstream Cargo modules extend the spec by
calling ``extend_cargo_openapi_spec()`` from their own post_init_hook or
by monkey-patching ``CARGO_API_SPEC['paths']`` — whichever pattern their
module uses.

The spec includes:
  - Complete schema definitions for all Cargo data types
  - All authentication endpoints (cargo_auth module)
  - Customer, vendor, driver, notification, wallet, and admin endpoints
  - Shared parameters (pagination, filtering, sorting)
  - Standard error responses
"""

import copy

# ── Base spec skeleton ────────────────────────────────────────────────────────

CARGO_API_SPEC = {
    'openapi': '3.0.3',
    'info': {
        'title':       'Cargo Marketplace API',
        'version':     '1.0.0',
        'description': (
            'REST API for the Cargo multi-vendor delivery marketplace. '
            'Compatible with Flutter Customer, Vendor, and Driver apps.'
        ),
        'contact': {
            'name':  'Cargo Support',
            'email': 'support@cargo.eg',
        },
        'license': {
            'name': 'LGPL-3.0',
        },
    },
    'servers': [
        {'url': '/api/v1', 'description': 'Cargo API v1'},
    ],
    'security': [{'BearerAuth': []}],

    'components': {
        'securitySchemes': {
            'BearerAuth': {
                'type':         'http',
                'scheme':       'bearer',
                'bearerFormat': 'JWT',
                'description':  'JWT access token. Obtain via POST /api/v1/auth/login.',
            },
        },

        'parameters': {
            'PageParam': {
                'name': 'page', 'in': 'query', 'schema': {'type': 'integer', 'minimum': 1, 'default': 1},
                'description': 'Page number (1-based).',
            },
            'LimitParam': {
                'name': 'limit', 'in': 'query',
                'schema': {'type': 'integer', 'minimum': 1, 'maximum': 100, 'default': 20},
                'description': 'Results per page (max 100).',
            },
            'SortParam': {
                'name': 'sort', 'in': 'query', 'schema': {'type': 'string'},
                'description': 'Sort field. Prefix with - for DESC (e.g. sort=-created_at).',
            },
            'SearchParam': {
                'name': 'q', 'in': 'query', 'schema': {'type': 'string'},
                'description': 'Free-text search query.',
            },
        },

        'schemas': {

            # ── Envelope schemas ──────────────────────────────────────────────
            'SuccessResponse': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean', 'example': True},
                    'data':    {},
                    'message': {'type': 'string'},
                },
                'required': ['success'],
            },
            'ErrorResponse': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean', 'example': False},
                    'error':   {'type': 'string',  'example': 'ERR_VALIDATION'},
                    'message': {'type': 'string',  'example': 'Email is required.'},
                    'field':   {'type': 'string',  'example': 'email', 'nullable': True},
                },
                'required': ['success', 'error', 'message'],
            },
            'PaginationMeta': {
                'type': 'object',
                'properties': {
                    'page':    {'type': 'integer', 'example': 1},
                    'limit':   {'type': 'integer', 'example': 20},
                    'total':   {'type': 'integer', 'example': 154},
                    'pages':   {'type': 'integer', 'example': 8},
                    'hasNext': {'type': 'boolean', 'example': True},
                    'hasPrev': {'type': 'boolean', 'example': False},
                },
            },

            # ── Domain schemas ────────────────────────────────────────────────
            'User': {
                'type': 'object',
                'properties': {
                    'id':            {'type': 'integer', 'example': 42},
                    'name':          {'type': 'string',  'example': 'Ahmed Hassan'},
                    'email':         {'type': 'string',  'format': 'email'},
                    'phone':         {'type': 'string',  'example': '+201012345678'},
                    'avatar':        {'type': 'string',  'example': 'https://example.com/img/42.jpg'},
                    'role':          {'type': 'string',
                                     'enum': ['customer', 'vendor', 'vendor_manager',
                                              'driver', 'operations', 'finance',
                                              'admin', 'super_admin']},
                    'loyaltyPoints': {'type': 'integer', 'example': 350},
                    'address':       {'type': 'string',  'example': '12 Tahrir Square, Cairo'},
                    'walletBalance': {'type': 'number',  'example': 125.50},
                    'unreadCount':   {'type': 'integer', 'example': 3},
                },
            },
            'AuthTokens': {
                'type': 'object',
                'properties': {
                    'accessToken':  {'type': 'string', 'description': 'Short-lived JWT (24 h)'},
                    'refreshToken': {'type': 'string', 'description': 'Long-lived JWT (30 d)'},
                    'tokenType':    {'type': 'string', 'example': 'Bearer'},
                    'expiresIn':    {'type': 'integer', 'example': 86400,
                                    'description': 'Access token lifetime in seconds'},
                    'user':         {'$ref': '#/components/schemas/User'},
                },
            },
            'Category': {
                'type': 'object',
                'properties': {
                    'id':         {'type': 'integer', 'example': 5},
                    'name':       {'type': 'string',  'example': 'Burgers'},
                    'slug':       {'type': 'string',  'example': 'burgers'},
                    'icon':       {'type': 'string',  'example': 'https://example.com/img/cat5.png'},
                    'storeCount': {'type': 'integer', 'example': 12},
                    'sortOrder':  {'type': 'integer', 'example': 1},
                },
            },
            'Store': {
                'type': 'object',
                'properties': {
                    'id':             {'type': 'integer', 'example': 7},
                    'name':           {'type': 'string',  'example': 'Burger King Maadi'},
                    'slug':           {'type': 'string',  'example': 'burger-king-maadi'},
                    'description':    {'type': 'string'},
                    'logo':           {'type': 'string'},
                    'coverImage':     {'type': 'string'},
                    'categoryId':     {'type': 'integer'},
                    'categoryName':   {'type': 'string'},
                    'rating':         {'type': 'number', 'example': 4.5},
                    'reviewCount':    {'type': 'integer'},
                    'isOpen':         {'type': 'boolean'},
                    'deliveryFee':    {'type': 'number', 'example': 15.00},
                    'minOrderAmount': {'type': 'number', 'example': 50.00},
                    'estimatedTime':  {'type': 'integer', 'example': 35,
                                     'description': 'Estimated delivery time in minutes'},
                    'address':        {'type': 'string'},
                    'city':           {'type': 'string'},
                    'phone':          {'type': 'string'},
                    'tags':           {'type': 'array', 'items': {'type': 'string'}},
                    'isFeatured':     {'type': 'boolean'},
                },
            },
            'Product': {
                'type': 'object',
                'properties': {
                    'id':              {'type': 'integer'},
                    'name':            {'type': 'string'},
                    'description':     {'type': 'string'},
                    'price':           {'type': 'number', 'example': 89.99},
                    'originalPrice':   {'type': 'number', 'example': 99.99},
                    'discountPercent': {'type': 'integer', 'example': 10},
                    'image':           {'type': 'string'},
                    'storeId':         {'type': 'integer', 'nullable': True},
                    'storeName':       {'type': 'string'},
                    'categoryId':      {'type': 'integer'},
                    'categoryName':    {'type': 'string'},
                    'rating':          {'type': 'number'},
                    'reviewCount':     {'type': 'integer'},
                    'tags':            {'type': 'array', 'items': {'type': 'string'}},
                    'isAvailable':     {'type': 'boolean'},
                    'isFeatured':      {'type': 'boolean'},
                    'isTrending':      {'type': 'boolean'},
                },
            },
            'OrderItem': {
                'type': 'object',
                'properties': {
                    'productId': {'type': 'integer'},
                    'name':      {'type': 'string'},
                    'price':     {'type': 'number'},
                    'quantity':  {'type': 'integer'},
                    'image':     {'type': 'string'},
                    'subtotal':  {'type': 'number'},
                    'notes':     {'type': 'string', 'nullable': True},
                },
            },
            'Order': {
                'type': 'object',
                'properties': {
                    'id':            {'type': 'integer'},
                    'orderRef':      {'type': 'string',  'example': 'S00042'},
                    'status':        {'type': 'string',
                                     'enum': ['confirmed', 'preparing', 'ready',
                                              'collecting', 'delivering', 'otp_check',
                                              'delivered', 'cancelled']},
                    'total':         {'type': 'number'},
                    'subtotal':      {'type': 'number'},
                    'deliveryFee':   {'type': 'number'},
                    'itemCount':     {'type': 'integer'},
                    'createdAt':     {'type': 'string', 'format': 'date-time'},
                    'updatedAt':     {'type': 'string', 'format': 'date-time'},
                    'storeId':       {'type': 'integer'},
                    'storeName':     {'type': 'string'},
                    'storeImage':    {'type': 'string'},
                    'driverId':      {'type': 'integer', 'nullable': True},
                    'driverName':    {'type': 'string',  'nullable': True},
                    'driverPhone':   {'type': 'string',  'nullable': True},
                    'driverRating':  {'type': 'number',  'nullable': True},
                    'estimatedTime': {'type': 'integer', 'nullable': True},
                    'items':         {'type': 'array', 'items': {'$ref': '#/components/schemas/OrderItem'}},
                    'deliveryAddress': {'type': 'string'},
                    'notes':         {'type': 'string', 'nullable': True},
                },
            },
            'Review': {
                'type': 'object',
                'properties': {
                    'id':          {'type': 'integer'},
                    'rating':      {'type': 'number', 'minimum': 1, 'maximum': 5},
                    'comment':     {'type': 'string'},
                    'userName':    {'type': 'string'},
                    'userAvatar':  {'type': 'string'},
                    'createdAt':   {'type': 'string', 'format': 'date-time'},
                    'reviewType':  {'type': 'string', 'enum': ['store', 'product', 'driver']},
                },
            },
            'Notification': {
                'type': 'object',
                'properties': {
                    'id':        {'type': 'integer'},
                    'title':     {'type': 'string'},
                    'body':      {'type': 'string'},
                    'type':      {'type': 'string'},
                    'isRead':    {'type': 'boolean'},
                    'data':      {'type': 'object', 'nullable': True},
                    'createdAt': {'type': 'string', 'format': 'date-time'},
                },
            },
            'WalletTransaction': {
                'type': 'object',
                'properties': {
                    'id':          {'type': 'integer'},
                    'amount':      {'type': 'number'},
                    'type':        {'type': 'string', 'enum': ['credit', 'debit', 'refund', 'cashout']},
                    'description': {'type': 'string'},
                    'reference':   {'type': 'string', 'nullable': True},
                    'balance':     {'type': 'number', 'description': 'Balance after transaction'},
                    'createdAt':   {'type': 'string', 'format': 'date-time'},
                },
            },
            'VendorDashboard': {
                'type': 'object',
                'properties': {
                    'todayOrders':    {'type': 'integer'},
                    'pendingOrders':  {'type': 'integer'},
                    'todayRevenue':   {'type': 'number'},
                    'monthRevenue':   {'type': 'number'},
                    'totalProducts':  {'type': 'integer'},
                    'avgRating':      {'type': 'number'},
                    'totalReviews':   {'type': 'integer'},
                },
            },
            'DriverDashboard': {
                'type': 'object',
                'properties': {
                    'todayDeliveries':  {'type': 'integer'},
                    'todayEarnings':    {'type': 'number'},
                    'pendingPickups':   {'type': 'integer'},
                    'activeOrder':      {'$ref': '#/components/schemas/Order', 'nullable': True},
                    'totalDeliveries':  {'type': 'integer'},
                    'rating':           {'type': 'number'},
                },
            },
            'HealthResponse': {
                'type': 'object',
                'properties': {
                    'status':    {'type': 'string', 'example': 'ok'},
                    'version':   {'type': 'string', 'example': '1.0.0'},
                    'timestamp': {'type': 'string', 'format': 'date-time'},
                },
            },
        },

        'responses': {
            '400': {'description': 'Bad Request',           'content': {'application/json': {'schema': {'$ref': '#/components/schemas/ErrorResponse'}}}},
            '401': {'description': 'Unauthorized',          'content': {'application/json': {'schema': {'$ref': '#/components/schemas/ErrorResponse'}}}},
            '403': {'description': 'Forbidden',             'content': {'application/json': {'schema': {'$ref': '#/components/schemas/ErrorResponse'}}}},
            '404': {'description': 'Not Found',             'content': {'application/json': {'schema': {'$ref': '#/components/schemas/ErrorResponse'}}}},
            '409': {'description': 'Conflict',              'content': {'application/json': {'schema': {'$ref': '#/components/schemas/ErrorResponse'}}}},
            '422': {'description': 'Unprocessable Entity',  'content': {'application/json': {'schema': {'$ref': '#/components/schemas/ErrorResponse'}}}},
            '429': {'description': 'Too Many Requests',     'content': {'application/json': {'schema': {'$ref': '#/components/schemas/ErrorResponse'}}}},
            '500': {'description': 'Internal Server Error', 'content': {'application/json': {'schema': {'$ref': '#/components/schemas/ErrorResponse'}}}},
        },
    },

    'paths': {

        # ── Infrastructure ────────────────────────────────────────────────────
        '/health': {
            'get': {
                'summary':     'Health check',
                'description': 'Returns 200 OK when the API server is up. No authentication required.',
                'operationId': 'health_check',
                'tags':        ['Infrastructure'],
                'security':    [],
                'responses': {
                    '200': {
                        'description': 'Server is healthy',
                        'content': {'application/json': {'schema': {'$ref': '#/components/schemas/HealthResponse'}}},
                    },
                },
            },
        },
        '/version': {
            'get': {
                'summary':     'API version',
                'operationId': 'get_version',
                'tags':        ['Infrastructure'],
                'security':    [],
                'responses': {
                    '200': {
                        'description': 'Version information',
                        'content': {'application/json': {'schema': {'$ref': '#/components/schemas/SuccessResponse'}}},
                    },
                },
            },
        },

        # ── Auth ──────────────────────────────────────────────────────────────
        '/auth/register': {
            'post': {
                'summary': 'Register a new customer account',
                'operationId': 'auth_register',
                'tags': ['Authentication'],
                'security': [],
                'requestBody': {
                    'required': True,
                    'content': {'application/json': {'schema': {
                        'type': 'object',
                        'required': ['name', 'email', 'phone', 'password'],
                        'properties': {
                            'name':     {'type': 'string'},
                            'email':    {'type': 'string', 'format': 'email'},
                            'phone':    {'type': 'string', 'example': '01012345678'},
                            'password': {'type': 'string', 'minLength': 6},
                        },
                    }}},
                },
                'responses': {
                    '201': {'description': 'Account created', 'content': {'application/json': {'schema': {'$ref': '#/components/schemas/AuthTokens'}}}},
                    '400': {'$ref': '#/components/responses/400'},
                    '409': {'$ref': '#/components/responses/409'},
                },
            },
        },
        '/auth/login': {
            'post': {
                'summary': 'Log in and obtain JWT tokens',
                'operationId': 'auth_login',
                'tags': ['Authentication'],
                'security': [],
                'requestBody': {
                    'required': True,
                    'content': {'application/json': {'schema': {
                        'type': 'object',
                        'required': ['email', 'password'],
                        'properties': {
                            'email':    {'type': 'string', 'format': 'email'},
                            'password': {'type': 'string'},
                        },
                    }}},
                },
                'responses': {
                    '200': {'description': 'Login successful', 'content': {'application/json': {'schema': {'$ref': '#/components/schemas/AuthTokens'}}}},
                    '401': {'$ref': '#/components/responses/401'},
                },
            },
        },
        '/auth/refresh': {
            'post': {
                'summary': 'Refresh access token using a refresh token',
                'operationId': 'auth_refresh',
                'tags': ['Authentication'],
                'security': [],
                'requestBody': {
                    'required': True,
                    'content': {'application/json': {'schema': {
                        'type': 'object', 'required': ['refreshToken'],
                        'properties': {'refreshToken': {'type': 'string'}},
                    }}},
                },
                'responses': {
                    '200': {'description': 'New access token issued', 'content': {'application/json': {'schema': {'$ref': '#/components/schemas/AuthTokens'}}}},
                    '401': {'$ref': '#/components/responses/401'},
                },
            },
        },
        '/auth/logout': {
            'post': {
                'summary':     'Log out and revoke the current refresh token',
                'operationId': 'auth_logout',
                'tags': ['Authentication'],
                'responses': {
                    '204': {'description': 'Logged out successfully'},
                    '401': {'$ref': '#/components/responses/401'},
                },
            },
        },
        '/auth/me': {
            'get': {
                'summary': 'Get the authenticated user profile',
                'operationId': 'auth_me_get',
                'tags': ['Authentication'],
                'responses': {
                    '200': {'description': 'User profile', 'content': {'application/json': {'schema': {'$ref': '#/components/schemas/User'}}}},
                    '401': {'$ref': '#/components/responses/401'},
                },
            },
            'patch': {
                'summary': 'Update the authenticated user profile',
                'operationId': 'auth_me_patch',
                'tags': ['Authentication'],
                'requestBody': {
                    'content': {'application/json': {'schema': {
                        'type': 'object',
                        'properties': {
                            'name':  {'type': 'string'},
                            'phone': {'type': 'string'},
                        },
                    }}},
                },
                'responses': {
                    '200': {'description': 'Profile updated', 'content': {'application/json': {'schema': {'$ref': '#/components/schemas/User'}}}},
                    '400': {'$ref': '#/components/responses/400'},
                    '401': {'$ref': '#/components/responses/401'},
                },
            },
        },
        '/auth/password': {
            'patch': {
                'summary': 'Change password',
                'operationId': 'auth_change_password',
                'tags': ['Authentication'],
                'requestBody': {
                    'required': True,
                    'content': {'application/json': {'schema': {
                        'type': 'object',
                        'required': ['currentPassword', 'newPassword'],
                        'properties': {
                            'currentPassword': {'type': 'string'},
                            'newPassword':     {'type': 'string', 'minLength': 6},
                        },
                    }}},
                },
                'responses': {
                    '200': {'description': 'Password changed'},
                    '400': {'$ref': '#/components/responses/400'},
                    '401': {'$ref': '#/components/responses/401'},
                },
            },
        },
        '/auth/avatar': {
            'post': {
                'summary': 'Upload or replace profile avatar',
                'operationId': 'auth_upload_avatar',
                'tags': ['Authentication'],
                'requestBody': {
                    'required': True,
                    'content': {'multipart/form-data': {'schema': {
                        'type': 'object',
                        'required': ['image'],
                        'properties': {'image': {'type': 'string', 'format': 'binary'}},
                    }}},
                },
                'responses': {
                    '200': {'description': 'Avatar updated'},
                    '400': {'$ref': '#/components/responses/400'},
                    '401': {'$ref': '#/components/responses/401'},
                },
            },
        },

        # ── Categories ────────────────────────────────────────────────────────
        '/categories': {
            'get': {
                'summary': 'List all product categories',
                'operationId': 'list_categories',
                'tags': ['Catalog'],
                'security': [],
                'parameters': [
                    {'$ref': '#/components/parameters/SearchParam'},
                ],
                'responses': {
                    '200': {'description': 'Category list', 'content': {'application/json': {'schema': {
                        'allOf': [
                            {'$ref': '#/components/schemas/SuccessResponse'},
                            {'type': 'object', 'properties': {'data': {'type': 'array', 'items': {'$ref': '#/components/schemas/Category'}}}},
                        ],
                    }}}},
                },
            },
        },

        # ── Stores ────────────────────────────────────────────────────────────
        '/stores': {
            'get': {
                'summary': 'List stores (with optional category filter)',
                'operationId': 'list_stores',
                'tags': ['Stores'],
                'security': [],
                'parameters': [
                    {'$ref': '#/components/parameters/PageParam'},
                    {'$ref': '#/components/parameters/LimitParam'},
                    {'$ref': '#/components/parameters/SortParam'},
                    {'$ref': '#/components/parameters/SearchParam'},
                    {'name': 'filter[categoryId]', 'in': 'query', 'schema': {'type': 'integer'}},
                    {'name': 'filter[isOpen]',     'in': 'query', 'schema': {'type': 'boolean'}},
                    {'name': 'filter[isFeatured]', 'in': 'query', 'schema': {'type': 'boolean'}},
                ],
                'responses': {
                    '200': {'description': 'Paginated store list', 'content': {'application/json': {'schema': {'$ref': '#/components/schemas/SuccessResponse'}}}},
                },
            },
        },
        '/stores/{id}': {
            'get': {
                'summary': 'Get store details',
                'operationId': 'get_store',
                'tags': ['Stores'],
                'security': [],
                'parameters': [{'name': 'id', 'in': 'path', 'required': True, 'schema': {'type': 'integer'}}],
                'responses': {
                    '200': {'description': 'Store details', 'content': {'application/json': {'schema': {'$ref': '#/components/schemas/Store'}}}},
                    '404': {'$ref': '#/components/responses/404'},
                },
            },
        },
        '/stores/{id}/products': {
            'get': {
                'summary': 'List products for a specific store',
                'operationId': 'list_store_products',
                'tags': ['Stores'],
                'security': [],
                'parameters': [
                    {'name': 'id', 'in': 'path', 'required': True, 'schema': {'type': 'integer'}},
                    {'$ref': '#/components/parameters/PageParam'},
                    {'$ref': '#/components/parameters/LimitParam'},
                    {'$ref': '#/components/parameters/SearchParam'},
                ],
                'responses': {'200': {'description': 'Store products'}},
            },
        },

        # ── Products ──────────────────────────────────────────────────────────
        '/products': {
            'get': {
                'summary': 'List products across all stores',
                'operationId': 'list_products',
                'tags': ['Products'],
                'security': [],
                'parameters': [
                    {'$ref': '#/components/parameters/PageParam'},
                    {'$ref': '#/components/parameters/LimitParam'},
                    {'$ref': '#/components/parameters/SortParam'},
                    {'$ref': '#/components/parameters/SearchParam'},
                    {'name': 'filter[categoryId]',  'in': 'query', 'schema': {'type': 'integer'}},
                    {'name': 'filter[isFeatured]',  'in': 'query', 'schema': {'type': 'boolean'}},
                    {'name': 'filter[isTrending]',  'in': 'query', 'schema': {'type': 'boolean'}},
                    {'name': 'filter[isAvailable]', 'in': 'query', 'schema': {'type': 'boolean'}},
                ],
                'responses': {'200': {'description': 'Paginated product list'}},
            },
        },
        '/products/{id}': {
            'get': {
                'summary': 'Get product details',
                'operationId': 'get_product',
                'tags': ['Products'],
                'security': [],
                'parameters': [{'name': 'id', 'in': 'path', 'required': True, 'schema': {'type': 'integer'}}],
                'responses': {
                    '200': {'description': 'Product details', 'content': {'application/json': {'schema': {'$ref': '#/components/schemas/Product'}}}},
                    '404': {'$ref': '#/components/responses/404'},
                },
            },
        },

        # ── Orders (customer) ─────────────────────────────────────────────────
        '/orders': {
            'get': {
                'summary': 'List authenticated customer orders',
                'operationId': 'list_orders',
                'tags': ['Orders'],
                'parameters': [
                    {'$ref': '#/components/parameters/PageParam'},
                    {'$ref': '#/components/parameters/LimitParam'},
                    {'name': 'filter[status]', 'in': 'query', 'schema': {'type': 'string'}},
                ],
                'responses': {'200': {'description': 'Paginated order list'}},
            },
            'post': {
                'summary': 'Place a new order',
                'operationId': 'create_order',
                'tags': ['Orders'],
                'requestBody': {
                    'required': True,
                    'content': {'application/json': {'schema': {
                        'type': 'object',
                        'required': ['storeId', 'items', 'deliveryAddress'],
                        'properties': {
                            'storeId':         {'type': 'integer'},
                            'deliveryAddress': {'type': 'string'},
                            'notes':           {'type': 'string'},
                            'items': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'required': ['productId', 'quantity'],
                                    'properties': {
                                        'productId': {'type': 'integer'},
                                        'quantity':  {'type': 'integer', 'minimum': 1},
                                        'notes':     {'type': 'string'},
                                    },
                                },
                            },
                        },
                    }}},
                },
                'responses': {
                    '201': {'description': 'Order created', 'content': {'application/json': {'schema': {'$ref': '#/components/schemas/Order'}}}},
                    '400': {'$ref': '#/components/responses/400'},
                    '422': {'$ref': '#/components/responses/422'},
                },
            },
        },
        '/orders/{id}': {
            'get': {
                'summary': 'Get order details',
                'operationId': 'get_order',
                'tags': ['Orders'],
                'parameters': [{'name': 'id', 'in': 'path', 'required': True, 'schema': {'type': 'integer'}}],
                'responses': {
                    '200': {'description': 'Order details', 'content': {'application/json': {'schema': {'$ref': '#/components/schemas/Order'}}}},
                    '403': {'$ref': '#/components/responses/403'},
                    '404': {'$ref': '#/components/responses/404'},
                },
            },
        },
        '/orders/{id}/cancel': {
            'post': {
                'summary': 'Cancel a pending order',
                'operationId': 'cancel_order',
                'tags': ['Orders'],
                'parameters': [{'name': 'id', 'in': 'path', 'required': True, 'schema': {'type': 'integer'}}],
                'responses': {
                    '200': {'description': 'Order cancelled'},
                    '403': {'$ref': '#/components/responses/403'},
                    '404': {'$ref': '#/components/responses/404'},
                    '422': {'$ref': '#/components/responses/422'},
                },
            },
        },
        '/orders/{id}/rate': {
            'post': {
                'summary': 'Rate a delivered order',
                'operationId': 'rate_order',
                'tags': ['Orders'],
                'parameters': [{'name': 'id', 'in': 'path', 'required': True, 'schema': {'type': 'integer'}}],
                'requestBody': {
                    'required': True,
                    'content': {'application/json': {'schema': {
                        'type': 'object',
                        'required': ['storeRating'],
                        'properties': {
                            'storeRating':   {'type': 'number', 'minimum': 1, 'maximum': 5},
                            'driverRating':  {'type': 'number', 'minimum': 1, 'maximum': 5},
                            'storeComment':  {'type': 'string'},
                            'driverComment': {'type': 'string'},
                        },
                    }}},
                },
                'responses': {
                    '200': {'description': 'Rating submitted'},
                    '422': {'$ref': '#/components/responses/422'},
                },
            },
        },

        # ── Notifications ─────────────────────────────────────────────────────
        '/notifications': {
            'get': {
                'summary': 'List notifications for the authenticated user',
                'operationId': 'list_notifications',
                'tags': ['Notifications'],
                'parameters': [
                    {'$ref': '#/components/parameters/PageParam'},
                    {'$ref': '#/components/parameters/LimitParam'},
                    {'name': 'filter[isRead]', 'in': 'query', 'schema': {'type': 'boolean'}},
                ],
                'responses': {'200': {'description': 'Paginated notifications'}},
            },
        },
        '/notifications/{id}/read': {
            'patch': {
                'summary': 'Mark a notification as read',
                'operationId': 'mark_notification_read',
                'tags': ['Notifications'],
                'parameters': [{'name': 'id', 'in': 'path', 'required': True, 'schema': {'type': 'integer'}}],
                'responses': {'200': {'description': 'Marked as read'}},
            },
        },
        '/notifications/read-all': {
            'post': {
                'summary': 'Mark all notifications as read',
                'operationId': 'mark_all_notifications_read',
                'tags': ['Notifications'],
                'responses': {'200': {'description': 'All notifications marked as read'}},
            },
        },

        # ── Wallet ────────────────────────────────────────────────────────────
        '/wallet': {
            'get': {
                'summary': 'Get wallet balance and summary',
                'operationId': 'get_wallet',
                'tags': ['Wallet'],
                'responses': {'200': {'description': 'Wallet summary'}},
            },
        },
        '/wallet/history': {
            'get': {
                'summary': 'List wallet transactions',
                'operationId': 'list_wallet_history',
                'tags': ['Wallet'],
                'parameters': [
                    {'$ref': '#/components/parameters/PageParam'},
                    {'$ref': '#/components/parameters/LimitParam'},
                ],
                'responses': {'200': {'description': 'Paginated transaction history'}},
            },
        },

        # ── Vendor ────────────────────────────────────────────────────────────
        '/vendor/dashboard': {
            'get': {
                'summary': 'Vendor dashboard statistics',
                'operationId': 'vendor_dashboard',
                'tags': ['Vendor'],
                'responses': {
                    '200': {'description': 'Dashboard data', 'content': {'application/json': {'schema': {'$ref': '#/components/schemas/VendorDashboard'}}}},
                    '403': {'$ref': '#/components/responses/403'},
                },
            },
        },
        '/vendor/orders': {
            'get': {
                'summary': 'List incoming orders for the vendor store',
                'operationId': 'vendor_list_orders',
                'tags': ['Vendor'],
                'parameters': [
                    {'$ref': '#/components/parameters/PageParam'},
                    {'$ref': '#/components/parameters/LimitParam'},
                    {'name': 'filter[status]', 'in': 'query', 'schema': {'type': 'string'}},
                ],
                'responses': {'200': {'description': 'Paginated vendor orders'}},
            },
        },
        '/vendor/orders/{id}/status': {
            'patch': {
                'summary': 'Update order status (vendor workflow)',
                'operationId': 'vendor_update_order_status',
                'tags': ['Vendor'],
                'parameters': [{'name': 'id', 'in': 'path', 'required': True, 'schema': {'type': 'integer'}}],
                'requestBody': {
                    'required': True,
                    'content': {'application/json': {'schema': {
                        'type': 'object',
                        'required': ['status'],
                        'properties': {
                            'status':           {'type': 'string'},
                            'estimatedMinutes': {'type': 'integer'},
                        },
                    }}},
                },
                'responses': {
                    '200': {'description': 'Status updated'},
                    '422': {'$ref': '#/components/responses/422'},
                },
            },
        },
        '/vendor/products': {
            'get': {
                'summary': 'List vendor products',
                'operationId': 'vendor_list_products',
                'tags': ['Vendor'],
                'parameters': [
                    {'$ref': '#/components/parameters/PageParam'},
                    {'$ref': '#/components/parameters/LimitParam'},
                    {'$ref': '#/components/parameters/SearchParam'},
                ],
                'responses': {'200': {'description': 'Vendor product list'}},
            },
            'post': {
                'summary': 'Create a new product',
                'operationId': 'vendor_create_product',
                'tags': ['Vendor'],
                'responses': {
                    '201': {'description': 'Product created'},
                    '400': {'$ref': '#/components/responses/400'},
                },
            },
        },
        '/vendor/products/{id}': {
            'get':    {'summary': 'Get vendor product',    'operationId': 'vendor_get_product',    'tags': ['Vendor'], 'parameters': [{'name': 'id', 'in': 'path', 'required': True, 'schema': {'type': 'integer'}}], 'responses': {'200': {'description': 'Product'}, '404': {'$ref': '#/components/responses/404'}}},
            'patch':  {'summary': 'Update vendor product', 'operationId': 'vendor_update_product', 'tags': ['Vendor'], 'parameters': [{'name': 'id', 'in': 'path', 'required': True, 'schema': {'type': 'integer'}}], 'responses': {'200': {'description': 'Updated'}, '400': {'$ref': '#/components/responses/400'}}},
            'delete': {'summary': 'Delete vendor product', 'operationId': 'vendor_delete_product', 'tags': ['Vendor'], 'parameters': [{'name': 'id', 'in': 'path', 'required': True, 'schema': {'type': 'integer'}}], 'responses': {'204': {'description': 'Deleted'}}},
        },

        # ── Driver ────────────────────────────────────────────────────────────
        '/driver/dashboard': {
            'get': {
                'summary': 'Driver dashboard',
                'operationId': 'driver_dashboard',
                'tags': ['Driver'],
                'responses': {
                    '200': {'description': 'Dashboard data', 'content': {'application/json': {'schema': {'$ref': '#/components/schemas/DriverDashboard'}}}},
                    '403': {'$ref': '#/components/responses/403'},
                },
            },
        },
        '/driver/orders': {
            'get': {
                'summary': 'List available and active orders for the driver',
                'operationId': 'driver_list_orders',
                'tags': ['Driver'],
                'parameters': [
                    {'$ref': '#/components/parameters/PageParam'},
                    {'$ref': '#/components/parameters/LimitParam'},
                    {'name': 'filter[status]', 'in': 'query', 'schema': {'type': 'string'}},
                ],
                'responses': {'200': {'description': 'Driver order list'}},
            },
        },
        '/driver/orders/{id}/accept': {
            'post': {
                'summary': 'Accept a ready order for pickup',
                'operationId': 'driver_accept_order',
                'tags': ['Driver'],
                'parameters': [{'name': 'id', 'in': 'path', 'required': True, 'schema': {'type': 'integer'}}],
                'responses': {'200': {'description': 'Order accepted'}, '422': {'$ref': '#/components/responses/422'}},
            },
        },
        '/driver/orders/{id}/pickup': {
            'post': {
                'summary': 'Confirm order has been picked up from store',
                'operationId': 'driver_pickup_order',
                'tags': ['Driver'],
                'parameters': [{'name': 'id', 'in': 'path', 'required': True, 'schema': {'type': 'integer'}}],
                'responses': {'200': {'description': 'Pickup confirmed'}},
            },
        },
        '/driver/orders/{id}/verify-otp': {
            'post': {
                'summary': 'Verify customer OTP and complete delivery',
                'operationId': 'driver_verify_otp',
                'tags': ['Driver'],
                'parameters': [{'name': 'id', 'in': 'path', 'required': True, 'schema': {'type': 'integer'}}],
                'requestBody': {
                    'required': True,
                    'content': {'application/json': {'schema': {
                        'type': 'object', 'required': ['otp'],
                        'properties': {'otp': {'type': 'string', 'example': '4821'}},
                    }}},
                },
                'responses': {
                    '200': {'description': 'OTP verified, delivery complete'},
                    '400': {'$ref': '#/components/responses/400'},
                },
            },
        },
        '/driver/location': {
            'patch': {
                'summary': 'Update driver GPS location',
                'operationId': 'driver_update_location',
                'tags': ['Driver'],
                'requestBody': {
                    'required': True,
                    'content': {'application/json': {'schema': {
                        'type': 'object',
                        'required': ['latitude', 'longitude'],
                        'properties': {
                            'latitude':  {'type': 'number', 'example': 30.0444},
                            'longitude': {'type': 'number', 'example': 31.2357},
                        },
                    }}},
                },
                'responses': {'200': {'description': 'Location updated'}},
            },
        },

        # ── Admin ─────────────────────────────────────────────────────────────
        '/admin/users': {
            'get': {
                'summary': 'List all platform users (admin)',
                'operationId': 'admin_list_users',
                'tags': ['Admin'],
                'parameters': [
                    {'$ref': '#/components/parameters/PageParam'},
                    {'$ref': '#/components/parameters/LimitParam'},
                    {'$ref': '#/components/parameters/SearchParam'},
                    {'name': 'filter[role]', 'in': 'query', 'schema': {'type': 'string'}},
                ],
                'responses': {'200': {'description': 'User list'}, '403': {'$ref': '#/components/responses/403'}},
            },
        },
        '/admin/stores': {
            'get':  {'summary': 'List all stores (admin)',   'operationId': 'admin_list_stores',  'tags': ['Admin'], 'responses': {'200': {'description': 'Store list'}}},
            'post': {'summary': 'Create a store (admin)',    'operationId': 'admin_create_store', 'tags': ['Admin'], 'responses': {'201': {'description': 'Created'}, '400': {'$ref': '#/components/responses/400'}}},
        },
        '/admin/orders': {
            'get': {
                'summary': 'List all orders (admin)',
                'operationId': 'admin_list_orders',
                'tags': ['Admin'],
                'parameters': [
                    {'$ref': '#/components/parameters/PageParam'},
                    {'$ref': '#/components/parameters/LimitParam'},
                    {'name': 'filter[status]', 'in': 'query', 'schema': {'type': 'string'}},
                ],
                'responses': {'200': {'description': 'Order list'}},
            },
        },
        '/admin/analytics': {
            'get': {
                'summary': 'Platform-wide analytics (admin)',
                'operationId': 'admin_analytics',
                'tags': ['Admin'],
                'responses': {'200': {'description': 'Analytics data'}},
            },
        },
    },

    'tags': [
        {'name': 'Infrastructure',  'description': 'Health check, versioning and API documentation'},
        {'name': 'Authentication',  'description': 'Registration, login, token management and profile'},
        {'name': 'Catalog',         'description': 'Product categories'},
        {'name': 'Stores',          'description': 'Store discovery and details'},
        {'name': 'Products',        'description': 'Product browsing and details'},
        {'name': 'Orders',          'description': 'Customer order placement and tracking'},
        {'name': 'Notifications',   'description': 'In-app push notifications'},
        {'name': 'Wallet',          'description': 'Digital wallet and transaction history'},
        {'name': 'Vendor',          'description': 'Vendor store management and order processing'},
        {'name': 'Driver',          'description': 'Driver delivery workflow'},
        {'name': 'Admin',           'description': 'Platform administration (admin role required)'},
    ],
}


def get_cargo_openapi_spec():
    """Return a deep copy of the OpenAPI spec dict (safe for serialisation)."""
    return copy.deepcopy(CARGO_API_SPEC)


def extend_cargo_openapi_spec(paths=None, schemas=None, tags=None):
    """
    Allow downstream Cargo modules to extend the shared OpenAPI spec.

    Args:
        paths   : dict of new path entries to merge into spec['paths']
        schemas : dict of new schema entries to merge into spec['components']['schemas']
        tags    : list of new tag objects to append to spec['tags']
    """
    if paths:
        CARGO_API_SPEC['paths'].update(paths)
    if schemas:
        CARGO_API_SPEC['components']['schemas'].update(schemas)
    if tags:
        existing_names = {t['name'] for t in CARGO_API_SPEC.get('tags', [])}
        for tag in tags:
            if tag.get('name') not in existing_names:
                CARGO_API_SPEC.setdefault('tags', []).append(tag)
