# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
Cargo image utilities.

Helpers for building image URLs, encoding images for API responses
and validating uploaded image data.
"""

import base64
import os

from ..constants import MAX_IMAGE_SIZE_MB, ALLOWED_IMAGE_EXTS
from ..exceptions import CargoInvalidFieldError


def build_image_url(base_url: str, model: str, record_id: int,
                    field: str = 'image_512') -> str:
    """
    Build the public Odoo image URL for a model record field.

    Args:
        base_url:  web.base.url config parameter value
        model:     Odoo model name (e.g. 'product.template')
        record_id: ID of the record
        field:     Image field name (default 'image_512')

    Returns:
        Full URL string, or empty string if record_id is falsy.
    """
    if not record_id:
        return ''
    model_path = model.replace('.', '-')   # Odoo URL convention
    return f'{base_url}/web/image/{model}/{record_id}/{field}'


def encode_base64(image_bytes: bytes) -> str:
    """Encode raw image bytes as a base64 string for Odoo Binary fields."""
    return base64.b64encode(image_bytes).decode('ascii')


def decode_base64(b64_string: str) -> bytes:
    """
    Decode a base64 string (with or without data URI prefix) to bytes.

    Handles both:
    - ``data:image/jpeg;base64,/9j/4AAQ...``
    - ``/9j/4AAQ...``
    """
    if ',' in b64_string:
        b64_string = b64_string.split(',', 1)[1]
    return base64.b64decode(b64_string)


def validate_extension(filename: str, field: str = 'image') -> str:
    """Validate the file extension is in the allowed set."""
    ext = os.path.splitext(filename.lower())[1]
    if ext not in ALLOWED_IMAGE_EXTS:
        allowed = ', '.join(sorted(ALLOWED_IMAGE_EXTS))
        raise CargoInvalidFieldError(
            field,
            f'File type "{ext}" is not allowed. Allowed: {allowed}'
        )
    return ext


def validate_size(data: bytes, field: str = 'image') -> None:
    """Raise CargoInvalidFieldError if image data exceeds MAX_IMAGE_SIZE_MB."""
    max_bytes = MAX_IMAGE_SIZE_MB * 1024 * 1024
    if len(data) > max_bytes:
        actual_mb = len(data) / (1024 * 1024)
        raise CargoInvalidFieldError(
            field,
            f'Image size {actual_mb:.1f} MB exceeds the maximum of {MAX_IMAGE_SIZE_MB} MB'
        )
