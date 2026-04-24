from flask import Blueprint, render_template
from ..models import Recipe

bp = Blueprint("brewday", __name__, url_prefix="/brewday")


@bp.route("/<int:recipe_id>")
def timer(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    # Build brew day steps from recipe ingredients
    steps = _generate_steps(recipe)
    return render_template("brewday/timer.html", recipe=recipe, steps=steps)


def _fmt_adjunct(adj):
    amount = f"{adj.amount} " if adj.amount else ""
    return f"{amount}{adj.name}"


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

    adjuncts = list(recipe.adjuncts)
    mash_adj = [a for a in adjuncts if a.stage == "mash"]
    boil_adj = [a for a in adjuncts if a.stage == "boil"]
    flameout_adj = [a for a in adjuncts if a.stage == "flameout"]
    primary_adj = [a for a in adjuncts if a.stage == "primary"]
    secondary_adj = [a for a in adjuncts if a.stage == "secondary"]
    bottling_adj = [a for a in adjuncts if a.stage == "bottling"]

    water_gal = recipe.batch_size * 1.15  # ~15% extra for boil-off

    steps.append({
        "text": f"Heat {water_gal:.1f} gallons of water to 155 F",
        "timer": None,
        "type": "action",
        "equipment": ["Brew kettle (3 gal)", "Thermometer", "Stir spoon"],
    })

    if steep_grains or mash_adj:
        grain_list = ", ".join(
            f"{rf.amount_oz} oz {rf.fermentable.name}" for rf in steep_grains
        )
        extras = ", ".join(_fmt_adjunct(a) for a in mash_adj)
        if grain_list and extras:
            steep_text = f"Steep grains: {grain_list} (plus {extras}) at 150-155 F"
        elif grain_list:
            steep_text = f"Steep grains: {grain_list} at 150-155 F"
        else:
            steep_text = f"Steep {extras} at 150-155 F"
        steps.append({
            "text": steep_text,
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

    # Build boil-addition alerts (hops + boil adjuncts) keyed by minutes remaining
    boil_timeline = []  # list of (mins_remaining, description)
    for hop in boil_hops[1:]:
        boil_timeline.append((hop.boil_time_min, f"{hop.amount_oz} oz {hop.hop.name}"))
    for adj in boil_adj:
        mins = adj.time_value if adj.time_value is not None else 0
        boil_timeline.append((mins, _fmt_adjunct(adj)))
    boil_timeline.sort(key=lambda x: -x[0])

    # Start-of-boil step
    first_hop = boil_hops[0] if boil_hops else None
    start_adj_at_top = [a for a in boil_adj if a.time_value is None or a.time_value >= recipe.boil_time]
    start_extras = ", ".join(_fmt_adjunct(a) for a in start_adj_at_top)

    if first_hop:
        start_text = f"Start {recipe.boil_time}-minute boil. Add {first_hop.amount_oz} oz {first_hop.hop.name} (bittering)"
        if start_extras:
            start_text += f"; also add {start_extras}"
        steps.append({
            "text": start_text,
            "timer": recipe.boil_time * 60,
            "type": "timer",
            "equipment": ["Digital scale", "Hop bag (optional)"],
        })
    else:
        start_text = f"Start {recipe.boil_time}-minute boil"
        if start_extras:
            start_text += f". Add {start_extras}"
        steps.append({
            "text": start_text,
            "timer": recipe.boil_time * 60,
            "type": "timer",
            "equipment": ["Brew kettle"],
        })

    # Mid-boil alerts (hops after first, plus boil adjuncts with time_value < boil_time)
    for mins_left, desc in boil_timeline:
        if mins_left >= recipe.boil_time:
            continue  # already covered at start
        steps.append({
            "text": f"At {mins_left} min remaining: add {desc}",
            "timer": None,
            "type": "alert",
            "alert_at": (recipe.boil_time - mins_left) * 60,
            "equipment": ["Digital scale"],
        })

    if flameout_hops or flameout_adj:
        parts = [f"{rh.amount_oz} oz {rh.hop.name}" for rh in flameout_hops]
        parts += [_fmt_adjunct(a) for a in flameout_adj]
        hop_list = ", ".join(parts)
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
    pitch_text = f"Transfer to fermenter, pitch {yeast_name}. Seal with airlock."
    primary_day_zero = [a for a in primary_adj if a.time_value in (None, 0)]
    if primary_day_zero:
        extras = ", ".join(_fmt_adjunct(a) for a in primary_day_zero)
        pitch_text += f" Also add: {extras}."
    steps.append({
        "text": pitch_text,
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

    # Later primary additions (day > 0)
    for adj in [a for a in primary_adj if a.time_value not in (None, 0)]:
        steps.append({
            "text": f"Primary day {adj.time_value}: add {_fmt_adjunct(adj)}" + (f" — {adj.notes}" if adj.notes else ""),
            "timer": None,
            "type": "note",
            "equipment": ["Sanitized addition vessel or bag"],
        })

    if dryhop_hops:
        hop_list = ", ".join(f"{rh.amount_oz} oz {rh.hop.name}" for rh in dryhop_hops)
        steps.append({
            "text": f"Dry hop (add after 3-5 days): {hop_list}",
            "timer": None,
            "type": "note",
            "equipment": ["Digital scale", "Sanitized hop bag or loose addition"],
        })

    for adj in secondary_adj:
        when = f"day {adj.time_value}" if adj.time_value is not None else "at transfer"
        text = f"Secondary {when}: add {_fmt_adjunct(adj)}"
        if adj.notes:
            text += f" — {adj.notes}"
        steps.append({
            "text": text,
            "timer": None,
            "type": "note",
            "equipment": ["Sanitized addition vessel or bag"],
        })

    for adj in bottling_adj:
        text = f"At bottling: add {_fmt_adjunct(adj)}"
        if adj.notes:
            text += f" — {adj.notes}"
        steps.append({
            "text": text,
            "timer": None,
            "type": "note",
            "equipment": ["Bottling bucket", "Sanitized stir spoon"],
        })

    return steps
