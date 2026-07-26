# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
Cargo structured logging utilities.

Provides a consistent log format across all Cargo modules and helpers
for logging API requests and responses in a structured way.
"""

import logging
import time


# ── Logger factory ────────────────────────────────────────────────────────────

def get_logger(module_name: str) -> logging.Logger:
    """
    Return a logger namespaced under 'cargo.<module_name>'.

    Usage::

        from cargo_base.utils.logging_utils import get_logger
        _logger = get_logger(__name__)
    """
    return logging.getLogger(f'cargo.{module_name}')


# ── Request timer context manager ─────────────────────────────────────────────

class RequestTimer:
    """
    Context manager that measures elapsed time for an API request.

    Usage::

        timer = RequestTimer()
        with timer:
            result = do_work()
        duration_ms = timer.elapsed_ms
    """

    def __init__(self):
        self._start:      float = 0.0
        self.elapsed_ms:  float = 0.0

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed_ms = (time.perf_counter() - self._start) * 1000.0


# ── Structured log helpers ────────────────────────────────────────────────────

_api_logger = get_logger('api')


def log_request(method: str, endpoint: str, uid: int = None, ip: str = '') -> None:
    """Log an incoming API request."""
    _api_logger.info(
        '[REQUEST] %s %s | uid=%s | ip=%s',
        method, endpoint, uid or 'anon', ip,
    )


def log_response(
    method: str,
    endpoint: str,
    status: int,
    duration_ms: float,
    uid: int = None,
) -> None:
    """Log a completed API response."""
    level = logging.WARNING if status >= 400 else logging.INFO
    _api_logger.log(
        level,
        '[RESPONSE] %s %s → %d (%.1f ms) | uid=%s',
        method, endpoint, status, duration_ms, uid or 'anon',
    )


def log_error(module: str, exc: Exception, context: str = '') -> None:
    """Log an unexpected exception with context."""
    logger = get_logger(module)
    logger.exception('[ERROR] %s | %s: %s', context, type(exc).__name__, exc)
