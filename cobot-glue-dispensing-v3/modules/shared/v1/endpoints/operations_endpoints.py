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

# === LEGACY ENDPOINTS (for backward compatibility) ===

# Legacy endpoints from pl_ui/Endpoints.py
START_LEGACY = "start"
STOP_LEGACY = "stop"
PAUSE_LEGACY = "pause"
RUN_REMO = "run_demo"  # Note: original name was RUN_REMO
STOP_DEMO_LEGACY = "stop_demo"
TEST_RUN_LEGACY = "test_run"
CALIBRATE_LEGACY = "calibrate"
HELP_LEGACY = "HELP"

# Legacy Constants.py endpoints
START_LEGACY_2 = "start"
STOP_LEGACY_2 = "stop"
PAUSE_LEGACY_2 = "pause"
TEST_RUN_LEGACY_2 = "test_run"
RUN_REMO_LEGACY = "run_demo"
STOP_DEMO_LEGACY_2 = "stop_demo"