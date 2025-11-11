# Endpoints.py

# -----------------------------
# Read Operations (GET)
# -----------------------------
STATS_GENERATOR = "/stats/generator"
STATS_TRANSDUCER = "/stats/transducer"
STATS_PUMPS = "/stats/pumps"
STATS_PUMP_BY_ID = "/stats/pumps/{pump_id}"
STATS_FAN = "/stats/fan"
STATS_LOADCELLS = "/stats/loadcells"
STATS_LOADCELL_BY_ID = "/stats/loadcells/{loadcell_id}"

# -----------------------------
# Write / Action Operations (POST / PUT)
# -----------------------------
RESET_GENERATOR = "/reset/generator"
RESET_TRANSDUCER = "/reset/transducer"
RESET_FAN = "/reset/fan"
RESET_PUMP_MOTOR = "/reset/pumps/{pump_id}/motor"
RESET_PUMP_BELT = "/reset/pumps/{pump_id}/belt"
RESET_LOADCELL = "/reset/loadcells/{loadcell_id}"
