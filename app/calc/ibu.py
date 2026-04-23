"""IBU calculation using the Tinseth formula."""

import math


def calc_ibu(hop_additions, og, batch_size_gal):
    """Calculate total IBU using Tinseth's formula.

    Args:
        hop_additions: list of dicts with keys:
            - amount_oz: hop weight in ounces
            - alpha_acid: alpha acid percentage (e.g. 12.0 for 12%)
            - boil_time_min: minutes in boil (0 for flameout, -1 for dry hop)
        og: original gravity (e.g. 1.050)
        batch_size_gal: final batch size in gallons

    Returns:
        Total IBU as a float
    """
    if batch_size_gal <= 0:
        return 0.0

    total_ibu = 0.0
    for hop in hop_additions:
        boil_min = hop["boil_time_min"]
        if boil_min <= 0:
            # Flameout and dry hops contribute negligible IBU
            continue

        alpha = hop["alpha_acid"] / 100.0  # convert percentage to decimal
        amount_oz = hop["amount_oz"]

        # Bigness factor — accounts for reduced utilization at higher gravities
        bigness = 1.65 * math.pow(0.000125, og - 1.0)

        # Boil time factor — utilization increases with time, asymptotically
        boil_factor = (1.0 - math.exp(-0.04 * boil_min)) / 4.15

        utilization = bigness * boil_factor

        # mg/L of alpha acid
        mg_per_l = (alpha * amount_oz * 7490) / batch_size_gal

        total_ibu += utilization * mg_per_l

    return round(total_ibu, 1)
