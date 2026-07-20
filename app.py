from flask import Flask, flash, redirect, render_template, request, session, url_for

import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from werkzeug.security import check_password_hash

from migrations import run_migrations
from models import TODO_STATES, Note, StickyNote, Todo, db, now
from routes import register_routes
from utils.filters import register_filters
from utils.session import SESSION_LIFETIME
from utils.version import get_version


load_dotenv(override=True)

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", os.urandom(100).hex())
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_URI", "sqlite:///shelf.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["PERMANENT_SESSION_LIFETIME"] = SESSION_LIFETIME

db.init_app(app)
register_filters(app)
register_routes(app)

app.jinja_env.globals["TODO_STATES"] = TODO_STATES
app.jinja_env.globals["APP_VERSION"] = get_version()

os.makedirs(app.instance_path, exist_ok=True)

with app.app_context():
    db.create_all()
    run_migrations()


def is_logged_in():
    last_login = session.get("last_login")
    if last_login is None or now() - last_login > SESSION_LIFETIME:
        session.clear()
        return False
    return True


@app.get("/")
def index():
    upcoming_todos = (
        Todo.query.filter(
            ~Todo.deleted,
            ~Todo.archived,
            Todo.deadline.isnot(None),
            Todo.state.notin_(["done", "cancelled"]),
        )
        .order_by(Todo.overdue.desc(), Todo.deadline.asc())
        .limit(5)
        .all()
    )

    recent_notes = (
        Note.query.filter(~Note.deleted).order_by(Note.updated_at.desc()).limit(5).all()
    )

    sticky_notes = (
        StickyNote.query.filter(
            ~StickyNote.deleted,
            StickyNote.pinned.is_(True) | ~StickyNote.expired,
        )
        .order_by(StickyNote.pinned.desc(), StickyNote.created_at.desc())
        .limit(6)
        .all()
    )

    return render_template(
        "dashboard.jinja",
        recent_notes=recent_notes,
        sticky_notes=sticky_notes,
        upcoming_todos=upcoming_todos,
    )


@app.get("/login", endpoint="login")
def login_get():
    if is_logged_in():
        return redirect(url_for("index"))
    return render_template("login.jinja")


@app.post("/login", endpoint="login_post")
def login_post():
    if is_logged_in():
        return redirect(url_for("index"), code=303)
    password = request.form.get("password", "")
    stored_hash = os.getenv("PASSWORD_HASH", "")
    if stored_hash and check_password_hash(stored_hash, password):
        session.permanent = True
        session["last_login"] = now()
        return redirect(url_for("index"), code=303)
    flash("Incorrect password.", "error")
    return render_template("login.jinja"), 401


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"), code=303)


@app.before_request
def require_login():
    allowed = ["login", "login_post", "logout", "static", "todos.ical_feed"]
    if request.endpoint and request.endpoint not in allowed:
        if not is_logged_in():
            return redirect(url_for("login"), code=303)


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
        title="Internal server error",
        description="Something went wrong. Please try again later.",
    ), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
