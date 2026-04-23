from flask import Blueprint, render_template
from ..models import Style

bp = Blueprint("styles", __name__, url_prefix="/styles")


@bp.route("/")
def list_styles():
    styles = Style.query.order_by(Style.category).all()
    return render_template("styles/list.html", styles=styles)
