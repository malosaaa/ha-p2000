"""Constants for the P2000 Scraper integration."""
from typing import Final
from datetime import timedelta
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

DOMAIN: Final = "p2000_alarmfase1"
PLATFORMS: Final[list[str]] = ["sensor"]
MANUFACTURER: Final = "Malosaaa - alarmfase1.nl"

# Configuration Keys
CONF_REGION_PATH: Final = "region_path"
CONF_INSTANCE_NAME: Final = "instance_name" # User-defined name for the device/instance
CONF_SENSORS: Final = "sensors"
CONF_FILTERS: Final = "filters"
CONF_FILTER_AMBULANCE: Final = "filter_ambulance"
CONF_FILTER_FIRE: Final = "filter_fire"
CONF_FILTER_POLICE: Final = "filter_police"
CONF_FILTER_OTHER: Final = "filter_other" # For KNRM, Traumaheli, etc.
CONF_SCAN_INTERVAL: Final = "scan_interval"
DEFAULT_SCAN_INTERVAL: Final = 120  # seconds (2 minutes)
MIN_SCAN_INTERVAL: Final = 30      # seconds

# API Details
BASE_URL: Final = "https://www.alarmfase1.nl/"
API_TIMEOUT: Final = 20 # Increased timeout for scraping

# Update Interval
DEFAULT_UPDATE_INTERVAL: Final = timedelta(seconds=90) # Check every 90 seconds? Adjust as needed.

# Data Keys from scraping (used for sensor selection and attributes)
# These should match the keys returned by the api.py parser
SCRAPED_DATA_KEYS: Final[list[str]] = [
    "priority_code", # Like P 1, A 2 etc. (Primary sensor state)
    "message",
    "time", # Parsed datetime object
    "city",
    "address",
    "postalcode",
    "latitude",
    "longitude",
    "service_type", # Inferred type: Ambulance, Fire Department, Police, Other
    "raw_time_str", # Original time string like "xx minuten geleden" or "hh:mm:ss"
    "absolute_time_str", # The string from the title attribute used for parsing
]

# Default sensor selection (which ones are enabled by default)
DEFAULT_ENABLED_SENSORS: Final[list[str]] = [
    "priority_code",
    "message",
    "time",
    "city",
    "address",
    "service_type",
    "latitude",
    "longitude",
]

# Sensor configuration schema used in config flow options
SENSOR_SCHEMA = vol.Schema({
    vol.Optional(key, default=(key in DEFAULT_ENABLED_SENSORS)): cv.boolean
    for key in SCRAPED_DATA_KEYS
})

# Filter configuration schema used in config flow options
FILTER_SCHEMA = vol.Schema({
    vol.Optional(CONF_FILTER_AMBULANCE, default=True): cv.boolean,
    vol.Optional(CONF_FILTER_FIRE, default=True): cv.boolean,
    vol.Optional(CONF_FILTER_POLICE, default=True): cv.boolean,
    vol.Optional(CONF_FILTER_OTHER, default=True): cv.boolean,
})

# Mapping from Font Awesome icon class fragments to Service Types
SERVICE_TYPE_ICON_MAP: Final[dict[str, str]] = {
    "ambulance": "Ambulance",
    "fire-extinguisher": "Fire Department", # Or 'fire' ? Check actual class
    # Police often doesn't have a specific icon here, might need text parsing?
    # Add other common ones based on observation
    "helicopter": "Trauma Heli",
    "life-ring": "KNRM / Water Rescue",
    # Add more as needed
}
DEFAULT_SERVICE_TYPE: Final = "Other"


# Diagnostics
DIAG_CONFIG_ENTRY = "config_entry"
DIAG_OPTIONS = "options"
DIAG_COORDINATOR_DATA = "coordinator_data"