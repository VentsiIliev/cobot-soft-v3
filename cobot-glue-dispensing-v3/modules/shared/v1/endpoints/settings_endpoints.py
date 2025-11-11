"""
Settings Endpoints - API v1

This module contains all settings-related endpoints for the internal API.
All endpoints follow the RESTful pattern: /api/v1/settings/{domain}
"""

# === ROBOT SETTINGS ===

# Robot configuration management
SETTINGS_ROBOT_GET = "/api/v1/settings/robot"
SETTINGS_ROBOT_SET = "/api/v1/settings/robot"

# === CAMERA SETTINGS ===

# Camera configuration management  
SETTINGS_CAMERA_GET = "/api/v1/settings/camera"
SETTINGS_CAMERA_SET = "/api/v1/settings/camera"

# === GLUE SETTINGS ===

# Glue system configuration management
SETTINGS_GLUE_GET = "/api/v1/settings/glue"
SETTINGS_GLUE_SET = "/api/v1/settings/glue"

# === GENERAL SETTINGS ===

# Generic settings operations
SETTINGS_GET = "/api/v1/settings"
SETTINGS_UPDATE = "/api/v1/settings"

# === LEGACY ENDPOINTS (for backward compatibility) ===

# Legacy endpoints from pl_ui/Endpoints.py
GET_SETTINGS = "settings/get"
UPDATE_SETTINGS = "settings/update"

# Legacy Constants.py endpoints
SETTINGS_ROBOT_GET_LEGACY = "settings/robot/get"
SETTINGS_ROBOT_SET_LEGACY = "settings/robot/set"
SETTINGS_GLUE_GET_LEGACY = "settings/glue/get"
SETTINGS_GLUE_SET_LEGACY = "settings/glue/set"
SETTINGS_CAMERA_GET_LEGACY = "settings/camera/get"
SETTINGS_CAMERA_SET_LEGACY = "settings/camera/set"