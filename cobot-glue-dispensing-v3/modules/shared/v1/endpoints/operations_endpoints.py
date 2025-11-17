"""
Operations Endpoints - API v1

This module contains all operation and workflow-related endpoints for the internal API.
All endpoints follow the RESTful pattern: /api/v1/operations/{action}
"""

# === MAIN OPERATIONS ===

# Core system operations
START = "/api/v1/operations/start"
STOP = "/api/v1/operations/stop"
PAUSE = "/api/v1/operations/pause"
CLEAN_NOZZLE = "/api/v1/operations/clean-nozzle"

# === DEMO OPERATIONS ===

# Demo workflow operations
RUN_DEMO = "/api/v1/operations/demo/start"
STOP_DEMO = "/api/v1/operations/demo/stop"

# === TEST OPERATIONS ===

# Testing and validation operations
TEST_RUN = "/api/v1/operations/test-run"

# === CALIBRATION OPERATIONS ===

# System-wide calibration operations
CALIBRATE = "/api/v1/operations/calibrate"

# === GENERAL OPERATIONS ===

# Utility operations
HELP = "/api/v1/operations/help"


