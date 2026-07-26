# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
Unit tests for cargo_base.utils.validators.

All tests are pure Python — no database interaction required.
"""

from odoo.tests.common import BaseCase

from ..exceptions import CargoMissingFieldError, CargoInvalidFieldError
from ..utils.validators import (
    require,
    require_str,
    optional_str,
    require_int,
    require_float,
    require_positive,
    validate_email,
    validate_phone,
    validate_password,
    validate_rating,
    validate_otp,
    validate_pagination,
    pagination_offset,
    validate_selection,
)


class TestRequireValidators(BaseCase):

    def test_require_raises_on_none(self):
        with self.assertRaises(CargoMissingFieldError):
            require(None, 'test_field')

    def test_require_raises_on_empty_string(self):
        with self.assertRaises(CargoMissingFieldError):
            require('', 'test_field')

    def test_require_passes_zero(self):
        """Zero is a valid value — must not be treated as missing."""
        self.assertEqual(require(0, 'field'), 0)

    def test_require_passes_false(self):
        self.assertFalse(require(False, 'field'))

    def test_require_str_strips_whitespace(self):
        self.assertEqual(require_str('  hello  ', 'f'), 'hello')

    def test_require_str_raises_on_too_long(self):
        with self.assertRaises(CargoInvalidFieldError):
            require_str('x' * 101, 'f', max_length=100)

    def test_optional_str_returns_empty_on_none(self):
        self.assertEqual(optional_str(None, 'f'), '')

    def test_optional_str_returns_empty_on_blank(self):
        self.assertEqual(optional_str('  ', 'f'), '')

    def test_require_int_valid(self):
        self.assertEqual(require_int('42', 'n'), 42)

    def test_require_int_invalid(self):
        with self.assertRaises(CargoInvalidFieldError):
            require_int('abc', 'n')

    def test_require_int_min_violation(self):
        with self.assertRaises(CargoInvalidFieldError):
            require_int(-1, 'n', min_val=0)

    def test_require_float_valid(self):
        self.assertAlmostEqual(require_float('3.14', 'f'), 3.14)

    def test_require_positive_raises_on_zero(self):
        with self.assertRaises(CargoInvalidFieldError):
            require_positive(0, 'price')

    def test_require_positive_passes(self):
        self.assertAlmostEqual(require_positive(0.01, 'price'), 0.01)


class TestEmailValidator(BaseCase):

    def test_valid_email(self):
        self.assertEqual(validate_email('User@Example.COM'), 'user@example.com')

    def test_invalid_email_no_at(self):
        with self.assertRaises(CargoInvalidFieldError):
            validate_email('notanemail')

    def test_invalid_email_no_domain(self):
        with self.assertRaises(CargoInvalidFieldError):
            validate_email('user@')

    def test_missing_email(self):
        with self.assertRaises(CargoMissingFieldError):
            validate_email('')


class TestPhoneValidator(BaseCase):

    def test_valid_local_format(self):
        result = validate_phone('01012345678')
        self.assertTrue(result.startswith('+2'))

    def test_valid_international_format(self):
        result = validate_phone('+201012345678')
        self.assertEqual(result, '+201012345678')

    def test_invalid_operator(self):
        """08x numbers are not valid Egyptian mobile numbers."""
        with self.assertRaises(CargoInvalidFieldError):
            validate_phone('08012345678')

    def test_too_short(self):
        with self.assertRaises(CargoInvalidFieldError):
            validate_phone('0101234')


class TestPasswordValidator(BaseCase):

    def test_valid_password(self):
        result = validate_password('Secure123')
        self.assertEqual(result, 'Secure123')

    def test_too_short(self):
        with self.assertRaises(CargoInvalidFieldError):
            validate_password('abc1')

    def test_no_letter(self):
        with self.assertRaises(CargoInvalidFieldError):
            validate_password('12345678')

    def test_no_digit(self):
        with self.assertRaises(CargoInvalidFieldError):
            validate_password('abcdefgh')


class TestRatingValidator(BaseCase):

    def test_valid_rating(self):
        self.assertAlmostEqual(validate_rating(4.5), 4.5)

    def test_below_minimum(self):
        with self.assertRaises(CargoInvalidFieldError):
            validate_rating(0.9)

    def test_above_maximum(self):
        with self.assertRaises(CargoInvalidFieldError):
            validate_rating(5.1)


class TestOTPValidator(BaseCase):

    def test_valid_4_digits(self):
        self.assertEqual(validate_otp('1234'), '1234')

    def test_valid_6_digits(self):
        self.assertEqual(validate_otp('123456'), '123456')

    def test_invalid_alpha(self):
        with self.assertRaises(CargoInvalidFieldError):
            validate_otp('12AB')

    def test_invalid_length_3(self):
        with self.assertRaises(CargoInvalidFieldError):
            validate_otp('123')


class TestPagination(BaseCase):

    def test_defaults(self):
        page, limit = validate_pagination()
        self.assertGreaterEqual(page, 1)
        self.assertGreater(limit, 0)

    def test_clamps_limit_to_max(self):
        _, limit = validate_pagination(limit=9999)
        self.assertLessEqual(limit, 100)

    def test_offset_first_page(self):
        self.assertEqual(pagination_offset(1, 20), 0)

    def test_offset_second_page(self):
        self.assertEqual(pagination_offset(2, 20), 20)

    def test_offset_third_page(self):
        self.assertEqual(pagination_offset(3, 10), 20)


class TestSelectionValidator(BaseCase):

    CHOICES = [('a', 'Alpha'), ('b', 'Beta'), ('c', 'Gamma')]

    def test_valid_choice(self):
        self.assertEqual(validate_selection('a', self.CHOICES, 'field'), 'a')

    def test_invalid_choice(self):
        with self.assertRaises(CargoInvalidFieldError):
            validate_selection('x', self.CHOICES, 'field')

    def test_missing_choice(self):
        with self.assertRaises(CargoMissingFieldError):
            validate_selection('', self.CHOICES, 'field')
