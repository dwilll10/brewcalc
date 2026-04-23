"""Fermentation route — proxies requests to the Raspberry Pi controller.

This avoids CORS issues and keeps the Pi's API URL configured in one place.
The browser talks to the recipe app, which forwards to the Pi.
"""

import json
import logging

import requests
from flask import Blueprint, render_template, request, jsonify, current_app

from ..models import Recipe

bp = Blueprint("fermentation", __name__, url_prefix="/fermentation")
logger = logging.getLogger(__name__)


def _pi_url(path=""):
    """Build the full URL to the Pi controller API."""
    base = current_app.config.get("FERMCTL_API_URL", "http://raspberrypi.local:5001")
    return f"{base}{path}"


def _pi_get(path, params=None):
    """GET request to Pi controller with error handling."""
    try:
        resp = requests.get(_pi_url(path), params=params, timeout=5)
        return resp.json(), resp.status_code
    except requests.ConnectionError:
        return {"error": "Cannot connect to fermentation controller", "offline": True}, 503
    except requests.Timeout:
        return {"error": "Fermentation controller timed out"}, 504


def _pi_post(path, data=None):
    """POST request to Pi controller with error handling."""
    try:
        resp = requests.post(_pi_url(path), json=data, timeout=5)
        return resp.json(), resp.status_code
    except requests.ConnectionError:
        return {"error": "Cannot connect to fermentation controller", "offline": True}, 503
    except requests.Timeout:
        return {"error": "Fermentation controller timed out"}, 504


def _pi_put(path, data=None):
    """PUT request to Pi controller with error handling."""
    try:
        resp = requests.put(_pi_url(path), json=data, timeout=5)
        return resp.json(), resp.status_code
    except requests.ConnectionError:
        return {"error": "Cannot connect to fermentation controller", "offline": True}, 503
    except requests.Timeout:
        return {"error": "Fermentation controller timed out"}, 504


# --- Pages ---

@bp.route("/recipe/<int:recipe_id>")
def dashboard(recipe_id):
    """Fermentation dashboard for a specific recipe."""
    recipe = Recipe.query.get_or_404(recipe_id)
    status, _ = _pi_get("/api/status")
    return render_template(
        "fermentation/dashboard.html",
        recipe=recipe,
        status=status,
    )


# --- Proxy API endpoints ---

@bp.route("/api/status")
def api_status():
    data, code = _pi_get("/api/status")
    return jsonify(data), code


@bp.route("/api/start", methods=["POST"])
def api_start():
    """Start a fermentation run for a recipe.

    JSON body: recipe_id (int)
    """
    req_data = request.get_json()
    recipe_id = req_data.get("recipe_id")
    recipe = Recipe.query.get_or_404(recipe_id)

    # Parse the fermentation profile from the recipe
    profile = []
    if recipe.ferm_profile:
        try:
            profile = json.loads(recipe.ferm_profile)
        except json.JSONDecodeError:
            pass

    # If no profile set, use yeast temp range midpoint
    if not profile and recipe.yeast:
        mid_temp = (recipe.yeast.temp_low + recipe.yeast.temp_high) / 2
        profile = [{"hours": 0, "temp_f": mid_temp}]

    data, code = _pi_post("/api/runs", {
        "recipe_id": recipe.id,
        "recipe_name": recipe.name,
        "profile": profile,
    })
    return jsonify(data), code


@bp.route("/api/stop", methods=["POST"])
def api_stop():
    req_data = request.get_json()
    run_id = req_data.get("run_id")
    if not run_id:
        return jsonify({"error": "run_id required"}), 400
    data, code = _pi_post(f"/api/runs/{run_id}/stop")
    return jsonify(data), code


@bp.route("/api/readings")
def api_readings():
    run_id = request.args.get("run_id")
    since = request.args.get("since")
    data, code = _pi_get("/api/readings", {"run_id": run_id, "since": since})
    return jsonify(data), code


@bp.route("/api/profile", methods=["PUT"])
def api_update_profile():
    data, code = _pi_put("/api/profile", request.get_json())
    return jsonify(data), code


@bp.route("/api/override", methods=["POST"])
def api_override():
    data, code = _pi_post("/api/override", request.get_json())
    return jsonify(data), code
