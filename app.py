"""
Cloud Notes - a small Flask web app used for the Codomax Digital Solutions
Module 3 internship (Cloud Services & Web App Deployment).

Flow:  Application Code -> Cloud Compute (Render) -> Database -> Networking -> Live Web App

This single file contains:
  1. Configuration read from environment variables (no hard-coded secrets)
  2. Logging setup (stdout, so the cloud platform can collect it)
  3. The SQLAlchemy "Note" model (the database table)
  4. The three routes: "/" , "/health" , "/api/notes"

Run locally with:      python app.py
Run in the cloud with: gunicorn app:app
"""

import os
import re
import sys
import logging
from datetime import datetime, timezone

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix

# ---------------------------------------------------------------------------
# 1. CONFIGURATION - every value comes from an environment variable
# ---------------------------------------------------------------------------

# Local fallback only. In the cloud, DATABASE_URL is set to a real PostgreSQL URL.
DEFAULT_DATABASE_URL = "sqlite:///cloud_notes.db"


def normalize_database_url(url):
    """Convert postgres:// into postgresql:// because SQLAlchemy needs the long form."""
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


# SECRET_KEY has no fixed default on purpose. Locally we generate a random
# temporary key so the app still runs; nothing secret is ever stored in the code.
secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    secret_key = "dev-only-random-key-%s" % os.urandom(16).hex()

app = Flask(__name__)
app.config.update(
    SECRET_KEY=secret_key,
    SQLALCHEMY_DATABASE_URI=normalize_database_url(
        os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    ),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    # The task asks for the latest 50 notes to be listed on the page
    MAX_NOTES_DISPLAYED=50,
)

# The cloud platform puts one proxy in front of the app. Trusting one hop lets
# url_for() build correct https:// links without trusting the whole internet.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Application settings from the environment
APP_NAME = os.getenv("APP_NAME", "Cloud Notes")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "500"))
NOTES_PER_PAGE = app.config["MAX_NOTES_DISPLAYED"]
MAX_AUTHOR_LENGTH = 80

# ---------------------------------------------------------------------------
# 2. LOGGING - write to stdout so the cloud log dashboard can read it
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("cloud_notes")

db = SQLAlchemy(app)


# ---------------------------------------------------------------------------
# 3. DATABASE MODEL
# ---------------------------------------------------------------------------


class Note(db.Model):
    """One note saved by a user."""

    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(MAX_AUTHOR_LENGTH), nullable=False)
    message = db.Column(db.String(MAX_MESSAGE_LENGTH), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        """Convert this note into a plain dictionary for the JSON API."""
        created = self.created_at
        if created is not None and created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        return {
            "id": self.id,
            "author": self.author,
            "message": self.message,
            "created_at": created.isoformat() if created else None,
        }

    def __repr__(self):
        return "<Note %s by %s>" % (self.id, self.author)


# ---------------------------------------------------------------------------
# 4. HELPER FUNCTIONS
# ---------------------------------------------------------------------------


def mask_database_url(url=None):
    """Hide the password before a database URL is written to the logs."""
    raw = url or app.config["SQLALCHEMY_DATABASE_URI"]
    if "@" not in raw or "://" not in raw:
        return raw  # a local SQLite file - there is no password to hide
    scheme, rest = raw.split("://", 1)
    credentials, host = rest.split("@", 1)
    user = credentials.split(":", 1)[0]
    return "%s://%s:****@%s" % (scheme, user, host)


def create_tables():
    """Create the notes table if it does not exist yet (safe on every start)."""
    with app.app_context():
        db.create_all()


def clean(value):
    """Strip HTML tags and collapse repeated spaces from user input."""
    if not value:
        return ""
    text = re.sub(r"<[^>]*>", "", value)
    return re.sub(r"\s+", " ", text).strip()


def validate(author, message):
    """Return (clean_author, clean_message, error_message)."""
    author = clean(author)
    message = clean(message)

    if not author:
        return author, message, "Please enter your name."
    if not message:
        return author, message, "Please enter a note."
    if len(author) > MAX_AUTHOR_LENGTH:
        return "", "", "Your name is too long (maximum %d characters)." % MAX_AUTHOR_LENGTH
    if len(message) > MAX_MESSAGE_LENGTH:
        return "", "", "Your note is too long (maximum %d characters)." % MAX_MESSAGE_LENGTH
    return author, message, None


# ---------------------------------------------------------------------------
# 5. ROUTES
# ---------------------------------------------------------------------------


@app.route("/", methods=["GET", "POST"])
def index():
    """Show the add-note form and the latest notes."""
    error = None
    author_value = ""
    message_value = ""

    if request.method == "POST":
        author_value = request.form.get("author", "")
        message_value = request.form.get("message", "")
        author, message, error = validate(author_value, message_value)

        if error:
            logger.warning("Rejected note from form: %s", error)
        else:
            note = Note(author=author, message=message)
            db.session.add(note)
            db.session.commit()
            logger.info("Note added by %s (id=%s)", author, note.id)
            return redirect(url_for("index"))

    try:
        notes = (
            Note.query.order_by(Note.created_at.desc(), Note.id.desc())
            .limit(NOTES_PER_PAGE)
            .all()
        )
    except Exception as exc:  # noqa: BLE001 - show a friendly page, log the detail
        logger.error("Could not load notes: %s", exc)
        notes = []
        error = "The note list is temporarily unavailable. Please try again."

    return render_template(
        "index.html",
        app_name=APP_NAME,
        notes=notes,
        error=error,
        author_value=author_value,
        message_value=message_value,
        max_length=MAX_MESSAGE_LENGTH,
    )


@app.route("/health")
def health():
    """Health check - also used by the cloud platform to monitor the service."""
    db_ok = False
    try:
        db.session.execute(db.text("SELECT 1"))
        db_ok = True
        details = "database connection OK"
    except Exception as exc:  # noqa: BLE001 - logged, never shown to the visitor
        logger.error("Health check database error: %s", exc)
        details = "database connection FAILED"

    payload = {
        "status": "healthy" if db_ok else "unhealthy",
        "app": APP_NAME,
        "database": "connected" if db_ok else "error",
        "details": details,
        "notes_displayed": NOTES_PER_PAGE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("Health check -> %s (%s)", payload["status"], details)
    return jsonify(payload), (200 if db_ok else 503)


@app.route("/api/notes")
def api_notes():
    """Return the latest notes as JSON."""
    try:
        limit = int(request.args.get("limit", NOTES_PER_PAGE))
    except (TypeError, ValueError):
        limit = NOTES_PER_PAGE
    limit = max(1, min(limit, NOTES_PER_PAGE))

    try:
        notes = (
            Note.query.order_by(Note.created_at.desc(), Note.id.desc())
            .limit(limit)
            .all()
        )
    except Exception as exc:  # noqa: BLE001 - report the failure as JSON
        logger.error("API request failed: %s", exc)
        return jsonify({"error": "database unavailable", "count": 0, "notes": []}), 503

    logger.info("API request returned %d note(s)", len(notes))
    return jsonify(
        {
            "count": len(notes),
            "app": APP_NAME,
            "notes": [n.to_dict() for n in notes],
        }
    )


def wants_json():
    return request.path.startswith("/api") or request.path == "/health"


@app.errorhandler(404)
def not_found(_error):
    logger.warning("404 - page not found: %s", request.path)
    if wants_json():
        return jsonify({"error": "not found", "path": request.path}), 404
    return render_template("index.html", app_name=APP_NAME, notes=[], error=None,
                           author_value="", message_value="",
                           max_length=MAX_MESSAGE_LENGTH), 404


@app.errorhandler(500)
def server_error(_error):
    logger.error("500 - unhandled server error on %s", request.path)
    if wants_json():
        return jsonify({"error": "internal server error"}), 500
    return render_template("index.html", app_name=APP_NAME, notes=[], error=None,
                           author_value="", message_value="",
                           max_length=MAX_MESSAGE_LENGTH), 500


# ---------------------------------------------------------------------------
# 6. START THE APP
# ---------------------------------------------------------------------------

# Create the table at import time so gunicorn workers can use it immediately.
create_tables()

if not os.getenv("SECRET_KEY"):
    logger.warning("SECRET_KEY is not set - using a temporary development key. "
                   "Set SECRET_KEY in the cloud dashboard before going live.")

logger.info("%s starting | LOG_LEVEL=%s | DB=%s",
            APP_NAME, LOG_LEVEL, mask_database_url())

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)