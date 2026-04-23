"""Configuration for the fermentation controller."""

import os

# --- GPIO Pin Assignments (BCM numbering) ---
SENSOR_GPIO = 4       # DS18B20 data pin (1-Wire default)
HEAT_RELAY_GPIO = 17  # Relay channel 1 — heat wrap
COOL_RELAY_GPIO = 27  # Relay channel 2 — cooling fan

# --- Relay logic ---
# Most opto-isolated relay modules are active-LOW (GPIO LOW = relay ON)
RELAY_ACTIVE_LOW = True

# --- Temperature Controller ---
HYSTERESIS_F = 0.5          # +/- degrees F deadband
CONTROL_INTERVAL_SEC = 10   # How often to read sensor and adjust relays
DEFAULT_TARGET_F = 66.0     # Default target if no profile is set

# --- Sensor ---
SENSOR_READ_ATTEMPTS = 3    # Read N times, take median
SENSOR_READ_DELAY = 0.2     # Seconds between reads
MAX_TEMP_CHANGE_F = 5.0     # Reject readings that jump more than this from previous

# --- Safety ---
WATCHDOG_TIMEOUT_SEC = 60   # If no valid reading for this long, kill relays
MAX_TEMP_F = 90.0           # Emergency shutoff above this temp
MIN_TEMP_F = 32.0           # Emergency shutoff below this temp

# --- Database ---
DB_PATH = os.environ.get(
    "FERMCTL_DB",
    os.path.join(os.path.dirname(__file__), "..", "data", "fermctl.db"),
)

# --- API ---
API_HOST = "0.0.0.0"
API_PORT = int(os.environ.get("FERMCTL_PORT", 5001))

# --- Simulation mode (for development without Pi hardware) ---
SIMULATE = os.environ.get("FERMCTL_SIMULATE", "0") == "1"
