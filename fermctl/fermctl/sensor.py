"""DS18B20 temperature sensor interface.

Reads temperature from a DS18B20 1-Wire sensor connected to GPIO4.
The sensor appears at /sys/bus/w1/devices/28-xxxx/w1_slave after
enabling the w1-gpio overlay in /boot/config.txt.

In simulation mode, returns a synthetic temperature that drifts
around a base value — useful for development without Pi hardware.
"""

import glob
import logging
import os
import time
import random
import statistics

from . import config

logger = logging.getLogger("fermctl.sensor")

# Cache the device path after first discovery
_device_path = None

# For simulation mode
_sim_temp = 68.0


def _find_device():
    """Locate the DS18B20 sysfs device path."""
    global _device_path
    if _device_path and os.path.exists(_device_path):
        return _device_path

    devices = glob.glob("/sys/bus/w1/devices/28-*/w1_slave")
    if not devices:
        logger.error("No DS18B20 sensor found. Check wiring and dtoverlay=w1-gpio.")
        return None

    _device_path = devices[0]
    device_id = _device_path.split("/")[-2]
    logger.info("Found DS18B20 sensor: %s", device_id)
    return _device_path


def _read_raw():
    """Read the raw sysfs output from the sensor.

    Returns:
        Temperature in Fahrenheit, or None if read failed.
    """
    path = _find_device()
    if path is None:
        return None

    try:
        with open(path, "r") as f:
            lines = f.readlines()
    except OSError as e:
        logger.warning("Failed to read sensor: %s", e)
        return None

    # Line 1 ends with "YES" if CRC check passed
    if len(lines) < 2 or "YES" not in lines[0]:
        logger.warning("Sensor CRC check failed")
        return None

    # Line 2 contains t=XXXXX (millidegrees Celsius)
    try:
        t_pos = lines[1].index("t=")
        temp_c = int(lines[1][t_pos + 2:]) / 1000.0
    except (ValueError, IndexError):
        logger.warning("Could not parse temperature from sensor output")
        return None

    temp_f = temp_c * 9.0 / 5.0 + 32.0
    return temp_f


def _read_simulated():
    """Return a simulated temperature for development without hardware."""
    global _sim_temp
    # Drift randomly by up to ±0.3 F per read
    _sim_temp += random.uniform(-0.3, 0.3)
    # Clamp to reasonable range
    _sim_temp = max(55.0, min(85.0, _sim_temp))
    return round(_sim_temp, 2)


def set_sim_temp(temp_f):
    """Set the simulated temperature base (for testing)."""
    global _sim_temp
    _sim_temp = temp_f


def read_temp_f(previous=None):
    """Read temperature from the DS18B20 sensor.

    Takes multiple readings and returns the median for noise rejection.
    Rejects readings that deviate too far from the previous valid reading.

    Args:
        previous: The last known valid temperature, used for spike rejection.

    Returns:
        Temperature in Fahrenheit as a float, or None if all reads failed.
    """
    if config.SIMULATE:
        return _read_simulated()

    readings = []
    for _ in range(config.SENSOR_READ_ATTEMPTS):
        temp = _read_raw()
        if temp is not None:
            readings.append(temp)
        if _ < config.SENSOR_READ_ATTEMPTS - 1:
            time.sleep(config.SENSOR_READ_DELAY)

    if not readings:
        logger.error("All %d sensor reads failed", config.SENSOR_READ_ATTEMPTS)
        return None

    # Take median to reject outliers
    temp = statistics.median(readings)

    # Spike rejection: if we have a previous reading, reject large jumps
    if previous is not None and abs(temp - previous) > config.MAX_TEMP_CHANGE_F:
        logger.warning(
            "Rejected spike: %.1f F (previous: %.1f F, delta: %.1f F)",
            temp, previous, abs(temp - previous),
        )
        return None

    # Safety bounds check
    if temp > config.MAX_TEMP_F or temp < config.MIN_TEMP_F:
        logger.warning("Temperature %.1f F outside safe bounds [%d, %d]",
                        temp, config.MIN_TEMP_F, config.MAX_TEMP_F)
        return None

    return round(temp, 2)
