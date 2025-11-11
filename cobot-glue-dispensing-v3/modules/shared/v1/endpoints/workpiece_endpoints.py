"""
Workpiece Endpoints - API v1

This module contains all workpiece-related endpoints for the internal API.
All endpoints follow the RESTful pattern: /api/v1/workpieces/{action}
"""

# === WORKPIECE CRUD OPERATIONS ===

# Basic CRUD operations
WORKPIECE_GET_ALL = "/api/v1/workpieces/get-all"
WORKPIECE_SAVE = "/api/v1/workpieces"
WORKPIECE_GET_BY_ID = "/api/v1/workpieces/by-id"
WORKPIECE_DELETE = "/api/v1/workpieces/delete"

# Import operations
WORKPIECE_SAVE_DXF = "/api/v1/workpieces/import/dxf"

# === WORKPIECE CREATION WORKFLOW ===

# Multi-step workpiece creation process
WORKPIECE_CREATE = "/api/v1/workpieces/create"
WORKPIECE_CREATE_STEP_1 = "/api/v1/workpieces/create/step-1"
WORKPIECE_CREATE_STEP_2 = "/api/v1/workpieces/create/step-2"

# === LEGACY ENDPOINTS (for backward compatibility) ===

# Legacy endpoints from pl_ui/Endpoints.py
SAVE_WORKPIECE = "save_workpiece"
SAVE_WORKPIECE_DXF = "save_workpiece_dxf"
WORPIECE_GET_ALL = "WORKPIECE_GET_ALL"  # Note: typo in original
WORKPIECE_GET_BY_ID_LEGACY = "WORKPIECE_GET_BY_ID"
CREATE_WORKPIECE_TOPIC = "CREATE_WORKPIECE_TOPIC"  # This moves the robot to capture position
CREATE_WORKPIECE_STEP_1 = "CREATE_WORKPIECE_STEP_1"
CREATE_WORKPIECE_STEP_2 = "CREATE_WORKPIECE_STEP_2"
WORKPIECE_DELETE_LEGACY = "WORKPIECE_DELETE"

# Legacy Constants.py endpoints
WORKPIECE_CREATE_LEGACY = "workpiece/create"
WORKPIECE_CREATE_STEP_1_LEGACY = "workpiece/create_step_1"
WORKPIECE_CREATE_STEP_2_LEGACY = "workpiece/create_step_2"
WORKPIECE_SAVE_LEGACY = "workpiece/save"
WORKPIECE_DELETE_LEGACY_2 = "workpiece/delete"
WORKPIECE_GET_BY_ID_LEGACY_2 = "workpiece/getbyid"
WORKPIECE_SAVE_DXF_LEGACY = "workpiece/dxf"
WORKPIECE_GET_ALL_LEGACY = "workpiece/getall"