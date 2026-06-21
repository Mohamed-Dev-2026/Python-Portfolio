# =============================================================================
# app.py — Flask Application: Routes, Error Handlers, and App Factory
#
# Architecture overview
# ─────────────────────
# ┌─────────────────────────────────────────────────────────────────────┐
# │  app.py  (this file)                                                │
# │    create_app()  ← application factory                             │
# │    ├── configure Flask + SQLite                                     │
# │    ├── initialise SQLAlchemy (models.py)                            │
# │    ├── register Blueprints (events_bp, registrations_bp)           │
# │    └── register global error handlers                              │
# │                                                                     │
# │  routes/                                                            │
# │    events.py        → GET  /events                                 │
# │                     → POST /events                                 │
# │    registrations.py → POST /events/<id>/register                  │
# │                     → GET  /events/<id>/registrations              │
# └─────────────────────────────────────────────────────────────────────┘
#
# Run:
#   pip install -r requirements.txt
#   python app.py
# =============================================================================

import os
from flask import Flask, jsonify, render_template
from models import db

# ---------------------------------------------------------------------------
# Blueprints — imported here so create_app() can register them.
# Blueprints let you split routes across multiple files without circular
# imports. Each Blueprint is essentially a mini Flask app that gets
# "mounted" onto the main app.
# ---------------------------------------------------------------------------
from routes.events import events_bp
from routes.registrations import registrations_bp


def create_app(test_config: dict | None = None) -> Flask:
    """
    Application factory.

    Using a factory instead of a module-level `app = Flask(__name__)` means:
      - You can create multiple isolated app instances (great for testing).
      - Configuration can be injected at creation time.

    Args:
        test_config: Optional dict of config overrides (used in unit tests).

    Returns:
        A fully configured Flask application instance.
    """
    # static_url_path tells Flask what URL prefix to use when serving files
    # from the /static folder. The Replit reverse proxy routes /events-api/*
    # to this Flask process, so static assets must be under that same prefix.
    app = Flask(__name__, static_url_path="/events-api/static")

    # -----------------------------------------------------------------------
    # Configuration
    # -----------------------------------------------------------------------
    # SQLALCHEMY_DATABASE_URI — SQLite stores everything in a single file next
    # to app.py. "sqlite:///events.db" means a relative path inside the
    # instance folder. Use an in-memory DB when running tests.
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///events.db")

    # Suppress a noisy SQLAlchemy warning about modification tracking that we
    # don't use — we rely on explicit commits instead.
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # A secret key is required by Flask for session signing. Load it from an
    # environment variable in production so it is never hard-coded.
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")

    # Override any setting with the test config if provided.
    if test_config:
        app.config.update(test_config)

    # -----------------------------------------------------------------------
    # Database initialisation
    # -----------------------------------------------------------------------
    # Bind the SQLAlchemy instance (created in models.py) to this app.
    # `init_app` is the standard pattern when `db` lives outside the factory.
    db.init_app(app)

    # Create all tables that don't yet exist. This is safe to call on every
    # startup — it's a no-op for tables that already exist.
    with app.app_context():
        db.create_all()

    # -----------------------------------------------------------------------
    # Blueprint registration
    # -----------------------------------------------------------------------
    # url_prefix means every route inside the blueprint is prefixed.
    # e.g. events_bp route "/events" becomes GET /api/events
    # Routes are served under /events-api so the Replit reverse proxy
    # can route /events-api/* → this Flask process on port 5000.
    app.register_blueprint(events_bp, url_prefix="/events-api")
    app.register_blueprint(registrations_bp, url_prefix="/events-api")

    # -----------------------------------------------------------------------
    # Frontend route
    # -----------------------------------------------------------------------
    # Serve the HTML/CSS/JS frontend at the root of the /events-api path.
    # Flask's built-in static file serving handles /events-api/static/* files.
    @app.route("/events-api/")
    @app.route("/events-api")
    def frontend():
        """Serve the single-page HTML frontend."""
        return render_template("index.html")

    # -----------------------------------------------------------------------
    # Global error handlers
    # -----------------------------------------------------------------------
    # These catch errors that bubble up from *any* route in the app.

    @app.errorhandler(404)
    def not_found(error):
        """Return a JSON 404 instead of Flask's default HTML error page."""
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        """Return a JSON 405 when the HTTP method is not supported."""
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def internal_error(error):
        """
        Catch-all for unhandled server errors.
        Roll back any open database transaction so the session isn't left in
        a broken state for the next request.
        """
        db.session.rollback()
        return jsonify({"error": "An unexpected server error occurred"}), 500

    return app


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
# `__name__ == "__main__"` is True only when you run `python app.py`
# directly. It is False when Flask or a WSGI server imports this module.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    flask_app = create_app()
    # Read PORT from the environment so Replit can assign it automatically.
    port = int(os.environ.get("PORT", 5000))
    flask_app.run(host="0.0.0.0", debug=True, port=port)
