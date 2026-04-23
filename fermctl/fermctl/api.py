"""Flask REST API for the fermentation controller.

Exposes endpoints to start/stop fermentation runs, get status,
retrieve temperature readings, and push profile updates.
Runs on port 5001 by default to avoid conflicts with the recipe app.
"""

import json
import logging

from flask import Flask, request, jsonify, render_template

from . import config
from .controller import FermentationController

logger = logging.getLogger("fermctl.api")

app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static",
)

# Controller instance — shared with the control loop
controller = FermentationController()


# --- Dashboard ---

@app.route("/")
def dashboard():
    """Serve the web dashboard."""
    return render_template("dashboard.html")


# --- REST API ---

@app.route("/api/status")
def api_status():
    """Get current controller status."""
    return jsonify(controller.get_status())


@app.route("/api/runs", methods=["GET"])
def api_list_runs():
    """List recent fermentation runs."""
    runs = controller.logger.get_runs()
    return jsonify(runs)


@app.route("/api/runs", methods=["POST"])
def api_start_run():
    """Start a new fermentation run.

    JSON body:
        recipe_id: (optional) int — recipe ID from brewcalc
        recipe_name: (optional) string
        profile: list of {hours, temp_f} waypoints
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    profile_json = json.dumps(data.get("profile", []))
    controller.start_run(
        recipe_id=data.get("recipe_id"),
        recipe_name=data.get("recipe_name", ""),
        profile_json=profile_json,
    )
    return jsonify(controller.get_status()), 201


@app.route("/api/runs/<int:run_id>")
def api_get_run(run_id):
    """Get details for a specific run."""
    run = controller.logger.get_run(run_id)
    if not run:
        return jsonify({"error": "Run not found"}), 404
    return jsonify(run)


@app.route("/api/runs/<int:run_id>/stop", methods=["POST"])
def api_stop_run(run_id):
    """Stop the active fermentation run."""
    if controller.active_run_id != run_id:
        return jsonify({"error": "Run is not active"}), 400
    controller.stop_run()
    return jsonify({"status": "stopped", "run_id": run_id})


@app.route("/api/readings")
def api_readings():
    """Get temperature readings for a run.

    Query params:
        run_id: (required) int
        since: (optional) ISO timestamp — only return newer readings
    """
    run_id = request.args.get("run_id", type=int)
    if not run_id:
        # Default to active run
        if controller.active_run_id:
            run_id = controller.active_run_id
        else:
            return jsonify({"error": "run_id required"}), 400

    since = request.args.get("since")
    readings = controller.logger.get_readings(run_id, since=since)
    return jsonify(readings)


@app.route("/api/profile", methods=["GET"])
def api_get_profile():
    """Get the current active temperature profile."""
    return jsonify({
        "profile": controller.profile.waypoints,
        "active": controller.is_running,
    })


@app.route("/api/profile", methods=["PUT"])
def api_update_profile():
    """Update the active fermentation profile.

    JSON body:
        profile: list of {hours, temp_f} waypoints
    """
    data = request.get_json()
    if not data or "profile" not in data:
        return jsonify({"error": "profile required"}), 400

    controller.update_profile(json.dumps(data["profile"]))
    return jsonify({
        "profile": controller.profile.waypoints,
        "status": "updated",
    })


@app.route("/api/override", methods=["POST"])
def api_override():
    """Set or clear a manual temperature override.

    JSON body:
        temp_f: float — target temp, or null to clear override
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    temp = data.get("temp_f")
    controller.set_override(float(temp) if temp is not None else None)
    return jsonify(controller.get_status())
