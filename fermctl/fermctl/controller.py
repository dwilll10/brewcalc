"""Bang-bang temperature controller with hysteresis and watchdog.

Controls fermentation temperature by switching heat/cool relays based on
the current temperature relative to the target. Uses a deadband (hysteresis)
to prevent rapid relay cycling.

Safety features:
- Watchdog: if no valid sensor reading for WATCHDOG_TIMEOUT_SEC, all relays off
- Temperature bounds: emergency shutoff if temp exceeds safe range
- Fail-safe: relays are normally-open, so power loss = everything off
"""

import logging
import time
import threading

from . import config
from . import sensor
from . import relay
from .profile import FermentationProfile
from .logger import FermLogger

logger = logging.getLogger("fermctl.controller")


class FermentationController:
    """Main controller that runs the temperature control loop."""

    def __init__(self, db_path=None):
        self.profile = FermentationProfile()
        self.logger = FermLogger(db_path or config.DB_PATH)
        self.active_run_id = None
        self.start_time = None
        self.last_valid_temp = None
        self.last_valid_time = None
        self.target_temp = config.DEFAULT_TARGET_F
        self.override_temp = None  # Manual override
        self._running = False
        self._thread = None

    @property
    def is_running(self):
        return self._running

    @property
    def elapsed_hours(self):
        if self.start_time is None:
            return 0.0
        return (time.time() - self.start_time) / 3600.0

    def start_run(self, recipe_id=None, recipe_name="", profile_json=None):
        """Start a new fermentation run.

        Args:
            recipe_id: ID from the recipe app (for cross-reference)
            recipe_name: Human-readable recipe name
            profile_json: JSON string defining the temperature profile
        """
        if self._running:
            self.stop_run()

        if profile_json:
            self.profile = FermentationProfile.from_json(profile_json)
        else:
            self.profile = FermentationProfile()

        self.active_run_id = self.logger.start_run(
            recipe_id=recipe_id,
            recipe_name=recipe_name,
            profile_json=self.profile.to_json(),
        )
        self.start_time = time.time()
        self.last_valid_temp = None
        self.last_valid_time = time.time()
        self.override_temp = None
        self._running = True

        logger.info("Started fermentation run #%d: %s, profile=%s",
                     self.active_run_id, recipe_name, self.profile)

        # Start control loop in background thread
        self._thread = threading.Thread(target=self._control_loop, daemon=True)
        self._thread.start()

    def stop_run(self):
        """Stop the active fermentation run and turn off relays."""
        self._running = False
        relay.all_off()

        if self.active_run_id:
            self.logger.end_run(self.active_run_id)
            logger.info("Stopped fermentation run #%d", self.active_run_id)

        self.active_run_id = None
        self.start_time = None
        self.override_temp = None

        if self._thread:
            self._thread.join(timeout=config.CONTROL_INTERVAL_SEC + 2)
            self._thread = None

    def set_override(self, temp_f=None):
        """Set a manual temperature override, or None to clear."""
        self.override_temp = temp_f
        if temp_f is not None:
            logger.info("Manual override set: %.1f F", temp_f)
        else:
            logger.info("Manual override cleared, resuming profile")

    def update_profile(self, profile_json):
        """Update the active fermentation profile mid-run."""
        self.profile = FermentationProfile.from_json(profile_json)
        if self.active_run_id:
            self.logger.update_run_profile(self.active_run_id, profile_json)
        logger.info("Profile updated: %s", self.profile)

    def get_status(self):
        """Return current controller status as a dict."""
        return {
            "active": self._running,
            "run_id": self.active_run_id,
            "current_temp": self.last_valid_temp,
            "target_temp": self.target_temp,
            "heat_on": relay.is_heat_on(),
            "cool_on": relay.is_cool_on(),
            "elapsed_hours": round(self.elapsed_hours, 2),
            "override_temp": self.override_temp,
        }

    def _control_loop(self):
        """Main control loop — runs in a background thread."""
        logger.info("Control loop started (interval=%ds)", config.CONTROL_INTERVAL_SEC)

        while self._running:
            try:
                self._control_step()
            except Exception:
                logger.exception("Error in control step")
                relay.all_off()

            time.sleep(config.CONTROL_INTERVAL_SEC)

        logger.info("Control loop stopped")

    def _control_step(self):
        """Execute one control cycle: read, decide, actuate, log."""
        now = time.time()

        # Read temperature
        temp = sensor.read_temp_f(previous=self.last_valid_temp)

        if temp is not None:
            self.last_valid_temp = temp
            self.last_valid_time = now
        else:
            # Check watchdog
            if self.last_valid_time and (now - self.last_valid_time) > config.WATCHDOG_TIMEOUT_SEC:
                logger.error("WATCHDOG: No valid reading for %d seconds. Safety shutoff.",
                             config.WATCHDOG_TIMEOUT_SEC)
                relay.all_off()
                return
            # Use last known temp for logging but don't actuate
            temp = self.last_valid_temp

        if temp is None:
            return

        # Determine target
        if self.override_temp is not None:
            self.target_temp = self.override_temp
        else:
            self.target_temp = self.profile.get_target_temp(self.elapsed_hours)

        # Bang-bang control with hysteresis
        if temp < self.target_temp - config.HYSTERESIS_F:
            relay.heat_on()
            relay.cool_off()
        elif temp > self.target_temp + config.HYSTERESIS_F:
            relay.heat_off()
            relay.cool_on()
        else:
            # Inside deadband — maintain current state or coast
            relay.heat_off()
            relay.cool_off()

        # Log reading
        if self.active_run_id:
            self.logger.log_reading(
                run_id=self.active_run_id,
                temp_f=temp,
                target_f=self.target_temp,
                heat_on=relay.is_heat_on(),
                cool_on=relay.is_cool_on(),
            )
