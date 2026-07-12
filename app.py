from flask import Flask, flash, redirect, render_template, request, session, url_for

import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from werkzeug.security import check_password_hash

from migrations import run_migrations
from models import TODO_STATES, Note, StickyNote, Todo, db, now
from routes import register_routes
from utils.filters import register_filters
from utils.recurring import process_due_recurrences
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


RECUR_CHECK_INTERVAL = timedelta(hours=1)
last_recur_check = None


def check_recurring_todos():
    global last_recur_check
    if last_recur_check and now() - last_recur_check < RECUR_CHECK_INTERVAL:
        return
    last_recur_check = now()
    process_due_recurrences()


@app.get("/")
def index():
    recent_notes = (
        Note.query.filter(Note.deleted_at.is_(None))
        .order_by(Note.updated_at.desc())
        .limit(5)
        .all()
    )

    sticky_notes = (
        StickyNote.query.filter(StickyNote.deleted_at.is_(None))
        .order_by(StickyNote.pinned.desc(), StickyNote.created_at.desc())
        .all()
    )
    dashboard_sticky_notes = [s for s in sticky_notes if s.pinned or not s.expired][:6]

    current_time = datetime.now()
    week_ago = current_time - timedelta(days=7)

    stats = {
        "notes": Note.query.filter(
            Note.deleted_at.is_(None), Note.archived_at.is_(None)
        ).count(),
        "open_todos": Todo.query.filter(
            Todo.deleted_at.is_(None),
            Todo.archived_at.is_(None),
            Todo.state.in_(["open", "active"]),
        ).count(),
        "overdue_todos": Todo.query.filter(
            Todo.deleted_at.is_(None),
            Todo.archived_at.is_(None),
            Todo.state.notin_(["done", "cancelled"]),
            Todo.deadline.isnot(None),
            Todo.deadline < current_time,
        ).count(),
        "sticky_notes": StickyNote.query.filter(
            StickyNote.deleted_at.is_(None)
        ).count(),
        "completed_week": Todo.query.filter(
            Todo.deleted_at.is_(None),
            Todo.completed_at.isnot(None),
            Todo.completed_at >= week_ago,
        ).count(),
    }

    due_todos = (
        Todo.query.filter(
            Todo.deleted_at.is_(None),
            Todo.archived_at.is_(None),
            Todo.deadline.isnot(None),
            Todo.state.notin_(["done", "cancelled"]),
        )
        .order_by(Todo.deadline.asc())
        .all()
    )

    upcoming_todos = []
    for todo in due_todos:
        if not todo.visible:
            continue
        upcoming_todos.append(todo)
        if len(upcoming_todos) == 5:
            break

    return render_template(
        "dashboard.jinja",
        recent_notes=recent_notes,
        sticky_notes=dashboard_sticky_notes,
        upcoming_todos=upcoming_todos,
        current_time=current_time,
        stats=stats,
    )


@app.get("/login", endpoint="login")
def login_get():
    if is_logged_in():
        return redirect(url_for("index"))
    return render_template("login.jinja")


@app.post("/login", endpoint="login_post")
def login_post():
    if is_logged_in():
        return redirect(url_for("index"))
    password = request.form.get("password", "")
    stored_hash = os.getenv("PASSWORD_HASH", "")
    if stored_hash and check_password_hash(stored_hash, password):
        session.permanent = True
        session["last_login"] = now()
        return redirect(url_for("index"), code=303)
    flash("Incorrect password.", "error")
    return render_template("login.jinja")


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"), code=303)


@app.before_request
def require_login():
    allowed = ["login", "login_post", "logout", "static", "todos.ical_feed"]
    if request.endpoint and request.endpoint not in allowed:
        if not is_logged_in():
            return redirect(url_for("login"))
        check_recurring_todos()


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
