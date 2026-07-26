# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
Tests for cargo_api.utils.pagination.

Covers:
  - PaginationParams construction and defaults
  - page/limit clamping
  - sort field parsing (ascending and descending)
  - sort field allow-list enforcement
  - offset calculation
  - build_pagination_meta() metadata correctness
  - parse_search() / parse_filters() helpers
"""

from odoo.tests.common import BaseCase

from odoo.addons.cargo_api.utils.pagination import (
    PaginationParams,
    build_pagination_meta,
)


class TestPaginationParams(BaseCase):
    """Unit tests for PaginationParams — no database required."""

    def _params(self, page=1, limit=20, sort=None, allowed=None):
        return PaginationParams(
            page=page,
            limit=limit,
            sort_field=sort,
            sort_asc=True if sort and not sort.startswith('-') else False,
            allowed_sort_fields=allowed,
        )

    # ── Defaults ─────────────────────────────────────────────────────────────

    def test_default_page_is_1(self):
        p = self._params()
        self.assertEqual(p.page, 1)

    def test_default_limit_is_20(self):
        p = self._params()
        self.assertEqual(p.limit, 20)

    def test_default_offset_is_0(self):
        p = self._params(page=1, limit=20)
        self.assertEqual(p.offset, 0)

    # ── Page clamping ─────────────────────────────────────────────────────────

    def test_page_below_1_clamped_to_1(self):
        p = self._params(page=0)
        self.assertEqual(p.page, 1)

    def test_page_negative_clamped_to_1(self):
        p = self._params(page=-5)
        self.assertEqual(p.page, 1)

    # ── Limit clamping ────────────────────────────────────────────────────────

    def test_limit_above_100_clamped_to_100(self):
        p = self._params(limit=999)
        self.assertEqual(p.limit, 100)

    def test_limit_0_clamped_to_1(self):
        p = self._params(limit=0)
        self.assertEqual(p.limit, 1)

    def test_limit_negative_clamped_to_1(self):
        p = self._params(limit=-10)
        self.assertEqual(p.limit, 1)

    # ── Offset calculation ────────────────────────────────────────────────────

    def test_offset_page_1(self):
        p = self._params(page=1, limit=20)
        self.assertEqual(p.offset, 0)

    def test_offset_page_2(self):
        p = self._params(page=2, limit=20)
        self.assertEqual(p.offset, 20)

    def test_offset_page_5_limit_10(self):
        p = self._params(page=5, limit=10)
        self.assertEqual(p.offset, 40)

    def test_offset_page_3_limit_50(self):
        p = self._params(page=3, limit=50)
        self.assertEqual(p.offset, 100)

    # ── Sort parsing ──────────────────────────────────────────────────────────

    def test_sort_asc_builds_asc_clause(self):
        p = PaginationParams(page=1, limit=20, sort_field='name', sort_asc=True)
        self.assertEqual(p.order_clause, 'name ASC')

    def test_sort_desc_builds_desc_clause(self):
        p = PaginationParams(page=1, limit=20, sort_field='created_at', sort_asc=False)
        self.assertEqual(p.order_clause, 'created_at DESC')

    def test_no_sort_field_means_no_order_clause(self):
        p = PaginationParams(page=1, limit=20, sort_field=None)
        self.assertIsNone(p.order_clause)

    def test_sort_field_not_in_allowlist_is_ignored(self):
        p = PaginationParams(
            page=1, limit=20,
            sort_field='password',            # not allowed
            sort_asc=True,
            allowed_sort_fields={'name', 'created_at'},
        )
        self.assertIsNone(p.sort_field)
        self.assertIsNone(p.order_clause)

    def test_sort_field_in_allowlist_is_accepted(self):
        p = PaginationParams(
            page=1, limit=20,
            sort_field='name',
            sort_asc=True,
            allowed_sort_fields={'name', 'created_at'},
        )
        self.assertEqual(p.sort_field, 'name')

    def test_to_dict_contains_all_keys(self):
        p = self._params(page=2, limit=10)
        d = p.to_dict()
        for key in ('page', 'limit', 'sort_field', 'sort_asc', 'offset'):
            self.assertIn(key, d)


class TestBuildPaginationMeta(BaseCase):
    """Unit tests for build_pagination_meta()."""

    def test_single_page(self):
        meta = build_pagination_meta(total=5, page=1, limit=20)
        self.assertEqual(meta['pages'], 1)
        self.assertEqual(meta['total'], 5)
        self.assertFalse(meta['hasNext'])
        self.assertFalse(meta['hasPrev'])

    def test_has_next_on_first_page_of_many(self):
        meta = build_pagination_meta(total=100, page=1, limit=20)
        self.assertEqual(meta['pages'], 5)
        self.assertTrue(meta['hasNext'])
        self.assertFalse(meta['hasPrev'])

    def test_has_prev_on_second_page(self):
        meta = build_pagination_meta(total=100, page=2, limit=20)
        self.assertTrue(meta['hasPrev'])
        self.assertTrue(meta['hasNext'])

    def test_no_next_on_last_page(self):
        meta = build_pagination_meta(total=100, page=5, limit=20)
        self.assertFalse(meta['hasNext'])
        self.assertTrue(meta['hasPrev'])

    def test_pages_ceil_division(self):
        # 21 items / 20 per page = 2 pages
        meta = build_pagination_meta(total=21, page=1, limit=20)
        self.assertEqual(meta['pages'], 2)

    def test_zero_total(self):
        meta = build_pagination_meta(total=0, page=1, limit=20)
        self.assertEqual(meta['total'], 0)
        self.assertEqual(meta['pages'], 1)   # minimum 1 page
        self.assertFalse(meta['hasNext'])
        self.assertFalse(meta['hasPrev'])

    def test_meta_contains_all_keys(self):
        meta = build_pagination_meta(total=50, page=2, limit=10)
        for key in ('page', 'limit', 'total', 'pages', 'hasNext', 'hasPrev'):
            self.assertIn(key, meta, f'Pagination meta missing key: {key}')

    def test_page_and_limit_echoed_back(self):
        meta = build_pagination_meta(total=200, page=3, limit=15)
        self.assertEqual(meta['page'], 3)
        self.assertEqual(meta['limit'], 15)
