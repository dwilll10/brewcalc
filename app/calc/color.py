"""SRM color calculation using the Morey equation."""

import math


def calc_srm(fermentables, batch_size_gal):
    """Calculate beer color in SRM using Morey's equation.

    Args:
        fermentables: list of dicts with keys:
            - amount_oz: weight in ounces
            - srm: color rating of the fermentable
        batch_size_gal: batch size in gallons

    Returns:
        SRM as a float
    """
    if batch_size_gal <= 0:
        return 0.0

    # Calculate Malt Color Units
    mcu = 0.0
    for f in fermentables:
        amount_lb = f["amount_oz"] / 16.0
        mcu += f["srm"] * amount_lb / batch_size_gal

    if mcu <= 0:
        return 0.0

    # Morey equation
    srm = 1.4922 * math.pow(mcu, 0.6859)
    return round(srm, 1)
