from flask import Blueprint, render_template
from ..models import Recipe

bp = Blueprint("brewday", __name__, url_prefix="/brewday")


@bp.route("/<int:recipe_id>")
def timer(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    # Build brew day steps from recipe ingredients
    steps = _generate_steps(recipe)
    return render_template("brewday/timer.html", recipe=recipe, steps=steps)


def _generate_steps(recipe):
    """Generate an ordered list of brew day steps from a recipe."""
    steps = []
    steep_grains = [rf for rf in recipe.fermentables if rf.use == "steep"]
    boil_additions = [rf for rf in recipe.fermentables if rf.use in ("boil", "late")]
    boil_hops = sorted(
        [rh for rh in recipe.hops if rh.use == "boil"],
        key=lambda h: h.boil_time_min,
        reverse=True,
    )
    flameout_hops = [rh for rh in recipe.hops if rh.use == "flameout"]
    dryhop_hops = [rh for rh in recipe.hops if rh.use == "dryhop"]

    water_gal = recipe.batch_size * 1.15  # ~15% extra for boil-off

    steps.append({
        "text": f"Heat {water_gal:.1f} gallons of water to 155 F",
        "timer": None,
        "type": "action",
        "equipment": ["Brew kettle (3 gal)", "Thermometer", "Stir spoon"],
    })

    if steep_grains:
        grain_list = ", ".join(
            f"{rf.amount_oz} oz {rf.fermentable.name}" for rf in steep_grains
        )
        steps.append({
            "text": f"Steep grains: {grain_list} at 150-155 F",
            "timer": 30 * 60,
            "type": "timer",
            "equipment": ["Mesh grain bag", "Thermometer"],
        })
        steps.append({
            "text": "Remove grain bag, let drip. Do not squeeze.",
            "timer": None,
            "type": "action",
            "equipment": ["Heat-resistant gloves or tongs"],
        })

    steps.append({
        "text": "Bring to a boil",
        "timer": None,
        "type": "action",
        "equipment": ["Brew kettle"],
    })

    if boil_additions:
        extract_list = ", ".join(
            f"{rf.amount_oz} oz {rf.fermentable.name}" for rf in boil_additions
        )
        steps.append({
            "text": f"Remove from heat. Stir in extracts: {extract_list}. Return to boil.",
            "timer": None,
            "type": "action",
            "equipment": ["Stir spoon", "Digital scale"],
        })

    # Hop additions during boil
    if boil_hops:
        first_hop = boil_hops[0]
        steps.append({
            "text": f"Start {recipe.boil_time}-minute boil. Add {first_hop.amount_oz} oz {first_hop.hop.name} (bittering)",
            "timer": recipe.boil_time * 60,
            "type": "timer",
            "equipment": ["Digital scale", "Hop bag (optional)"],
        })
        for hop in boil_hops[1:]:
            mins_left = hop.boil_time_min
            steps.append({
                "text": f"At {mins_left} min remaining: add {hop.amount_oz} oz {hop.hop.name}",
                "timer": None,
                "type": "alert",
                "alert_at": (recipe.boil_time - mins_left) * 60,
                "equipment": ["Digital scale"],
            })
    else:
        steps.append({
            "text": f"Start {recipe.boil_time}-minute boil",
            "timer": recipe.boil_time * 60,
            "type": "timer",
            "equipment": ["Brew kettle"],
        })

    if flameout_hops:
        hop_list = ", ".join(f"{rh.amount_oz} oz {rh.hop.name}" for rh in flameout_hops)
        steps.append({
            "text": f"Flameout: add {hop_list}. Steep 10 min.",
            "timer": 10 * 60,
            "type": "timer",
            "equipment": ["Digital scale", "Hop bag (optional)"],
        })

    steps.append({
        "text": "Chill wort to ~68-70 F (ice bath or wort chiller)",
        "timer": None,
        "type": "action",
        "equipment": ["Ice bath or wort chiller", "Thermometer", "Sink or large basin"],
    })

    steps.append({
        "text": "Take hydrometer reading to verify OG",
        "timer": None,
        "type": "action",
        "equipment": ["Hydrometer", "Test jar", "Turkey baster or wine thief"],
    })

    yeast_name = recipe.yeast.name if recipe.yeast else "yeast"
    steps.append({
        "text": f"Transfer to fermenter, pitch {yeast_name}. Seal with airlock.",
        "timer": None,
        "type": "action",
        "equipment": ["Fermenter (2 gal)", "Auto-siphon + tubing", "Airlock + stopper", "Star San spray bottle"],
    })

    steps.append({
        "text": "Clean all equipment thoroughly",
        "timer": None,
        "type": "action",
        "equipment": ["PBW or OxiClean", "Brush", "Spray bottle"],
    })

    if dryhop_hops:
        hop_list = ", ".join(f"{rh.amount_oz} oz {rh.hop.name}" for rh in dryhop_hops)
        steps.append({
            "text": f"Dry hop (add after 3-5 days): {hop_list}",
            "timer": None,
            "type": "note",
            "equipment": ["Digital scale", "Sanitized hop bag or loose addition"],
        })

    return steps
