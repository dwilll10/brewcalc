from flask import Blueprint, render_template, request, redirect, url_for, flash

from ..extensions import db
from ..models import Fermentable, Hop, Yeast, Style

bp = Blueprint("admin", __name__, url_prefix="/admin")


# --- Fermentables ---

@bp.route("/fermentables")
def fermentables():
    items = Fermentable.query.order_by(Fermentable.name).all()
    return render_template("admin/fermentables.html", items=items)


@bp.route("/fermentables/add", methods=["POST"])
def add_fermentable():
    item = Fermentable(
        name=request.form["name"],
        type=request.form["type"],
        ppg=float(request.form["ppg"]),
        srm=float(request.form["srm"]),
        notes=request.form.get("notes", ""),
    )
    db.session.add(item)
    db.session.commit()
    flash(f"Added fermentable: {item.name}", "success")
    return redirect(url_for("admin.fermentables"))


@bp.route("/fermentables/<int:item_id>/edit", methods=["POST"])
def edit_fermentable(item_id):
    item = Fermentable.query.get_or_404(item_id)
    item.name = request.form["name"]
    item.type = request.form["type"]
    item.ppg = float(request.form["ppg"])
    item.srm = float(request.form["srm"])
    item.notes = request.form.get("notes", "")
    db.session.commit()
    flash(f"Updated: {item.name}", "success")
    return redirect(url_for("admin.fermentables"))


@bp.route("/fermentables/<int:item_id>/delete", methods=["POST"])
def delete_fermentable(item_id):
    item = Fermentable.query.get_or_404(item_id)
    name = item.name
    db.session.delete(item)
    db.session.commit()
    flash(f"Deleted: {name}", "success")
    return redirect(url_for("admin.fermentables"))


# --- Hops ---

@bp.route("/hops")
def hops():
    items = Hop.query.order_by(Hop.name).all()
    return render_template("admin/hops.html", items=items)


@bp.route("/hops/add", methods=["POST"])
def add_hop():
    item = Hop(
        name=request.form["name"],
        alpha_acid=float(request.form["alpha_acid"]),
        type=request.form["type"],
        notes=request.form.get("notes", ""),
    )
    db.session.add(item)
    db.session.commit()
    flash(f"Added hop: {item.name}", "success")
    return redirect(url_for("admin.hops"))


@bp.route("/hops/<int:item_id>/edit", methods=["POST"])
def edit_hop(item_id):
    item = Hop.query.get_or_404(item_id)
    item.name = request.form["name"]
    item.alpha_acid = float(request.form["alpha_acid"])
    item.type = request.form["type"]
    item.notes = request.form.get("notes", "")
    db.session.commit()
    flash(f"Updated: {item.name}", "success")
    return redirect(url_for("admin.hops"))


@bp.route("/hops/<int:item_id>/delete", methods=["POST"])
def delete_hop(item_id):
    item = Hop.query.get_or_404(item_id)
    name = item.name
    db.session.delete(item)
    db.session.commit()
    flash(f"Deleted: {name}", "success")
    return redirect(url_for("admin.hops"))


# --- Yeasts ---

@bp.route("/yeasts")
def yeasts():
    items = Yeast.query.order_by(Yeast.name).all()
    return render_template("admin/yeasts.html", items=items)


@bp.route("/yeasts/add", methods=["POST"])
def add_yeast():
    item = Yeast(
        name=request.form["name"],
        lab=request.form.get("lab", ""),
        code=request.form.get("code", ""),
        attenuation=float(request.form["attenuation"]),
        temp_low=float(request.form["temp_low"]),
        temp_high=float(request.form["temp_high"]),
        type=request.form["type"],
        notes=request.form.get("notes", ""),
    )
    db.session.add(item)
    db.session.commit()
    flash(f"Added yeast: {item.name}", "success")
    return redirect(url_for("admin.yeasts"))


@bp.route("/yeasts/<int:item_id>/edit", methods=["POST"])
def edit_yeast(item_id):
    item = Yeast.query.get_or_404(item_id)
    item.name = request.form["name"]
    item.lab = request.form.get("lab", "")
    item.code = request.form.get("code", "")
    item.attenuation = float(request.form["attenuation"])
    item.temp_low = float(request.form["temp_low"])
    item.temp_high = float(request.form["temp_high"])
    item.type = request.form["type"]
    item.notes = request.form.get("notes", "")
    db.session.commit()
    flash(f"Updated: {item.name}", "success")
    return redirect(url_for("admin.yeasts"))


@bp.route("/yeasts/<int:item_id>/delete", methods=["POST"])
def delete_yeast(item_id):
    item = Yeast.query.get_or_404(item_id)
    name = item.name
    db.session.delete(item)
    db.session.commit()
    flash(f"Deleted: {name}", "success")
    return redirect(url_for("admin.yeasts"))


# --- Styles ---

@bp.route("/styles")
def styles():
    items = Style.query.order_by(Style.category).all()
    return render_template("admin/styles.html", items=items)


@bp.route("/styles/add", methods=["POST"])
def add_style():
    item = Style(
        name=request.form["name"],
        category=request.form.get("category", ""),
        og_low=float(request.form["og_low"]),
        og_high=float(request.form["og_high"]),
        fg_low=float(request.form["fg_low"]),
        fg_high=float(request.form["fg_high"]),
        ibu_low=int(request.form["ibu_low"]),
        ibu_high=int(request.form["ibu_high"]),
        srm_low=float(request.form["srm_low"]),
        srm_high=float(request.form["srm_high"]),
        abv_low=float(request.form["abv_low"]),
        abv_high=float(request.form["abv_high"]),
        description=request.form.get("description", ""),
    )
    db.session.add(item)
    db.session.commit()
    flash(f"Added style: {item.name}", "success")
    return redirect(url_for("admin.styles"))


@bp.route("/styles/<int:item_id>/edit", methods=["POST"])
def edit_style(item_id):
    item = Style.query.get_or_404(item_id)
    item.name = request.form["name"]
    item.category = request.form.get("category", "")
    item.og_low = float(request.form["og_low"])
    item.og_high = float(request.form["og_high"])
    item.fg_low = float(request.form["fg_low"])
    item.fg_high = float(request.form["fg_high"])
    item.ibu_low = int(request.form["ibu_low"])
    item.ibu_high = int(request.form["ibu_high"])
    item.srm_low = float(request.form["srm_low"])
    item.srm_high = float(request.form["srm_high"])
    item.abv_low = float(request.form["abv_low"])
    item.abv_high = float(request.form["abv_high"])
    item.description = request.form.get("description", "")
    db.session.commit()
    flash(f"Updated: {item.name}", "success")
    return redirect(url_for("admin.styles"))


@bp.route("/styles/<int:item_id>/delete", methods=["POST"])
def delete_style(item_id):
    item = Style.query.get_or_404(item_id)
    name = item.name
    db.session.delete(item)
    db.session.commit()
    flash(f"Deleted: {name}", "success")
    return redirect(url_for("admin.styles"))
