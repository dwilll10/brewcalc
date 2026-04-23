"""Tests for the fermentation controller modules."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Force simulation mode before importing modules
os.environ["FERMCTL_SIMULATE"] = "1"

from fermctl.profile import FermentationProfile
from fermctl.logger import FermLogger
from fermctl.sensor import read_temp_f, set_sim_temp
from fermctl import config


class TestProfile(unittest.TestCase):
    def test_single_waypoint(self):
        p = FermentationProfile([{"hours": 0, "temp_f": 66}])
        self.assertEqual(p.get_target_temp(0), 66)
        self.assertEqual(p.get_target_temp(100), 66)

    def test_linear_interpolation(self):
        p = FermentationProfile([
            {"hours": 0, "temp_f": 66},
            {"hours": 24, "temp_f": 72},
        ])
        self.assertEqual(p.get_target_temp(0), 66)
        self.assertEqual(p.get_target_temp(24), 72)
        self.assertAlmostEqual(p.get_target_temp(12), 69, places=1)

    def test_hold_after_last_waypoint(self):
        p = FermentationProfile([
            {"hours": 0, "temp_f": 66},
            {"hours": 72, "temp_f": 66},
            {"hours": 96, "temp_f": 70},
        ])
        self.assertEqual(p.get_target_temp(200), 70)

    def test_before_first_waypoint(self):
        p = FermentationProfile([{"hours": 5, "temp_f": 66}])
        self.assertEqual(p.get_target_temp(0), 66)

    def test_ale_profile(self):
        """Standard ale: hold 66 for 3 days, ramp to 70, then 72."""
        p = FermentationProfile([
            {"hours": 0, "temp_f": 66},
            {"hours": 72, "temp_f": 66},
            {"hours": 96, "temp_f": 70},
            {"hours": 120, "temp_f": 72},
        ])
        self.assertEqual(p.get_target_temp(36), 66)     # Day 1.5
        self.assertEqual(p.get_target_temp(72), 66)      # End of hold
        self.assertAlmostEqual(p.get_target_temp(84), 68, places=0)  # Mid-ramp
        self.assertEqual(p.get_target_temp(120), 72)     # Final

    def test_from_json(self):
        json_str = '[{"hours": 0, "temp_f": 64}, {"hours": 48, "temp_f": 68}]'
        p = FermentationProfile.from_json(json_str)
        self.assertEqual(p.get_target_temp(0), 64)
        self.assertAlmostEqual(p.get_target_temp(24), 66, places=1)

    def test_from_invalid_json(self):
        p = FermentationProfile.from_json("not json")
        self.assertEqual(p.get_target_temp(0), config.DEFAULT_TARGET_F)

    def test_to_json_roundtrip(self):
        original = [{"hours": 0, "temp_f": 66}, {"hours": 72, "temp_f": 70}]
        p = FermentationProfile(original)
        p2 = FermentationProfile.from_json(p.to_json())
        self.assertEqual(p.get_target_temp(36), p2.get_target_temp(36))


class TestLogger(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mktemp(suffix=".db")
        self.logger = FermLogger(self.tmp)

    def tearDown(self):
        if os.path.exists(self.tmp):
            os.unlink(self.tmp)

    def test_create_and_end_run(self):
        run_id = self.logger.start_run(recipe_id=1, recipe_name="Test Ale")
        self.assertIsNotNone(run_id)

        run = self.logger.get_run(run_id)
        self.assertEqual(run["recipe_name"], "Test Ale")
        self.assertEqual(run["active"], 1)

        self.logger.end_run(run_id)
        run = self.logger.get_run(run_id)
        self.assertEqual(run["active"], 0)
        self.assertIsNotNone(run["ended_at"])

    def test_log_and_get_readings(self):
        run_id = self.logger.start_run()
        self.logger.log_reading(run_id, 66.5, 66.0, True, False)
        self.logger.log_reading(run_id, 66.2, 66.0, False, False)

        readings = self.logger.get_readings(run_id)
        self.assertEqual(len(readings), 2)
        self.assertAlmostEqual(readings[0]["temp_f"], 66.5)
        self.assertEqual(readings[0]["heat_on"], 1)

    def test_get_latest_reading(self):
        run_id = self.logger.start_run()
        self.logger.log_reading(run_id, 65.0, 66.0, True, False)
        self.logger.log_reading(run_id, 66.5, 66.0, False, False)

        latest = self.logger.get_latest_reading(run_id)
        self.assertAlmostEqual(latest["temp_f"], 66.5)

    def test_list_runs(self):
        self.logger.start_run(recipe_name="Ale 1")
        self.logger.start_run(recipe_name="Stout 2")

        runs = self.logger.get_runs()
        self.assertEqual(len(runs), 2)
        self.assertEqual(runs[0]["recipe_name"], "Stout 2")  # Most recent first


class TestSensor(unittest.TestCase):
    def test_simulated_reading(self):
        """In simulation mode, should return a float in reasonable range."""
        config.SIMULATE = True
        set_sim_temp(66.0)
        temp = read_temp_f()
        self.assertIsNotNone(temp)
        self.assertGreater(temp, 55)
        self.assertLess(temp, 85)

    def test_simulated_readings_vary(self):
        """Simulated readings should drift slightly."""
        config.SIMULATE = True
        set_sim_temp(66.0)
        readings = [read_temp_f() for _ in range(10)]
        # Not all identical
        self.assertGreater(len(set(readings)), 1)


if __name__ == "__main__":
    unittest.main()
