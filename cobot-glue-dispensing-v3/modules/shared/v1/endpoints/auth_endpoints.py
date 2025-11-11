"""
Authentication Endpoints - API v1

This module contains all authentication-related endpoints for the internal API.
All endpoints follow the RESTful pattern: /api/v1/auth/{action}
"""

# === AUTHENTICATION ENDPOINTS ===

# Standard login with username/password
LOGIN = "/api/v1/auth/login"

# QR code login via camera
QR_LOGIN = "/api/v1/auth/qr-login"

# Legacy endpoint names (for backward compatibility)
# These map to the same endpoints as above
LEGACY_LOGIN = "login"
LEGACY_QR_LOGIN = "camera/login"