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
