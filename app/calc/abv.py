"""ABV calculation from original and final gravity."""


def calc_abv(og, fg):
    """Calculate alcohol by volume.

    Uses the standard homebrewing formula: ABV = (OG - FG) * 131.25

    Args:
        og: original gravity (e.g. 1.050)
        fg: final gravity (e.g. 1.012)

    Returns:
        ABV as a percentage (e.g. 4.99)
    """
    return round((og - fg) * 131.25, 2)
