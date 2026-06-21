# =============================================================================
# routes/events.py — Event Routes
#
# Endpoints
# ─────────
#   GET  /api/events          → List all events
#   POST /api/events          → Create a new event
# =============================================================================

from flask import Blueprint, request, jsonify
from models import db, Event
from datetime import datetime

# A Blueprint groups related routes. The first argument is the Blueprint's
# internal name — Flask uses it to generate url_for() names.
events_bp = Blueprint("events", __name__)


# ---------------------------------------------------------------------------
# GET /api/events
# ---------------------------------------------------------------------------
@events_bp.route("/events", methods=["GET"])
def list_events():
    """
    Return all events ordered by date (soonest first).

    Response 200:
        { "events": [ { id, name, date, description, ... }, ... ] }
    """
    # Query every row in the events table, sorted ascending by date.
    events = Event.query.order_by(Event.date.asc()).all()

    return jsonify({
        "events": [event.to_dict() for event in events]
    }), 200


# ---------------------------------------------------------------------------
# POST /api/events
# ---------------------------------------------------------------------------
@events_bp.route("/events", methods=["POST"])
def create_event():
    """
    Create a new event.

    Request body (JSON):
        {
            "name":        "Python Workshop",          (required)
            "date":        "2025-09-15T09:00:00",      (required, ISO 8601)
            "description": "A hands-on intro session"  (optional)
        }

    Response 201:
        { "message": "Event created", "event": { ... } }

    Errors:
        400 — Missing required fields or invalid date format.
    """
    data = request.get_json(silent=True)

    # `silent=True` returns None instead of raising if the body isn't JSON.
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    # ---- Validate required fields ----------------------------------------
    name = data.get("name", "").strip()
    date_str = data.get("date", "").strip()

    if not name:
        return jsonify({"error": "'name' is required"}), 400

    if not date_str:
        return jsonify({"error": "'date' is required (ISO 8601 format: YYYY-MM-DDTHH:MM:SS)"}), 400

    # ---- Parse the date string -------------------------------------------
    # We accept the ISO 8601 format that JavaScript / most HTTP clients send.
    try:
        event_date = datetime.fromisoformat(date_str)
    except ValueError:
        return jsonify({
            "error": "Invalid 'date' format. Use ISO 8601 (e.g. '2025-09-15T09:00:00')"
        }), 400

    # ---- Persist to the database -----------------------------------------
    new_event = Event(
        name=name,
        date=event_date,
        description=data.get("description"),  # Optional — None is fine
    )

    db.session.add(new_event)
    db.session.commit()

    return jsonify({
        "message": "Event created successfully",
        "event": new_event.to_dict()
    }), 201
