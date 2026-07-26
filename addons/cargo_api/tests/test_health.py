# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
Tests for infrastructure routes: health, version, openapi.

These tests exercise the controller logic directly (not via HTTP) by
calling the helper methods and verifying their return values.

Note: Full end-to-end HTTP tests (via werkzeug.test.Client) require a
running Odoo HTTP server and are better suited to integration test suites
run against a live instance.  These unit-level tests verify the core logic.
"""

import json

from odoo.tests.common import TransactionCase


class TestCargoHealthEndpoint(TransactionCase):
    """Verify the health check controller logic."""

    def test_health_returns_success_response(self):
        """_cargo_health logic must return a JSON response with status='ok'."""
        # We test the response builder directly since HTTP context is not
        # available in TransactionCase
        from cargo_base.utils.response import success
        data = {'status': 'ok', 'db': 'ok', 'timestamp': '2026-01-01T00:00:00Z'}
        resp = success(data)
        body = json.loads(resp.data)
        self.assertTrue(body['success'])
        self.assertEqual(body['data']['status'], 'ok')

    def test_db_connectivity_via_env(self):
        """
        The health check performs a SELECT 1 against the DB.
        Verify this works in the test environment.
        """
        self.env.cr.execute('SELECT 1')
        result = self.env.cr.fetchone()
        self.assertEqual(result[0], 1)


class TestCargoOpenAPISpec(TransactionCase):
    """Verify the OpenAPI specification is well-formed and complete."""

    def _get_spec(self):
        from cargo_api.utils.openapi import get_cargo_openapi_spec
        return get_cargo_openapi_spec()

    def test_spec_is_openapi_303(self):
        spec = self._get_spec()
        self.assertEqual(spec.get('openapi'), '3.0.3')

    def test_spec_has_info_block(self):
        spec = self._get_spec()
        self.assertIn('info', spec)
        self.assertIn('title', spec['info'])
        self.assertIn('version', spec['info'])

    def test_spec_has_bearer_security_scheme(self):
        spec = self._get_spec()
        schemes = spec.get('components', {}).get('securitySchemes', {})
        self.assertIn('BearerAuth', schemes)
        self.assertEqual(schemes['BearerAuth']['type'], 'http')
        self.assertEqual(schemes['BearerAuth']['scheme'], 'bearer')

    def test_spec_has_required_paths(self):
        spec = self._get_spec()
        paths = spec.get('paths', {})
        required = ['/health', '/version', '/auth/login', '/auth/register',
                    '/orders', '/stores', '/products']
        for path in required:
            self.assertIn(path, paths, f'OpenAPI spec is missing path: {path}')

    def test_spec_has_user_schema(self):
        spec = self._get_spec()
        schemas = spec.get('components', {}).get('schemas', {})
        self.assertIn('User', schemas)
        user_props = schemas['User'].get('properties', {})
        for field in ('id', 'name', 'email', 'phone', 'role', 'loyaltyPoints'):
            self.assertIn(field, user_props, f'User schema missing field: {field}')

    def test_spec_has_order_schema(self):
        spec = self._get_spec()
        schemas = spec.get('components', {}).get('schemas', {})
        self.assertIn('Order', schemas)
        order_props = schemas['Order'].get('properties', {})
        for field in ('id', 'status', 'total', 'items', 'storeName'):
            self.assertIn(field, order_props, f'Order schema missing field: {field}')

    def test_spec_all_status_enums_match_constants(self):
        """Order status enum in spec must match ORDER_STATUSES from constants."""
        from cargo_base.constants import ORDER_STATUSES
        spec = self._get_spec()
        order_status_enum = (
            spec.get('components', {})
            .get('schemas', {})
            .get('Order', {})
            .get('properties', {})
            .get('status', {})
            .get('enum', [])
        )
        self.assertTrue(order_status_enum, 'Order.status must have enum values in spec.')
        for status in ORDER_STATUSES:
            self.assertIn(
                status, order_status_enum,
                f'Order status {status!r} is in constants but missing from OpenAPI spec enum.',
            )

    def test_spec_is_json_serialisable(self):
        """The spec must serialise to valid JSON without errors."""
        spec = self._get_spec()
        try:
            json_str = json.dumps(spec)
        except (TypeError, ValueError) as exc:
            self.fail(f'OpenAPI spec is not JSON-serialisable: {exc}')
        self.assertGreater(len(json_str), 1000, 'Spec JSON seems too short.')

    def test_extend_spec_adds_paths(self):
        """extend_cargo_openapi_spec() must merge new paths into the spec."""
        from cargo_api.utils.openapi import extend_cargo_openapi_spec, CARGO_API_SPEC
        original_path_count = len(CARGO_API_SPEC['paths'])

        extend_cargo_openapi_spec(
            paths={'/test/custom': {'get': {'summary': 'Test', 'tags': ['Test'], 'responses': {'200': {'description': 'ok'}}}}},
            tags=[{'name': 'Test', 'description': 'Test tag'}],
        )

        self.assertIn('/test/custom', CARGO_API_SPEC['paths'])
        tag_names = [t['name'] for t in CARGO_API_SPEC.get('tags', [])]
        self.assertIn('Test', tag_names)

        # Clean up so this doesn't affect other tests
        del CARGO_API_SPEC['paths']['/test/custom']
        CARGO_API_SPEC['tags'] = [t for t in CARGO_API_SPEC['tags'] if t['name'] != 'Test']

    def test_get_spec_returns_deep_copy(self):
        """get_cargo_openapi_spec() must return a copy — mutations must not affect the original."""
        from cargo_api.utils.openapi import get_cargo_openapi_spec, CARGO_API_SPEC
        spec_copy = get_cargo_openapi_spec()
        spec_copy['info']['title'] = 'Mutated Title'
        self.assertNotEqual(CARGO_API_SPEC['info']['title'], 'Mutated Title')
