"""Temperature profile management.

A fermentation profile is a list of waypoints defining target temperature
over time. Between waypoints, temperature is linearly interpolated.

Example profile (standard ale):
[
    {"hours": 0,   "temp_f": 66},   # Start at 66 F
    {"hours": 72,  "temp_f": 66},   # Hold 66 F for 3 days
    {"hours": 96,  "temp_f": 70},   # Ramp to 70 F over day 4 (diacetyl rest)
    {"hours": 120, "temp_f": 72}    # Ramp to 72 F, hold until done
]
"""

import json
import logging

from . import config

logger = logging.getLogger("fermctl.profile")


class FermentationProfile:
    """Manages a temperature profile with time-based interpolation."""

    def __init__(self, waypoints=None):
        """Initialize with a list of waypoint dicts.

        Args:
            waypoints: List of {"hours": float, "temp_f": float} dicts,
                       sorted by hours ascending.
        """
        if waypoints:
            self.waypoints = sorted(waypoints, key=lambda w: w["hours"])
        else:
            self.waypoints = [{"hours": 0, "temp_f": config.DEFAULT_TARGET_F}]

    @classmethod
    def from_json(cls, json_str):
        """Create a profile from a JSON string."""
        try:
            data = json.loads(json_str)
            if isinstance(data, list) and len(data) > 0:
                return cls(data)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Invalid profile JSON, using default")
        return cls()

    def to_json(self):
        """Serialize the profile to a JSON string."""
        return json.dumps(self.waypoints)

    def get_target_temp(self, elapsed_hours):
        """Get the target temperature at a given elapsed time.

        Linearly interpolates between waypoints. Before the first waypoint,
        returns the first waypoint's temp. After the last, returns the last.

        Args:
            elapsed_hours: Hours since fermentation started.

        Returns:
            Target temperature in Fahrenheit.
        """
        if not self.waypoints:
            return config.DEFAULT_TARGET_F

        # Before first waypoint
        if elapsed_hours <= self.waypoints[0]["hours"]:
            return self.waypoints[0]["temp_f"]

        # After last waypoint — hold at final temp
        if elapsed_hours >= self.waypoints[-1]["hours"]:
            return self.waypoints[-1]["temp_f"]

        # Find the two surrounding waypoints and interpolate
        for i in range(len(self.waypoints) - 1):
            w1 = self.waypoints[i]
            w2 = self.waypoints[i + 1]
            if w1["hours"] <= elapsed_hours <= w2["hours"]:
                span = w2["hours"] - w1["hours"]
                if span == 0:
                    return w2["temp_f"]
                frac = (elapsed_hours - w1["hours"]) / span
                return w1["temp_f"] + frac * (w2["temp_f"] - w1["temp_f"])

        return self.waypoints[-1]["temp_f"]

    def __repr__(self):
        pts = ", ".join(f"{w['hours']}h:{w['temp_f']}F" for w in self.waypoints)
        return f"FermentationProfile([{pts}])"
