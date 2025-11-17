"""
Settings Endpoints - API v1

This module contains all settings-related endpoints for the internal API.
All endpoints follow the RESTful pattern: /api/v1/settings/{domain}
"""

# === ROBOT SETTINGS ===

# Robot configuration management
SETTINGS_ROBOT_GET = "/api/v1/settings/robot"
SETTINGS_ROBOT_SET = "/api/v1/settings/robot/set"

# === CAMERA SETTINGS ===

# Camera configuration management  
SETTINGS_CAMERA_GET = "/api/v1/settings/camera"
SETTINGS_CAMERA_SET = "/api/v1/settings/camera/set"


# === GENERAL SETTINGS ===

# Generic settings operations
SETTINGS_GET = "/api/v1/settings"
SETTINGS_UPDATE = "/api/v1/settings"

