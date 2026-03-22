"""Constants for pyliebherrhomeapi."""

# API endpoints and configuration
API_BASE_URL = "https://home-api.smartdevice.liebherr.com"
API_VERSION = "v1"
DEFAULT_TIMEOUT = 10

# Control names
CONTROL_TEMPERATURE = "temperature"
CONTROL_SUPER_FROST = "superfrost"
CONTROL_SUPER_COOL = "supercool"
CONTROL_PRESENTATION_LIGHT = "presentationlight"
CONTROL_PARTY_MODE = "partymode"
CONTROL_NIGHT_MODE = "nightmode"
CONTROL_ICE_MAKER = "icemaker"
CONTROL_HYDRO_BREEZE = "hydrobreeze"
CONTROL_BIO_FRESH_PLUS = "biofreshplus"
CONTROL_AUTO_DOOR = "autodoor"

# Temperature units
UNIT_CELSIUS = "°C"
UNIT_FAHRENHEIT = "°F"

# Ice maker modes
ICE_MAKER_OFF = "off"
ICE_MAKER_ON = "on"
ICE_MAKER_MAX_ICE = "max_ice"

# HydroBreeze modes
HYDRO_BREEZE_OFF = "off"
HYDRO_BREEZE_LOW = "low"
HYDRO_BREEZE_MEDIUM = "medium"
HYDRO_BREEZE_HIGH = "high"

# BioFreshPlus modes
BIO_FRESH_PLUS_ZERO_ZERO = "zero_zero"
BIO_FRESH_PLUS_ZERO_MINUS_TWO = "zero_minus_two"
BIO_FRESH_PLUS_MINUS_TWO_MINUS_TWO = "minus_two_minus_two"
BIO_FRESH_PLUS_MINUS_TWO_ZERO = "minus_two_zero"

# Device types
DEVICE_TYPE_FRIDGE = "fridge"
DEVICE_TYPE_FREEZER = "freezer"
DEVICE_TYPE_COMBI = "combi"
DEVICE_TYPE_WINE = "wine"

# Zone positions
ZONE_TOP = "top"
ZONE_MIDDLE = "middle"
ZONE_BOTTOM = "bottom"

# Auto door states
DOOR_CLOSED = "closed"
DOOR_OPEN = "open"
DOOR_MOVING = "moving"

# Default max brightness for presentation light if not provided by API
DEFAULT_PRESENTATION_LIGHT_MAX_BRIGHTNESS = 5
