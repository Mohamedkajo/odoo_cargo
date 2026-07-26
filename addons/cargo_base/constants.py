# -*- coding: utf-8 -*-
# Part of Cargo Marketplace. See LICENSE file for full copyright and licensing details.
"""
Cargo Marketplace — Platform-wide constants.

All shared constants are defined here to avoid magic strings scattered
across modules. Import from this module; never redefine locally.
"""

# ── Cargo User Roles ──────────────────────────────────────────────────────────
CARGO_ROLE_CUSTOMER = 'customer'
CARGO_ROLE_VENDOR   = 'vendor'
CARGO_ROLE_DRIVER   = 'driver'

CARGO_ROLES = [
    (CARGO_ROLE_CUSTOMER, 'Customer'),
    (CARGO_ROLE_VENDOR,   'Vendor'),
    (CARGO_ROLE_DRIVER,   'Driver'),
]

# ── Order Status Flow ─────────────────────────────────────────────────────────
ORDER_STATUS_CONFIRMED  = 'confirmed'
ORDER_STATUS_PREPARING  = 'preparing'
ORDER_STATUS_READY      = 'ready'
ORDER_STATUS_COLLECTING = 'collecting'
ORDER_STATUS_DELIVERING = 'delivering'
ORDER_STATUS_OTP_CHECK  = 'otp_check'
ORDER_STATUS_DELIVERED  = 'delivered'
ORDER_STATUS_CANCELLED  = 'cancelled'

ORDER_STATUSES = [
    (ORDER_STATUS_CONFIRMED,  'Confirmed'),
    (ORDER_STATUS_PREPARING,  'Preparing'),
    (ORDER_STATUS_READY,      'Ready for Pickup'),
    (ORDER_STATUS_COLLECTING, 'Driver Collecting'),
    (ORDER_STATUS_DELIVERING, 'Delivering'),
    (ORDER_STATUS_OTP_CHECK,  'OTP Verification'),
    (ORDER_STATUS_DELIVERED,  'Delivered'),
    (ORDER_STATUS_CANCELLED,  'Cancelled'),
]

# Terminal states — cannot transition out
ORDER_TERMINAL_STATES = {ORDER_STATUS_DELIVERED, ORDER_STATUS_CANCELLED}

# Valid transitions: {from_status: {allowed_to_statuses}}
ORDER_TRANSITIONS = {
    ORDER_STATUS_CONFIRMED:  {ORDER_STATUS_PREPARING, ORDER_STATUS_CANCELLED},
    ORDER_STATUS_PREPARING:  {ORDER_STATUS_READY,     ORDER_STATUS_CANCELLED},
    ORDER_STATUS_READY:      {ORDER_STATUS_COLLECTING, ORDER_STATUS_CANCELLED},
    ORDER_STATUS_COLLECTING: {ORDER_STATUS_DELIVERING},
    ORDER_STATUS_DELIVERING: {ORDER_STATUS_OTP_CHECK},
    ORDER_STATUS_OTP_CHECK:  {ORDER_STATUS_DELIVERED},
    ORDER_STATUS_DELIVERED:  set(),
    ORDER_STATUS_CANCELLED:  set(),
}

# ── JWT ───────────────────────────────────────────────────────────────────────
JWT_ALGORITHM            = 'HS256'
JWT_ACCESS_EXPIRY_SECS   = 86_400       # 24 hours
JWT_REFRESH_EXPIRY_SECS  = 2_592_000    # 30 days
JWT_ISSUER               = 'cargo-marketplace'
JWT_AUDIENCE             = 'cargo-mobile'

# ── API ───────────────────────────────────────────────────────────────────────
API_VERSION       = 'v1'
API_BASE_PATH     = f'/api/{API_VERSION}'
API_DEFAULT_LIMIT = 20
API_MAX_LIMIT     = 100

# ── HTTP Status Codes ─────────────────────────────────────────────────────────
HTTP_200 = 200
HTTP_201 = 201
HTTP_204 = 204
HTTP_400 = 400
HTTP_401 = 401
HTTP_403 = 403
HTTP_404 = 404
HTTP_409 = 409
HTTP_422 = 422
HTTP_429 = 429
HTTP_500 = 500

# ── Cargo Error Codes (returned in JSON) ──────────────────────────────────────
ERR_VALIDATION  = 'VALIDATION_ERROR'
ERR_AUTH        = 'INVALID_CREDENTIALS'
ERR_TOKEN       = 'INVALID_TOKEN'
ERR_EXPIRED     = 'TOKEN_EXPIRED'
ERR_REVOKED     = 'TOKEN_REVOKED'
ERR_PERMISSION  = 'PERMISSION_DENIED'
ERR_NOT_FOUND   = 'NOT_FOUND'
ERR_CONFLICT    = 'CONFLICT'
ERR_RATE_LIMIT  = 'RATE_LIMIT_EXCEEDED'
ERR_SERVER      = 'INTERNAL_SERVER_ERROR'
ERR_TRANSITION  = 'INVALID_STATUS_TRANSITION'
ERR_OTP         = 'INVALID_OTP'
ERR_OTP_EXPIRED = 'OTP_EXPIRED'

# ── Wallet Transaction Types ──────────────────────────────────────────────────
WALLET_TOPUP      = 'topup'
WALLET_PURCHASE   = 'purchase'
WALLET_REFUND     = 'refund'
WALLET_PAYOUT     = 'payout'
WALLET_COMMISSION = 'commission'
WALLET_REWARD     = 'reward'
WALLET_EARNING    = 'earning'

WALLET_TRANSACTION_TYPES = [
    (WALLET_TOPUP,      'Top Up'),
    (WALLET_PURCHASE,   'Purchase'),
    (WALLET_REFUND,     'Refund'),
    (WALLET_PAYOUT,     'Payout'),
    (WALLET_COMMISSION, 'Commission'),
    (WALLET_REWARD,     'Loyalty Reward'),
    (WALLET_EARNING,    'Driver Earning'),
]

# ── Notification Types ────────────────────────────────────────────────────────
NOTIF_ORDER  = 'order'
NOTIF_PROMO  = 'promo'
NOTIF_DRIVER = 'driver'
NOTIF_SYSTEM = 'system'
NOTIF_WALLET = 'wallet'

NOTIFICATION_TYPES = [
    (NOTIF_ORDER,  'Order Update'),
    (NOTIF_PROMO,  'Promotion'),
    (NOTIF_DRIVER, 'Driver Update'),
    (NOTIF_SYSTEM, 'System'),
    (NOTIF_WALLET, 'Wallet'),
]

# ── Vehicle Types ─────────────────────────────────────────────────────────────
VEHICLE_SCOOTER  = 'scooter'
VEHICLE_TRICYCLE = 'tricycle'
VEHICLE_VAN      = 'van'
VEHICLE_PACKAGE  = 'package'

VEHICLE_TYPES = [
    (VEHICLE_SCOOTER,  'Scooter'),
    (VEHICLE_TRICYCLE, 'Tricycle'),
    (VEHICLE_VAN,      'Van'),
    (VEHICLE_PACKAGE,  'Package'),
]

# ── Review Types ──────────────────────────────────────────────────────────────
REVIEW_STORE   = 'store'
REVIEW_PRODUCT = 'product'

REVIEW_TYPES = [
    (REVIEW_STORE,   'Store Review'),
    (REVIEW_PRODUCT, 'Product Review'),
]

# ── Favorite Types ────────────────────────────────────────────────────────────
FAVORITE_STORE   = 'store'
FAVORITE_PRODUCT = 'product'

FAVORITE_TYPES = [
    (FAVORITE_STORE,   'Store'),
    (FAVORITE_PRODUCT, 'Product'),
]

# ── Audit Actions ─────────────────────────────────────────────────────────────
AUDIT_CREATE   = 'create'
AUDIT_READ     = 'read'
AUDIT_UPDATE   = 'update'
AUDIT_DELETE   = 'delete'
AUDIT_LOGIN    = 'login'
AUDIT_LOGOUT   = 'logout'
AUDIT_REGISTER = 'register'

AUDIT_ACTIONS = [
    (AUDIT_CREATE,   'Create'),
    (AUDIT_READ,     'Read'),
    (AUDIT_UPDATE,   'Update'),
    (AUDIT_DELETE,   'Delete'),
    (AUDIT_LOGIN,    'Login'),
    (AUDIT_LOGOUT,   'Logout'),
    (AUDIT_REGISTER, 'Register'),
]

# ── ir.config_parameter Keys ──────────────────────────────────────────────────
CONFIG_JWT_SECRET        = 'cargo.jwt.secret'
CONFIG_JWT_ACCESS_EXPIRY = 'cargo.jwt.access_expiry_seconds'
CONFIG_JWT_REFRESH_EXPIRY= 'cargo.jwt.refresh_expiry_seconds'
CONFIG_RATE_LIMIT_RPM    = 'cargo.rate_limit.requests_per_minute'
CONFIG_COMMISSION_DEFAULT= 'cargo.commission.default_rate'
CONFIG_OTP_EXPIRY_MINS   = 'cargo.otp.expiry_minutes'
CONFIG_MAX_IMAGE_MB      = 'cargo.media.max_image_size_mb'
CONFIG_SUPPORT_EMAIL     = 'cargo.support.email'
CONFIG_SUPPORT_PHONE     = 'cargo.support.phone'
CONFIG_DEFAULT_CURRENCY  = 'cargo.default_currency'
CONFIG_DEFAULT_COUNTRY   = 'cargo.default_country_code'
CONFIG_FCM_SERVER_KEY    = 'cargo.fcm.server_key'

# ── Pagination Defaults ───────────────────────────────────────────────────────
DEFAULT_PAGE      = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE     = 100

# ── Image Constraints ─────────────────────────────────────────────────────────
MAX_IMAGE_SIZE_MB    = 5
ALLOWED_IMAGE_MIMES  = {'image/jpeg', 'image/png', 'image/webp'}
ALLOWED_IMAGE_EXTS   = {'.jpg', '.jpeg', '.png', '.webp'}

# ── OTP ───────────────────────────────────────────────────────────────────────
OTP_LENGTH         = 4
OTP_EXPIRY_MINUTES = 10

# ── Days of Week ──────────────────────────────────────────────────────────────
DAYS_OF_WEEK = [
    ('0', 'Monday'),
    ('1', 'Tuesday'),
    ('2', 'Wednesday'),
    ('3', 'Thursday'),
    ('4', 'Friday'),
    ('5', 'Saturday'),
    ('6', 'Sunday'),
]

# ── Egyptian Phone Regex ──────────────────────────────────────────────────────
# Egyptian mobile numbers: +20 1x xxxx xxxx or 01x xxxx xxxx
EGYPT_PHONE_REGEX = r'^(\+20|0020|0)?1[0125]\d{8}$'

# ── Password Policy ───────────────────────────────────────────────────────────
PASSWORD_MIN_LENGTH = 8
