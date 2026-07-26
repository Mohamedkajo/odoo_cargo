# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
CargoAuthController — Authentication endpoints for the Cargo Flutter apps.

Routes (all match Flutter's existing base-URL + path convention):
  POST /api/auth/register      — customer self-registration
  POST /api/auth/login         — login → JWT access + refresh tokens
  POST /api/auth/refresh       — rotate tokens
  POST /api/auth/logout        — revoke refresh token
  GET  /api/users/profile      — current-user profile
  PATCH /api/users/profile     — update profile fields
  PATCH /api/users/password    — change password
  POST  /api/users/avatar      — upload avatar image

Response contracts match the existing Node.js API exactly so the Flutter
Customer App requires zero code changes.
"""

import json
import logging
from datetime import timedelta

from odoo import fields, http
from odoo.exceptions import AccessDenied
from odoo.http import request

from cargo_base.constants import (
    HTTP_200,
    HTTP_201,
    HTTP_400,
    HTTP_401,
    HTTP_404,
    HTTP_409,
    ERR_VALIDATION,
    ERR_AUTH,
    ERR_NOT_FOUND,
    ERR_CONFLICT,
    CONFIG_JWT_SECRET,
    JWT_REFRESH_EXPIRY_SECS,
)
from cargo_base.utils.jwt_utils import (
    generate_access_token,
    generate_refresh_token,
    verify_token,
    hash_token,
)
from cargo_base.utils.validators import (
    validate_email,
    validate_password,
    normalize_egyptian_phone,
)
from cargo_base.utils.image_utils import decode_base64
from cargo_api.controllers.base import CargoBaseController
from cargo_api.utils.decorators import require_cargo_auth
from cargo_api.utils.upload import read_image_upload

_logger = logging.getLogger(__name__)

# Maximum avatar image size (bytes) — 5 MB
_MAX_AVATAR_SIZE = 5 * 1024 * 1024


def _json_body():
    """Parse and return the JSON request body, or an empty dict on error."""
    try:
        raw = request.httprequest.get_data(as_text=True)
        return json.loads(raw) if raw else {}
    except Exception:
        return {}


def _get_jwt_secret():
    """Retrieve the configured JWT HMAC secret from ir.config_parameter."""
    return request.env['ir.config_parameter'].sudo().get_param(CONFIG_JWT_SECRET, '')


def _auth_response(user):
    """
    Build the standard auth response:
      { "token": str, "refreshToken": str, "user": UserDict }

    The access token is a short-lived (24h) stateless JWT.
    A new refresh token is created and stored (hashed) in cargo.api.token.

    Bug fix: generate_access_token / generate_refresh_token require `secret`
    as the 3rd positional argument (not an `env=` keyword). The secret is
    read from ir.config_parameter using CONFIG_JWT_SECRET.

    Bug fix: cargo.api.token.expires_at is required=True (no default).
    Compute it from JWT_REFRESH_EXPIRY_SECS to avoid ValidationError.
    """
    secret = _get_jwt_secret()

    # Generate tokens — pass secret as required positional argument
    access_token  = generate_access_token(
        user.id,
        user.cargo_role or 'customer',
        secret,
    )
    refresh_token = generate_refresh_token(user.id, secret)

    # Compute expiry datetime for the refresh token record
    expires_at = fields.Datetime.now() + timedelta(seconds=JWT_REFRESH_EXPIRY_SECS)

    # Persist hashed refresh token (expires_at is required=True on the model)
    request.env['cargo.api.token'].sudo().create({
        'user_id':    user.id,
        'token_hash': hash_token(refresh_token),
        'expires_at': expires_at,
        'ip_address': request.httprequest.remote_addr,
        'user_agent': (request.httprequest.user_agent.string or '')[:255],
    })

    return {
        'token':        access_token,
        'refreshToken': refresh_token,
        'user':         user.sudo().cargo_to_auth_dict(),
    }


class CargoAuthController(CargoBaseController):
    """Authentication and profile management endpoints."""

    # ── Registration ──────────────────────────────────────────────────────────

    @http.route(
        '/api/auth/register',
        auth='none',
        methods=['POST'],
        type='http',
        csrf=False,
        save_session=False,
    )
    def cargo_register(self, **kwargs):
        """
        POST /api/auth/register

        Body: { name, email, password, phone? }
        Returns: { token, refreshToken, user }
        """
        body = _json_body()

        # Validate required fields
        name     = (body.get('name') or '').strip()
        email    = (body.get('email') or '').strip().lower()
        password = body.get('password') or ''
        phone_raw = body.get('phone') or ''

        errors = {}
        if not name:
            errors['name'] = 'Name is required.'
        if not email or not validate_email(email):
            errors['email'] = 'A valid email address is required.'
        if not password or not validate_password(password):
            errors['password'] = 'Password must be at least 8 characters.'

        phone = None
        if phone_raw:
            phone = normalize_egyptian_phone(phone_raw)
            if not phone:
                errors['phone'] = 'Invalid Egyptian phone number.'

        if errors:
            return request.make_response(
                json.dumps({'error': ERR_VALIDATION, 'message': 'Validation failed.', 'fields': errors}),
                status=HTTP_400,
                headers=[('Content-Type', 'application/json')],
            )

        # Check for duplicate email
        existing = request.env['res.users'].sudo().search(
            [('login', '=', email)], limit=1
        )
        if existing:
            return request.make_response(
                json.dumps({'error': ERR_CONFLICT, 'message': 'Email already registered.'}),
                status=HTTP_409,
                headers=[('Content-Type', 'application/json')],
            )

        # Create the user (cargo customer)
        try:
            user = request.env['res.users'].sudo().create({
                'name':      name,
                'login':     email,
                'email':     email,
                'password':  password,   # Odoo auto-hashes with bcrypt
                'groups_id': [(4, request.env.ref('cargo_base.cargo_group_customer').id)],
            })
            # cargo_role is on res.partner via related field; write separately
            user.partner_id.sudo().write({
                'cargo_role': 'customer',
                **(({'phone': phone}) if phone else {}),
            })
        except Exception as exc:
            _logger.error('cargo_register create error: %s', exc)
            return request.make_response(
                json.dumps({'error': 'ERR_SERVER', 'message': 'Registration failed. Please try again.'}),
                status=500,
                headers=[('Content-Type', 'application/json')],
            )

        payload = _auth_response(user)
        return request.make_response(
            json.dumps(payload),
            status=HTTP_201,
            headers=[('Content-Type', 'application/json')],
        )

    # ── Login ─────────────────────────────────────────────────────────────────

    @http.route(
        '/api/auth/login',
        auth='none',
        methods=['POST'],
        type='http',
        csrf=False,
        save_session=False,
    )
    def cargo_login(self, **kwargs):
        """
        POST /api/auth/login

        Body: { email, password }
        Returns: { token, refreshToken, user }
        """
        body  = _json_body()
        email    = (body.get('email') or '').strip().lower()
        password = body.get('password') or ''

        if not email or not password:
            return request.make_response(
                json.dumps({'error': ERR_VALIDATION, 'message': 'Email and password are required.'}),
                status=HTTP_400,
                headers=[('Content-Type', 'application/json')],
            )

        # Find user by email (login field)
        user = request.env['res.users'].sudo().search(
            [('login', '=', email), ('active', '=', True)], limit=1
        )
        if not user:
            return request.make_response(
                json.dumps({'error': ERR_AUTH, 'message': 'Invalid credentials.'}),
                status=HTTP_401,
                headers=[('Content-Type', 'application/json')],
            )

        # Verify password using Odoo's built-in mechanism
        try:
            user._check_credentials(password, {'interactive': False})
        except (AccessDenied, Exception):
            return request.make_response(
                json.dumps({'error': ERR_AUTH, 'message': 'Invalid credentials.'}),
                status=HTTP_401,
                headers=[('Content-Type', 'application/json')],
            )

        # Ensure the user has the cargo_group_customer group
        customer_group = request.env.ref('cargo_base.cargo_group_customer', raise_if_not_found=False)
        if customer_group and customer_group not in user.groups_id:
            user.sudo().write({'groups_id': [(4, customer_group.id)]})
            if not user.cargo_role:
                user.partner_id.sudo().write({'cargo_role': 'customer'})

        payload = _auth_response(user)
        return request.make_response(
            json.dumps(payload),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )

    # ── Token Refresh ─────────────────────────────────────────────────────────

    @http.route(
        '/api/auth/refresh',
        auth='none',
        methods=['POST'],
        type='http',
        csrf=False,
        save_session=False,
    )
    def cargo_refresh(self, **kwargs):
        """
        POST /api/auth/refresh

        Body: { refreshToken }
        Returns: { token, refreshToken, user }
        """
        body          = _json_body()
        refresh_token = body.get('refreshToken') or body.get('refresh_token') or ''

        if not refresh_token:
            return request.make_response(
                json.dumps({'error': ERR_VALIDATION, 'message': 'refreshToken is required.'}),
                status=HTTP_400,
                headers=[('Content-Type', 'application/json')],
            )

        token_hash = hash_token(refresh_token)
        token_record = request.env['cargo.api.token'].sudo().search(
            [('token_hash', '=', token_hash), ('is_revoked', '=', False)],
            limit=1,
        )

        if not token_record or token_record.is_expired:
            return request.make_response(
                json.dumps({'error': ERR_AUTH, 'message': 'Invalid or expired refresh token.'}),
                status=HTTP_401,
                headers=[('Content-Type', 'application/json')],
            )

        user = token_record.user_id

        # Revoke the old token (rotation)
        token_record.sudo().action_revoke()

        payload = _auth_response(user)
        return request.make_response(
            json.dumps(payload),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )

    # ── Logout ────────────────────────────────────────────────────────────────

    @http.route(
        '/api/auth/logout',
        auth='none',
        methods=['POST'],
        type='http',
        csrf=False,
        save_session=False,
    )
    @require_cargo_auth()
    def cargo_logout(self, **kwargs):
        """
        POST /api/auth/logout

        Header: Authorization: Bearer <accessToken>
        Body (optional): { refreshToken }
        Returns: 200 { message: "Logged out." }
        """
        body          = _json_body()
        refresh_token = body.get('refreshToken') or body.get('refresh_token') or ''

        if refresh_token:
            token_hash = hash_token(refresh_token)
            token_record = request.env['cargo.api.token'].sudo().search(
                [('token_hash', '=', token_hash)], limit=1,
            )
            if token_record:
                token_record.sudo().action_revoke()

        return request.make_response(
            json.dumps({'message': 'Logged out.'}),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )

    # ── Profile (GET) ─────────────────────────────────────────────────────────

    @http.route(
        '/api/users/profile',
        auth='none',
        methods=['GET'],
        type='http',
        csrf=False,
        save_session=False,
    )
    @require_cargo_auth()
    def cargo_get_profile(self, **kwargs):
        """
        GET /api/users/profile

        Header: Authorization: Bearer <accessToken>
        Returns: UserDict
        """
        user = request.cargo_user
        return request.make_response(
            json.dumps(user.sudo().cargo_to_auth_dict()),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )

    # ── Profile (PATCH) ───────────────────────────────────────────────────────

    @http.route(
        '/api/users/profile',
        auth='none',
        methods=['PATCH'],
        type='http',
        csrf=False,
        save_session=False,
    )
    @require_cargo_auth()
    def cargo_update_profile(self, **kwargs):
        """
        PATCH /api/users/profile

        Header: Authorization: Bearer <accessToken>
        Body: { name?, phone? }
        Returns: UserDict
        """
        user = request.cargo_user
        body = _json_body()

        user_vals    = {}
        partner_vals = {}

        if 'name' in body and body['name']:
            user_vals['name'] = str(body['name']).strip()

        if 'phone' in body:
            phone = normalize_egyptian_phone(body['phone'] or '')
            if body['phone'] and not phone:
                return request.make_response(
                    json.dumps({'error': ERR_VALIDATION, 'message': 'Invalid phone number.'}),
                    status=HTTP_400,
                    headers=[('Content-Type', 'application/json')],
                )
            partner_vals['phone'] = phone or False

        if user_vals:
            user.sudo().write(user_vals)
        if partner_vals:
            user.partner_id.sudo().write(partner_vals)

        return request.make_response(
            json.dumps(user.sudo().cargo_to_auth_dict()),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )

    # ── Password Change ───────────────────────────────────────────────────────

    @http.route(
        '/api/users/password',
        auth='none',
        methods=['PATCH'],
        type='http',
        csrf=False,
        save_session=False,
    )
    @require_cargo_auth()
    def cargo_change_password(self, **kwargs):
        """
        PATCH /api/users/password

        Header: Authorization: Bearer <accessToken>
        Body: { currentPassword, newPassword }
        Returns: 200 { message }
        """
        user = request.cargo_user
        body = _json_body()

        current = body.get('currentPassword') or ''
        new_pwd  = body.get('newPassword') or ''

        if not current or not new_pwd:
            return request.make_response(
                json.dumps({'error': ERR_VALIDATION, 'message': 'currentPassword and newPassword are required.'}),
                status=HTTP_400,
                headers=[('Content-Type', 'application/json')],
            )

        if not validate_password(new_pwd):
            return request.make_response(
                json.dumps({'error': ERR_VALIDATION, 'message': 'New password must be at least 8 characters.'}),
                status=HTTP_400,
                headers=[('Content-Type', 'application/json')],
            )

        try:
            user._check_credentials(current, {'interactive': False})
        except (AccessDenied, Exception):
            return request.make_response(
                json.dumps({'error': ERR_AUTH, 'message': 'Current password is incorrect.'}),
                status=HTTP_401,
                headers=[('Content-Type', 'application/json')],
            )

        user.sudo().write({'password': new_pwd})

        return request.make_response(
            json.dumps({'message': 'Password updated successfully.'}),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )

    # ── Avatar Upload ─────────────────────────────────────────────────────────

    @http.route(
        '/api/users/avatar',
        auth='none',
        methods=['POST'],
        type='http',
        csrf=False,
        save_session=False,
    )
    @require_cargo_auth()
    def cargo_upload_avatar(self, **kwargs):
        """
        POST /api/users/avatar  (multipart/form-data, field: avatar)

        Header: Authorization: Bearer <accessToken>
        Returns: { avatar: url }
        """
        user = request.cargo_user
        try:
            b64, _mime = read_image_upload(field='avatar', max_size=_MAX_AVATAR_SIZE)
        except Exception as exc:
            return request.make_response(
                json.dumps({'error': ERR_VALIDATION, 'message': str(exc)}),
                status=HTTP_400,
                headers=[('Content-Type', 'application/json')],
            )

        raw = decode_base64(b64)
        user.partner_id.sudo().write({'image_1920': b64})

        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url', '')
        avatar_url = f'{base_url}/web/image/res.partner/{user.partner_id.id}/image_128'

        return request.make_response(
            json.dumps({'avatar': avatar_url, 'user': user.sudo().cargo_to_auth_dict()}),
            status=HTTP_200,
            headers=[('Content-Type', 'application/json')],
        )
