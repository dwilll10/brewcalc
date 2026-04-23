import json

from flask import Blueprint, render_template, request, redirect, url_for, jsonify

from ..extensions import db
from ..models import (
    Recipe, RecipeFermentable, RecipeHop, RecipeAdjunct,
    Fermentable, Hop, Yeast, Style,
)
from ..calc import calc_og, calc_fg, calc_ibu, calc_srm, calc_abv

bp = Blueprint("recipes", __name__)


def _build_calc_inputs(recipe):
    """Build calculation input dicts from a recipe's relationships."""
    fermentables = []
    for rf in recipe.fermentables:
        fermentables.append({
            "amount_oz": rf.amount_oz,
            "ppg": rf.fermentable.ppg,
            "srm": rf.fermentable.srm,
            "type": rf.fermentable.type,
        })

    hop_additions = []
    for rh in recipe.hops:
        hop_additions.append({
            "amount_oz": rh.amount_oz,
            "alpha_acid": rh.hop.alpha_acid,
            "boil_time_min": rh.boil_time_min,
        })

    attenuation = recipe.yeast.attenuation if recipe.yeast else 0.75
    return fermentables, hop_additions, attenuation


def _recalculate(recipe):
    """Recalculate and store OG, FG, IBU, SRM, ABV on a recipe."""
    fermentables, hop_additions, attenuation = _build_calc_inputs(recipe)
    recipe.og = calc_og(fermentables, recipe.batch_size, recipe.efficiency)
    recipe.fg = calc_fg(recipe.og, attenuation)
    recipe.ibu = calc_ibu(hop_additions, recipe.og, recipe.batch_size)
    recipe.srm = calc_srm(fermentables, recipe.batch_size)
    recipe.abv = calc_abv(recipe.og, recipe.fg)


@bp.route("/")
def index():
    recipes = Recipe.query.order_by(Recipe.updated_at.desc()).all()
    return render_template("recipes/list.html", recipes=recipes)


@bp.route("/recipes/new", methods=["GET", "POST"])
def new_recipe():
    if request.method == "POST":
        recipe = Recipe(
            name=request.form["name"],
            style_id=request.form.get("style_id") or None,
            batch_size=float(request.form.get("batch_size", 1.75)),
            boil_time=int(request.form.get("boil_time", 60)),
            efficiency=float(request.form.get("efficiency", 1.0)),
            yeast_id=request.form.get("yeast_id") or None,
            notes=request.form.get("notes", ""),
            ferm_profile=request.form.get("ferm_profile", "[]"),
        )
        db.session.add(recipe)
        db.session.commit()
        return redirect(url_for("recipes.builder", recipe_id=recipe.id))

    styles = Style.query.order_by(Style.name).all()
    yeasts = Yeast.query.order_by(Yeast.name).all()
    return render_template("recipes/new.html", styles=styles, yeasts=yeasts)


@bp.route("/recipes/<int:recipe_id>")
def detail(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    style = recipe.style
    return render_template("recipes/detail.html", recipe=recipe, style=style)


@bp.route("/recipes/<int:recipe_id>/builder", methods=["GET"])
def builder(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    fermentables = Fermentable.query.order_by(Fermentable.name).all()
    hops = Hop.query.order_by(Hop.name).all()
    yeasts = Yeast.query.order_by(Yeast.name).all()
    styles = Style.query.order_by(Style.name).all()
    return render_template(
        "recipes/builder.html",
        recipe=recipe,
        fermentables=fermentables,
        hops=hops,
        yeasts=yeasts,
        styles=styles,
    )


@bp.route("/recipes/<int:recipe_id>/delete", methods=["POST"])
def delete_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    db.session.delete(recipe)
    db.session.commit()
    return redirect(url_for("recipes.index"))


# --- AJAX API endpoints for the recipe builder ---

@bp.route("/api/recipes/<int:recipe_id>/update", methods=["POST"])
def api_update_recipe(recipe_id):
    """Update recipe metadata (name, style, yeast, batch size, etc.)."""
    recipe = Recipe.query.get_or_404(recipe_id)
    data = request.get_json()

    if "name" in data:
        recipe.name = data["name"]
    if "style_id" in data:
        recipe.style_id = data["style_id"] or None
    if "yeast_id" in data:
        recipe.yeast_id = data["yeast_id"] or None
    if "batch_size" in data:
        recipe.batch_size = float(data["batch_size"])
    if "boil_time" in data:
        recipe.boil_time = int(data["boil_time"])
    if "efficiency" in data:
        recipe.efficiency = float(data["efficiency"])
    if "notes" in data:
        recipe.notes = data["notes"]
    if "ferm_profile" in data:
        recipe.ferm_profile = json.dumps(data["ferm_profile"])

    _recalculate(recipe)
    db.session.commit()
    return _recipe_stats_json(recipe)


@bp.route("/api/recipes/<int:recipe_id>/fermentable", methods=["POST"])
def api_add_fermentable(recipe_id):
    """Add a fermentable to the recipe."""
    recipe = Recipe.query.get_or_404(recipe_id)
    data = request.get_json()

    rf = RecipeFermentable(
        recipe_id=recipe.id,
        fermentable_id=int(data["fermentable_id"]),
        amount_oz=float(data.get("amount_oz", 16)),
        use=data.get("use", "boil"),
    )
    db.session.add(rf)
    _recalculate(recipe)
    db.session.commit()
    return _recipe_stats_json(recipe)


@bp.route("/api/recipes/<int:recipe_id>/fermentable/<int:rf_id>", methods=["PUT"])
def api_update_fermentable(recipe_id, rf_id):
    """Update a fermentable addition."""
    recipe = Recipe.query.get_or_404(recipe_id)
    rf = RecipeFermentable.query.get_or_404(rf_id)
    data = request.get_json()

    if "amount_oz" in data:
        rf.amount_oz = float(data["amount_oz"])
    if "use" in data:
        rf.use = data["use"]

    _recalculate(recipe)
    db.session.commit()
    return _recipe_stats_json(recipe)


@bp.route("/api/recipes/<int:recipe_id>/fermentable/<int:rf_id>", methods=["DELETE"])
def api_delete_fermentable(recipe_id, rf_id):
    """Remove a fermentable from the recipe."""
    recipe = Recipe.query.get_or_404(recipe_id)
    rf = RecipeFermentable.query.get_or_404(rf_id)
    db.session.delete(rf)
    _recalculate(recipe)
    db.session.commit()
    return _recipe_stats_json(recipe)


@bp.route("/api/recipes/<int:recipe_id>/hop", methods=["POST"])
def api_add_hop(recipe_id):
    """Add a hop addition to the recipe."""
    recipe = Recipe.query.get_or_404(recipe_id)
    data = request.get_json()

    rh = RecipeHop(
        recipe_id=recipe.id,
        hop_id=int(data["hop_id"]),
        amount_oz=float(data.get("amount_oz", 0.5)),
        boil_time_min=int(data.get("boil_time_min", 60)),
        use=data.get("use", "boil"),
    )
    db.session.add(rh)
    _recalculate(recipe)
    db.session.commit()
    return _recipe_stats_json(recipe)


@bp.route("/api/recipes/<int:recipe_id>/hop/<int:rh_id>", methods=["PUT"])
def api_update_hop(recipe_id, rh_id):
    """Update a hop addition."""
    recipe = Recipe.query.get_or_404(recipe_id)
    rh = RecipeHop.query.get_or_404(rh_id)
    data = request.get_json()

    if "amount_oz" in data:
        rh.amount_oz = float(data["amount_oz"])
    if "boil_time_min" in data:
        rh.boil_time_min = int(data["boil_time_min"])
    if "use" in data:
        rh.use = data["use"]

    _recalculate(recipe)
    db.session.commit()
    return _recipe_stats_json(recipe)


@bp.route("/api/recipes/<int:recipe_id>/hop/<int:rh_id>", methods=["DELETE"])
def api_delete_hop(recipe_id, rh_id):
    """Remove a hop addition from the recipe."""
    recipe = Recipe.query.get_or_404(recipe_id)
    rh = RecipeHop.query.get_or_404(rh_id)
    db.session.delete(rh)
    _recalculate(recipe)
    db.session.commit()
    return _recipe_stats_json(recipe)


@bp.route("/api/recipes/<int:recipe_id>/adjunct", methods=["POST"])
def api_add_adjunct(recipe_id):
    """Add an adjunct to the recipe."""
    recipe = Recipe.query.get_or_404(recipe_id)
    data = request.get_json()

    adj = RecipeAdjunct(
        recipe_id=recipe.id,
        name=data["name"],
        amount=data.get("amount", ""),
        add_time=data.get("add_time", ""),
        notes=data.get("notes", ""),
    )
    db.session.add(adj)
    db.session.commit()
    return _recipe_stats_json(recipe)


@bp.route("/api/recipes/<int:recipe_id>/adjunct/<int:adj_id>", methods=["DELETE"])
def api_delete_adjunct(recipe_id, adj_id):
    """Remove an adjunct from the recipe."""
    recipe = Recipe.query.get_or_404(recipe_id)
    adj = RecipeAdjunct.query.get_or_404(adj_id)
    db.session.delete(adj)
    db.session.commit()
    return _recipe_stats_json(recipe)


@bp.route("/api/recipes/<int:recipe_id>/calculate", methods=["GET"])
def api_calculate(recipe_id):
    """Recalculate and return recipe stats."""
    recipe = Recipe.query.get_or_404(recipe_id)
    _recalculate(recipe)
    db.session.commit()
    return _recipe_stats_json(recipe)


@bp.route("/api/recipes/<int:recipe_id>/scale", methods=["POST"])
def api_scale_recipe(recipe_id):
    """Scale all ingredient amounts to a new batch size.

    JSON body:
        new_batch_size: float (gallons)
    """
    recipe = Recipe.query.get_or_404(recipe_id)
    data = request.get_json()
    new_size = float(data["new_batch_size"])

    if new_size <= 0 or recipe.batch_size <= 0:
        return jsonify({"error": "Invalid batch size"}), 400

    ratio = new_size / recipe.batch_size

    for rf in recipe.fermentables:
        rf.amount_oz = round(rf.amount_oz * ratio, 2)

    for rh in recipe.hops:
        rh.amount_oz = round(rh.amount_oz * ratio, 2)

    recipe.batch_size = new_size
    _recalculate(recipe)
    db.session.commit()
    return _recipe_stats_json(recipe)


@bp.route("/api/recipes/<int:recipe_id>/ferm_profile", methods=["GET"])
def api_get_ferm_profile(recipe_id):
    """Get the fermentation profile for a recipe."""
    recipe = Recipe.query.get_or_404(recipe_id)
    profile = []
    if recipe.ferm_profile:
        try:
            profile = json.loads(recipe.ferm_profile)
        except json.JSONDecodeError:
            pass
    return jsonify({"profile": profile})


@bp.route("/api/recipes/<int:recipe_id>/ferm_profile", methods=["PUT"])
def api_update_ferm_profile(recipe_id):
    """Update the fermentation profile for a recipe.

    JSON body:
        profile: list of {hours: float, temp_f: float} waypoints
    """
    recipe = Recipe.query.get_or_404(recipe_id)
    data = request.get_json()
    profile = data.get("profile", [])
    # Sort by hours and validate
    profile = sorted(profile, key=lambda w: w.get("hours", 0))
    recipe.ferm_profile = json.dumps(profile)
    db.session.commit()
    return jsonify({"profile": profile})


def _recipe_stats_json(recipe):
    """Return recipe stats + ingredient lists as JSON."""
    style = recipe.style
    style_data = None
    if style:
        style_data = {
            "name": style.name,
            "og_low": style.og_low, "og_high": style.og_high,
            "fg_low": style.fg_low, "fg_high": style.fg_high,
            "ibu_low": style.ibu_low, "ibu_high": style.ibu_high,
            "srm_low": style.srm_low, "srm_high": style.srm_high,
            "abv_low": style.abv_low, "abv_high": style.abv_high,
        }

    return jsonify({
        "og": round(recipe.og or 1.0, 3),
        "fg": round(recipe.fg or 1.0, 3),
        "ibu": round(recipe.ibu or 0, 1),
        "srm": round(recipe.srm or 0, 1),
        "abv": round(recipe.abv or 0, 2),
        "style": style_data,
        "fermentables": [
            {
                "id": rf.id,
                "name": rf.fermentable.name,
                "amount_oz": rf.amount_oz,
                "use": rf.use,
            }
            for rf in recipe.fermentables
        ],
        "hops": [
            {
                "id": rh.id,
                "name": rh.hop.name,
                "amount_oz": rh.amount_oz,
                "boil_time_min": rh.boil_time_min,
                "use": rh.use,
            }
            for rh in recipe.hops
        ],
        "adjuncts": [
            {
                "id": adj.id,
                "name": adj.name,
                "amount": adj.amount,
                "add_time": adj.add_time,
            }
            for adj in recipe.adjuncts
        ],
    })
