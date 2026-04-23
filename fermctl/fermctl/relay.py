"""GPIO relay control for heating and cooling.

Controls a 2-channel relay module connected to the Raspberry Pi GPIO.
Relays are normally-open (NO), meaning power loss = relays off = safe state.

Most opto-isolated relay modules are active-LOW: GPIO LOW energizes the relay.
This is configurable via config.RELAY_ACTIVE_LOW.

In simulation mode, tracks relay state in memory without touching GPIO.
"""

import logging

from . import config

logger = logging.getLogger("fermctl.relay")

# Track current state
_heat_on = False
_cool_on = False
_gpio_initialized = False


def _init_gpio():
    """Initialize GPIO pins for relay control."""
    global _gpio_initialized
    if _gpio_initialized:
        return

    if config.SIMULATE:
        logger.info("Simulation mode: GPIO not initialized")
        _gpio_initialized = True
        return

    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Set relay pins as outputs, start with relays OFF
        off_state = GPIO.HIGH if config.RELAY_ACTIVE_LOW else GPIO.LOW
        GPIO.setup(config.HEAT_RELAY_GPIO, GPIO.OUT, initial=off_state)
        GPIO.setup(config.COOL_RELAY_GPIO, GPIO.OUT, initial=off_state)

        _gpio_initialized = True
        logger.info("GPIO initialized: heat=GPIO%d, cool=GPIO%d",
                     config.HEAT_RELAY_GPIO, config.COOL_RELAY_GPIO)
    except (ImportError, RuntimeError) as e:
        logger.error("Failed to initialize GPIO: %s. Running in simulation mode.", e)
        config.SIMULATE = True
        _gpio_initialized = True


def _set_pin(pin, on):
    """Set a GPIO pin to the appropriate state for on/off."""
    if config.SIMULATE:
        return

    import RPi.GPIO as GPIO
    if config.RELAY_ACTIVE_LOW:
        GPIO.output(pin, GPIO.LOW if on else GPIO.HIGH)
    else:
        GPIO.output(pin, GPIO.HIGH if on else GPIO.LOW)


def heat_on():
    """Turn on the heating relay."""
    global _heat_on
    _init_gpio()
    if not _heat_on:
        _set_pin(config.HEAT_RELAY_GPIO, True)
        _heat_on = True
        logger.debug("Heat ON")


def heat_off():
    """Turn off the heating relay."""
    global _heat_on
    _init_gpio()
    if _heat_on:
        _set_pin(config.HEAT_RELAY_GPIO, False)
        _heat_on = False
        logger.debug("Heat OFF")


def cool_on():
    """Turn on the cooling relay."""
    global _cool_on
    _init_gpio()
    if not _cool_on:
        _set_pin(config.COOL_RELAY_GPIO, True)
        _cool_on = True
        logger.debug("Cool ON")


def cool_off():
    """Turn off the cooling relay."""
    global _cool_on
    _init_gpio()
    if _cool_on:
        _set_pin(config.COOL_RELAY_GPIO, False)
        _cool_on = False
        logger.debug("Cool OFF")


def all_off():
    """Turn off both relays. Used for safety shutoff."""
    heat_off()
    cool_off()


def is_heat_on():
    return _heat_on


def is_cool_on():
    return _cool_on


def cleanup():
    """Release GPIO resources on shutdown."""
    all_off()
    if not config.SIMULATE:
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
            logger.info("GPIO cleaned up")
        except (ImportError, RuntimeError):
            pass
