# =============================================================================
# models.py — Database Models for the Event Registration System
#
# Uses Flask-SQLAlchemy (an ORM — Object Relational Mapper) so we interact
# with the SQLite database through Python classes instead of raw SQL.
# =============================================================================

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Create the SQLAlchemy instance here. It will be bound to the Flask app
# in app.py using the "application factory" pattern — db.init_app(app).
db = SQLAlchemy()


class Event(db.Model):
    """
    Represents a schedulable event.

    Columns:
        id          — Auto-incrementing primary key.
        name        — The event title (e.g. "Python Workshop").
        date        — When the event takes place (stored as a Python datetime).
        description — Optional free-text details about the event.
        created_at  — Timestamp set automatically when the row is inserted.
    """

    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # One-to-many relationship: an Event can have many Registrations.
    # `cascade="all, delete-orphan"` means if an Event is deleted,
    # all its Registrations are automatically deleted too.
    registrations = db.relationship(
        "Registration",
        backref="event",
        cascade="all, delete-orphan",
        lazy=True,
    )

    def to_dict(self):
        """Serialize the Event to a plain Python dict (for JSON responses)."""
        return {
            "id": self.id,
            "name": self.name,
            "date": self.date.isoformat(),
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "registration_count": len(self.registrations),
        }

    def __repr__(self):
        return f"<Event id={self.id} name='{self.name}'>"


class Registration(db.Model):
    """
    Represents a single user's registration for one event.

    Columns:
        id          — Auto-incrementing primary key.
        user_name   — The registrant's full name.
        user_email  — The registrant's email address.
        event_id    — Foreign key pointing to the Event being registered for.
        registered_at — Timestamp set automatically on insert.
    """

    __tablename__ = "registrations"

    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(150), nullable=False)
    user_email = db.Column(db.String(150), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Unique constraint: one email address may only register for a given
    # event once. The database enforces this at the storage level.
    __table_args__ = (
        db.UniqueConstraint("user_email", "event_id", name="uq_email_event"),
    )

    def to_dict(self):
        """Serialize the Registration to a plain Python dict."""
        return {
            "id": self.id,
            "user_name": self.user_name,
            "user_email": self.user_email,
            "event_id": self.event_id,
            "registered_at": self.registered_at.isoformat(),
        }

    def __repr__(self):
        return f"<Registration id={self.id} email='{self.user_email}' event_id={self.event_id}>"
