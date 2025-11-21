"""
Glue Application Constants

This module defines constants specific to the glue dispensing application,
including request resources and endpoint definitions.
"""

# === GLUE APPLICATION RESOURCES ===
REQUEST_RESOURCE_GLUE = "Glue"                    # Glue dispensing system resource
REQUEST_RESOURCE_GLUE_NOZZLE = "GlueNozzle"      # Glue nozzle control resource

# === GLUE APPLICATION ENDPOINTS ===

# Glue system configuration management
SETTINGS_GLUE_GET = "/api/v1/settings/glue/get"
SETTINGS_GLUE_SET = "/api/v1/settings/glue/set"


# Glue application specific operations
GLUE_NOZZLE_CLEAN = "glue/nozzle/clean"
GLUE_SPRAY_START = "glue/spray/start"
GLUE_SPRAY_STOP = "glue/spray/stop"
GLUE_CALIBRATE_NOZZLE = "glue/calibrate/nozzle"

