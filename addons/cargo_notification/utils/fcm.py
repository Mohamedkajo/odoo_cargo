# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
FCM push-notification dispatcher — stdlib only (no extra pip packages).

Uses Firebase Cloud Messaging Legacy HTTP API:
  POST https://fcm.googleapis.com/fcm/send
  Authorization: key=<SERVER_KEY>

The server key is stored in ir.config_parameter under ``cargo.fcm.server_key``.
If the key is absent or blank, the call is skipped (no error raised).

All functions are **fail-safe**: exceptions are caught and logged so that a
broken FCM key or a transient Google outage never crashes an order flow.
"""

import json
import logging
import urllib.error
import urllib.request

_logger = logging.getLogger(__name__)

_FCM_ENDPOINT = 'https://fcm.googleapis.com/fcm/send'
_TIMEOUT_SECS = 5


def _get_server_key(env) -> str:
    """Return the FCM server key from ir.config_parameter (or '' if unset)."""
    return (
        env['ir.config_parameter'].sudo()
        .get_param('cargo.fcm.server_key', default='')
        or ''
    )


def send_push(env, *, device_token: str, title: str, body: str,
              data: dict = None) -> bool:
    """
    Send a single-device push notification via FCM Legacy HTTP.

    Args:
        env:          Odoo Environment (for ir.config_parameter lookup)
        device_token: FCM registration token for the target device
        title:        Notification title
        body:         Notification body text
        data:         Optional dict forwarded as FCM data payload (to app)

    Returns:
        True if FCM accepted the message; False otherwise (already logged).
    """
    if not device_token:
        return False

    server_key = _get_server_key(env)
    if not server_key:
        _logger.debug(
            'cargo.fcm: server key not configured (cargo.fcm.server_key); '
            'skipping push for token %s…', device_token[:8]
        )
        return False

    payload = {
        'to': device_token,
        'notification': {
            'title': title,
            'body':  body,
            'sound': 'default',
        },
        'data': data or {},
        'priority': 'high',
    }

    return _post_to_fcm(server_key, payload, label=device_token[:8])


def send_multicast(env, *, device_tokens: list, title: str, body: str,
                   data: dict = None) -> bool:
    """
    Send a push notification to multiple devices via FCM multicast.

    Silently skips if token list is empty or server key is not configured.
    """
    tokens = [t for t in (device_tokens or []) if t]
    if not tokens:
        return False

    server_key = _get_server_key(env)
    if not server_key:
        return False

    payload = {
        'registration_ids': tokens,
        'notification': {
            'title': title,
            'body':  body,
            'sound': 'default',
        },
        'data': data or {},
        'priority': 'high',
    }

    return _post_to_fcm(server_key, payload, label=f'{len(tokens)} devices')


def _post_to_fcm(server_key: str, payload: dict, label: str) -> bool:
    """
    Internal: POST ``payload`` to the FCM endpoint.  Fail-safe — all
    exceptions are caught and logged; never re-raised.

    Returns True if FCM returned HTTP 200.
    """
    try:
        body_bytes = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            _FCM_ENDPOINT,
            data=body_bytes,
            headers={
                'Content-Type':  'application/json',
                'Authorization': f'key={server_key}',
            },
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT_SECS) as resp:
            status  = resp.status
            raw     = resp.read().decode('utf-8', errors='replace')

        try:
            result = json.loads(raw)
        except Exception:
            result = {}

        if status == 200 and result.get('success', 0) >= 1:
            _logger.debug('cargo.fcm: push accepted → %s', label)
            return True

        _logger.warning(
            'cargo.fcm: FCM returned status=%s, failure=%s for %s. '
            'response=%s',
            status, result.get('failure'), label, raw[:200],
        )
        return False

    except urllib.error.HTTPError as exc:
        _logger.warning(
            'cargo.fcm: HTTP %s from FCM for %s: %s',
            exc.code, label, exc.read()[:200],
        )
    except urllib.error.URLError as exc:
        _logger.warning('cargo.fcm: network error for %s: %s', label, exc.reason)
    except Exception as exc:  # noqa: BLE001
        _logger.exception('cargo.fcm: unexpected error for %s: %s', label, exc)

    return False
