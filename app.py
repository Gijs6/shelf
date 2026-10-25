from flask import Flask, render_template

import os

from dotenv import load_dotenv

from migrations import run_migrations
from models import (
    STICKY_COLOURS,
    TODO_STATES,
    Bookmark,
    Note,
    StickyNote,
    Todo,
    db,
)
from routes import register_routes
from utils.auth import init_auth
from utils.errors import register_errors
from utils.filters import register_filters
from utils.headers import register_headers
from utils.proxy import TrustedProxyFix
from utils.session import SESSION_LIFETIME
from utils.toasts import register_toasts
from utils.version import register_version

load_dotenv(override=True)

app = Flask(__name__)
app.jinja_env.autoescape = True
app.wsgi_app = TrustedProxyFix(
    app.wsgi_app, os.getenv("TRUSTED_PROXIES", "router").split(",")
)

app.secret_key = os.getenv("SECRET_KEY", os.urandom(100).hex())
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_URI", "sqlite:///shelf.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["PERMANENT_SESSION_LIFETIME"] = SESSION_LIFETIME
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = True

db.init_app(app)
init_auth(app, public={"todos.ical_feed"})
register_filters(app)
register_routes(app)
register_toasts(app)
register_version(app, "book")
register_errors(app, "book")
register_headers(app)

app.jinja_env.globals["TODO_STATES"] = TODO_STATES
app.jinja_env.globals["STICKY_COLOURS"] = STICKY_COLOURS

os.makedirs(app.instance_path, exist_ok=True)

with app.app_context():
    db.create_all()
    run_migrations()


@app.get("/")
def index():
    upcoming_todos = (
        Todo.query.filter(
            ~Todo.deleted,
            ~Todo.archived,
            Todo.deadline.isnot(None),
            Todo.state.notin_(["shelved", "done", "cancelled"]),
        )
        .order_by(Todo.overdue.desc(), Todo.deadline.asc())
        .limit(5)
        .all()
    )

    recent_notes = (
        Note.query.filter(~Note.deleted, ~Note.archived)
        .order_by(Note.updated_at.desc())
        .limit(5)
        .all()
    )

    recent_bookmarks = (
        Bookmark.query.filter(~Bookmark.deleted)
        .order_by(Bookmark.created_at.desc())
        .limit(5)
        .all()
    )

    sticky_notes = (
        StickyNote.query.filter(~StickyNote.deleted)
        .order_by(StickyNote.pinned.desc(), StickyNote.created_at.desc())
        .limit(6)
        .all()
    )

    return render_template(
        "dashboard.jinja",
        recent_notes=recent_notes,
        recent_bookmarks=recent_bookmarks,
        sticky_notes=sticky_notes,
        upcoming_todos=upcoming_todos,
    )


@app.errorhandler(403)
def forbidden(e):
    return render_template(
        "error.jinja",
        code=403,
        title="Forbidden",
        description="You don't have permission to view this page.",
    ), 403


@app.errorhandler(404)
def not_found(e):
    return render_template(
        "error.jinja",
        code=404,
        title="Not found",
        description="The page you're looking for doesn't exist.",
    ), 404


@app.errorhandler(500)
def server_error(e):
    return render_template(
        "error.jinja",
        code=500,
        title="Server error",
        description="Something went wrong on our end. Try again later.",
    ), 500


if __name__ == "__main__":
    app.config["SESSION_COOKIE_SECURE"] = False
    app.run(host="0.0.0.0", port=4000, debug=True)
