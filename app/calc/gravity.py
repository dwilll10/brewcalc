"""Original gravity and final gravity calculations."""

import math


def calc_og(fermentables, batch_size_gal, efficiency=1.0):
    """Calculate original gravity from fermentable additions.

    Args:
        fermentables: list of dicts with keys:
            - amount_oz: weight in ounces
            - ppg: points per pound per gallon
            - type: fermentable type (extract_liquid, extract_dry, grain, sugar)
        batch_size_gal: batch size in gallons
        efficiency: mash efficiency (1.0 for extract, 0.65-0.80 for all-grain)

    Returns:
        OG as a float (e.g. 1.050)
    """
    if batch_size_gal <= 0:
        return 1.000

    total_points = 0.0
    for f in fermentables:
        amount_lb = f["amount_oz"] / 16.0
        ppg = f["ppg"]
        # Extract types get efficiency=1.0 regardless of setting
        if f.get("type", "").startswith("extract") or f.get("type") == "sugar":
            eff = 1.0
        else:
            eff = efficiency
        total_points += amount_lb * ppg * eff

    og_points = total_points / batch_size_gal
    return 1.0 + og_points / 1000.0


def calc_fg(og, attenuation):
    """Calculate final gravity from OG and yeast attenuation.

    Args:
        og: original gravity (e.g. 1.050)
        attenuation: apparent attenuation as decimal (e.g. 0.75)

    Returns:
        FG as a float (e.g. 1.012)
    """
    og_points = (og - 1.0) * 1000.0
    fg_points = og_points * (1.0 - attenuation)
    return 1.0 + fg_points / 1000.0
