"""Unit tests for brewing calculation module.

Test vectors based on known recipes — values cross-checked against
BeerSmith/Brewfather standard outputs.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.calc.gravity import calc_og, calc_fg
from app.calc.ibu import calc_ibu
from app.calc.color import calc_srm
from app.calc.abv import calc_abv
from app.calc.scaling import scale_recipe


class TestGravity(unittest.TestCase):
    def test_simple_extract_og(self):
        """2.5 lb Light LME (PPG 36) in 1.75 gal => ~1.051"""
        fermentables = [{"amount_oz": 40, "ppg": 36, "type": "extract_liquid"}]
        og = calc_og(fermentables, 1.75)
        self.assertAlmostEqual(og, 1.051, places=2)

    def test_dme_og(self):
        """1 lb Light DME (PPG 44) in 1.75 gal => ~1.025"""
        fermentables = [{"amount_oz": 16, "ppg": 44, "type": "extract_dry"}]
        og = calc_og(fermentables, 1.75)
        self.assertAlmostEqual(og, 1.025, places=2)

    def test_mixed_extract_and_grain(self):
        """2.5 lb LME + 0.25 lb Crystal 40 in 1.75 gal"""
        fermentables = [
            {"amount_oz": 40, "ppg": 36, "type": "extract_liquid"},
            {"amount_oz": 4, "ppg": 34, "type": "grain"},
        ]
        og = calc_og(fermentables, 1.75, efficiency=0.70)
        # LME: 2.5 * 36 / 1.75 = 51.4 points (eff=1.0)
        # Crystal: 0.25 * 34 * 0.70 / 1.75 = 3.4 points
        self.assertAlmostEqual(og, 1.055, places=2)

    def test_zero_batch_size(self):
        og = calc_og([{"amount_oz": 16, "ppg": 36, "type": "extract_liquid"}], 0)
        self.assertEqual(og, 1.000)

    def test_empty_fermentables(self):
        og = calc_og([], 1.75)
        self.assertEqual(og, 1.000)

    def test_fg_from_og(self):
        """OG 1.050 with 75% attenuation => FG ~1.012"""
        fg = calc_fg(1.050, 0.75)
        self.assertAlmostEqual(fg, 1.0125, places=3)

    def test_fg_zero_attenuation(self):
        fg = calc_fg(1.050, 0.0)
        self.assertAlmostEqual(fg, 1.050, places=3)


class TestIBU(unittest.TestCase):
    def test_single_60min_addition(self):
        """0.5 oz Centennial (10% AA) at 60 min, OG 1.050, 1.75 gal"""
        hops = [{"amount_oz": 0.5, "alpha_acid": 10.0, "boil_time_min": 60}]
        ibu = calc_ibu(hops, 1.050, 1.75)
        # Expected ~48-52 IBU (Tinseth)
        self.assertGreater(ibu, 40)
        self.assertLess(ibu, 60)

    def test_flameout_zero_ibu(self):
        """Flameout hops (0 min) contribute no IBU"""
        hops = [{"amount_oz": 1.0, "alpha_acid": 12.0, "boil_time_min": 0}]
        ibu = calc_ibu(hops, 1.050, 1.75)
        self.assertEqual(ibu, 0.0)

    def test_dryhop_negative_time(self):
        """Dry hops (-1 min) contribute no IBU"""
        hops = [{"amount_oz": 1.0, "alpha_acid": 12.0, "boil_time_min": -1}]
        ibu = calc_ibu(hops, 1.050, 1.75)
        self.assertEqual(ibu, 0.0)

    def test_multiple_additions(self):
        """Multiple hop additions sum correctly"""
        hops = [
            {"amount_oz": 0.5, "alpha_acid": 10.0, "boil_time_min": 60},
            {"amount_oz": 0.5, "alpha_acid": 6.0, "boil_time_min": 15},
        ]
        ibu = calc_ibu(hops, 1.050, 1.75)
        # 60-min should be much more than 15-min
        ibu_60_only = calc_ibu([hops[0]], 1.050, 1.75)
        ibu_15_only = calc_ibu([hops[1]], 1.050, 1.75)
        self.assertAlmostEqual(ibu, ibu_60_only + ibu_15_only, places=1)
        self.assertGreater(ibu_60_only, ibu_15_only)

    def test_higher_gravity_lower_utilization(self):
        """Higher gravity wort should have lower hop utilization"""
        hops = [{"amount_oz": 0.5, "alpha_acid": 10.0, "boil_time_min": 60}]
        ibu_low = calc_ibu(hops, 1.040, 1.75)
        ibu_high = calc_ibu(hops, 1.080, 1.75)
        self.assertGreater(ibu_low, ibu_high)


class TestColor(unittest.TestCase):
    def test_light_extract(self):
        """Light LME (4 SRM) in 1.75 gal"""
        fermentables = [{"amount_oz": 40, "srm": 4}]
        srm = calc_srm(fermentables, 1.75)
        # Should be a light golden color, ~5-8 SRM
        self.assertGreater(srm, 3)
        self.assertLess(srm, 12)

    def test_roasted_barley(self):
        """Roasted Barley (500 SRM) should make beer very dark"""
        fermentables = [
            {"amount_oz": 40, "srm": 4},
            {"amount_oz": 4, "srm": 500},
        ]
        srm = calc_srm(fermentables, 1.75)
        self.assertGreater(srm, 25)

    def test_empty_fermentables(self):
        srm = calc_srm([], 1.75)
        self.assertEqual(srm, 0.0)


class TestABV(unittest.TestCase):
    def test_standard_beer(self):
        """OG 1.050, FG 1.012 => ~5.0% ABV"""
        abv = calc_abv(1.050, 1.012)
        self.assertAlmostEqual(abv, 4.99, places=1)

    def test_zero_alcohol(self):
        abv = calc_abv(1.050, 1.050)
        self.assertEqual(abv, 0.0)

    def test_high_gravity(self):
        """OG 1.080, FG 1.015 => ~8.5% ABV"""
        abv = calc_abv(1.080, 1.015)
        self.assertAlmostEqual(abv, 8.53, places=0)


class TestScaling(unittest.TestCase):
    def test_scale_up_doubles_amounts(self):
        """Scaling from 1.75 to 3.5 gal should double ingredient amounts"""
        fermentables = [{"amount_oz": 40, "ppg": 36, "srm": 4, "type": "extract_liquid"}]
        hops = [{"amount_oz": 0.5, "alpha_acid": 10.0, "boil_time_min": 60}]
        result = scale_recipe(fermentables, hops, 1.75, 3.5)
        self.assertAlmostEqual(result["scaled_fermentables"][0]["amount_oz"], 80.0, places=1)
        self.assertAlmostEqual(result["scaled_hops"][0]["amount_oz"], 1.0, places=1)

    def test_og_preserved_after_scaling(self):
        """OG should be approximately the same after scaling"""
        fermentables = [{"amount_oz": 40, "ppg": 36, "srm": 4, "type": "extract_liquid"}]
        hops = [{"amount_oz": 0.5, "alpha_acid": 10.0, "boil_time_min": 60}]
        og_original = calc_og(fermentables, 1.75)
        result = scale_recipe(fermentables, hops, 1.75, 5.0)
        self.assertAlmostEqual(result["og"], og_original, places=2)

    def test_scale_none_on_invalid(self):
        result = scale_recipe([], [], 0, 5.0)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
