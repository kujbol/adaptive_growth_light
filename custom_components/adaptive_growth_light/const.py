"""Constants for the Adaptive Growth Light integration."""

DOMAIN = "adaptive_growth_light"

# Configuration keys
CONF_NAME = "name"
CONF_TARGET_ENTITY = "target_entity"
CONF_TARGET_PHOTOPERIOD = "target_photoperiod"
CONF_LIGHTING_MODE = "lighting_mode"
CONF_MORNING_SPLIT = "morning_split"
CONF_DAYLIGHT_OVERLAP = "daylight_overlap"
CONF_EARLIEST_START = "earliest_start"
CONF_LATEST_END = "latest_end"

# Lighting modes
MODE_MORNING = "morning"
MODE_EVENING = "evening"
MODE_BOTH = "both"
LIGHTING_MODES = [MODE_MORNING, MODE_EVENING, MODE_BOTH]

# Default values
DEFAULT_NAME = "Plant Growth Light"
DEFAULT_TARGET_PHOTOPERIOD = 14.0  # hours
DEFAULT_LIGHTING_MODE = MODE_BOTH
DEFAULT_MORNING_SPLIT = 50.0  # percentage in morning
DEFAULT_DAYLIGHT_OVERLAP = 1.0  # hours overlap with daylight
DEFAULT_EARLIEST_START: str | None = None  # None by default (no cut-off restriction)
DEFAULT_LATEST_END: str | None = None  # None by default (no cut-off restriction)
DEFAULT_ENABLED = True

# Control boundaries
MIN_PHOTOPERIOD = 4.0
MAX_PHOTOPERIOD = 20.0
STEP_PHOTOPERIOD = 0.5

MIN_SPLIT = 0.0
MAX_SPLIT = 100.0
STEP_SPLIT = 5.0

MIN_OVERLAP = 0.0
MAX_OVERLAP = 4.0
STEP_OVERLAP = 0.25

# Frontend card path
FRONTEND_URL = "/adaptive_growth_light/adaptive-growth-light-card.js"
FRONTEND_DIR = "frontend"
