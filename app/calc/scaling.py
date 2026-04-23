"""Batch size scaling for recipes."""

from .gravity import calc_og
from .ibu import calc_ibu
from .color import calc_srm


def scale_recipe(fermentables, hop_additions, old_batch_gal, new_batch_gal):
    """Scale recipe ingredients from one batch size to another.

    Scales ingredient amounts linearly, then recalculates IBU and SRM
    (which are affected by batch size non-linearly).

    Args:
        fermentables: list of fermentable dicts (amount_oz, ppg, srm, type)
        hop_additions: list of hop dicts (amount_oz, alpha_acid, boil_time_min)
        old_batch_gal: original batch size in gallons
        new_batch_gal: target batch size in gallons

    Returns:
        dict with scaled_fermentables, scaled_hops, og, ibu, srm
    """
    if old_batch_gal <= 0 or new_batch_gal <= 0:
        return None

    ratio = new_batch_gal / old_batch_gal

    scaled_fermentables = []
    for f in fermentables:
        scaled = dict(f)
        scaled["amount_oz"] = round(f["amount_oz"] * ratio, 2)
        scaled_fermentables.append(scaled)

    scaled_hops = []
    for h in hop_additions:
        scaled = dict(h)
        scaled["amount_oz"] = round(h["amount_oz"] * ratio, 2)
        scaled_hops.append(scaled)

    # Recalculate stats with scaled amounts
    og = calc_og(scaled_fermentables, new_batch_gal)
    ibu = calc_ibu(scaled_hops, og, new_batch_gal)
    srm = calc_srm(scaled_fermentables, new_batch_gal)

    return {
        "scaled_fermentables": scaled_fermentables,
        "scaled_hops": scaled_hops,
        "og": og,
        "ibu": ibu,
        "srm": srm,
    }
