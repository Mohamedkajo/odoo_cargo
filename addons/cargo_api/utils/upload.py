# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
File and image upload utilities for Cargo REST API controllers.

Handles multipart/form-data uploads, validates MIME type and file size,
and converts uploaded files to Odoo-compatible base64 strings.

Usage in a controller::

    from cargo_api.utils.upload import read_image_upload

    @http.route('/api/v1/vendor/products/<int:product_id>/image',
                auth='none', methods=['POST'], type='http', csrf=False)
    @require_cargo_auth('vendor', 'admin')
    def upload_product_image(self, product_id, **kwargs):
        try:
            b64_data, mime_type = read_image_upload('image')
        except CargoValidationError as exc:
            return from_exception(exc)
        product.write({'image_1920': b64_data})
        ...
"""

import base64
import logging

from odoo.http import request

from odoo.addons.cargo_base.exceptions import CargoValidationError

_logger = logging.getLogger(__name__)

# Allowed image MIME types
_ALLOWED_IMAGE_MIMES = {
    'image/jpeg',
    'image/png',
    'image/webp',
    'image/gif',
}

# Allowed document MIME types (for future use)
_ALLOWED_DOC_MIMES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
}

# Default maximum sizes
_MAX_IMAGE_SIZE_MB = 5
_MAX_DOC_SIZE_MB   = 20


def _get_max_image_size_bytes():
    """Read the configured max image size from Cargo config parameters."""
    try:
        mb = float(
            request.env['ir.config_parameter'].sudo().get_param(
                'cargo.media.max_image_size_mb', str(_MAX_IMAGE_SIZE_MB)
            )
        )
        return int(mb * 1024 * 1024)
    except Exception:
        return _MAX_IMAGE_SIZE_MB * 1024 * 1024


def read_image_upload(field_name='image'):
    """
    Read and validate an image file from a multipart/form-data request.

    Args:
        field_name: The form field name to read the file from.

    Returns:
        Tuple of (base64_string, mime_type) ready for Odoo's Binary field.

    Raises:
        CargoValidationError: if the field is missing, the MIME type is not
            an allowed image type, or the file exceeds the configured size limit.
    """
    file_storage = request.httprequest.files.get(field_name)
    if not file_storage:
        raise CargoValidationError(
            f"No file uploaded. Expected a file in the '{field_name}' form field.",
            field=field_name,
        )

    mime_type = (file_storage.mimetype or '').lower()
    if mime_type not in _ALLOWED_IMAGE_MIMES:
        raise CargoValidationError(
            f'Unsupported image type: {mime_type!r}. '
            f'Allowed types: {", ".join(sorted(_ALLOWED_IMAGE_MIMES))}.',
            field=field_name,
        )

    raw_bytes = file_storage.read()
    max_bytes = _get_max_image_size_bytes()
    if len(raw_bytes) > max_bytes:
        max_mb = max_bytes / (1024 * 1024)
        actual_mb = len(raw_bytes) / (1024 * 1024)
        raise CargoValidationError(
            f'Image is too large ({actual_mb:.1f} MB). '
            f'Maximum allowed size is {max_mb:.1f} MB.',
            field=field_name,
        )

    if len(raw_bytes) == 0:
        raise CargoValidationError('Uploaded file is empty.', field=field_name)

    b64_data = base64.b64encode(raw_bytes).decode('ascii')
    return b64_data, mime_type


def read_file_upload(field_name='file', allowed_mimes=None, max_mb=None):
    """
    Read and validate any file from a multipart/form-data request.

    Args:
        field_name    : The form field name.
        allowed_mimes : Set of allowed MIME type strings.  None = any type.
        max_mb        : Maximum file size in megabytes.  None = 20 MB.

    Returns:
        Tuple of (raw_bytes, original_filename, mime_type).

    Raises:
        CargoValidationError on validation failure.
    """
    file_storage = request.httprequest.files.get(field_name)
    if not file_storage:
        raise CargoValidationError(
            f"No file uploaded. Expected a file in the '{field_name}' form field.",
            field=field_name,
        )

    mime_type = (file_storage.mimetype or '').lower()
    if allowed_mimes and mime_type not in allowed_mimes:
        raise CargoValidationError(
            f'Unsupported file type: {mime_type!r}. '
            f'Allowed: {", ".join(sorted(allowed_mimes))}.',
            field=field_name,
        )

    raw_bytes = file_storage.read()
    max_bytes = int((max_mb or _MAX_DOC_SIZE_MB) * 1024 * 1024)
    if len(raw_bytes) > max_bytes:
        raise CargoValidationError(
            f'File too large ({len(raw_bytes) / 1024 / 1024:.1f} MB). '
            f'Maximum is {max_bytes / 1024 / 1024:.0f} MB.',
            field=field_name,
        )

    if len(raw_bytes) == 0:
        raise CargoValidationError('Uploaded file is empty.', field=field_name)

    return raw_bytes, file_storage.filename or '', mime_type


def get_image_url(record, field='image_128', base_url=None):
    """
    Build a public image URL for an Odoo model record.

    Args:
        record   : Odoo record with an image field.
        field    : Image field name (default 'image_128').
        base_url : Override base URL (uses web.base.url param by default).

    Returns:
        Absolute URL string, or empty string if the record has no image.
    """
    if not record or not record._fields.get(field):
        return ''
    if not record[field]:
        return ''

    if base_url is None:
        base_url = (
            request.env['ir.config_parameter']
            .sudo()
            .get_param('web.base.url', '')
            .rstrip('/')
        )

    return f'{base_url}/web/image/{record._name}/{record.id}/{field}'
