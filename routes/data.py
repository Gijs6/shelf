from flask import (
    Blueprint,
    Response,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

import json
from datetime import datetime

from models import (
    STICKY_COLOURS,
    TODO_STATES,
    Note,
    StickyNote,
    Todo,
    db,
    generate_id,
    now,
)


data_bp = Blueprint("data", __name__, url_prefix="/data")


def iso(dt):
    return dt.isoformat() if dt else None


def parse_dt(value):
    return datetime.fromisoformat(value) if value else None


def note_to_dict(note):
    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "created_at": iso(note.created_at),
        "updated_at": iso(note.updated_at),
        "group_name": note.group_name,
        "deleted_at": iso(note.deleted_at),
        "archived_at": iso(note.archived_at),
    }


def sticky_note_to_dict(sticky_note):
    return {
        "id": sticky_note.id,
        "title": sticky_note.title,
        "content": sticky_note.content,
        "created_at": iso(sticky_note.created_at),
        "updated_at": iso(sticky_note.updated_at),
        "expires_at": iso(sticky_note.expires_at),
        "colour": sticky_note.colour,
        "pinned": sticky_note.pinned,
    }


def todo_to_dict(todo):
    return {
        "id": todo.id,
        "title": todo.title,
        "content": todo.content,
        "created_at": iso(todo.created_at),
        "updated_at": iso(todo.updated_at),
        "state": todo.state,
        "completed_at": iso(todo.completed_at),
        "active_at": iso(todo.active_at),
        "group_name": todo.group_name,
        "deadline": iso(todo.deadline),
        "deleted_at": iso(todo.deleted_at),
        "archived_at": iso(todo.archived_at),
    }


def get_or_create(model, data):
    item_id = data.get("id")
    instance = model.query.get(item_id) if item_id else None
    return instance or model(id=item_id or generate_id())


def apply_note(data):
    note = get_or_create(Note, data)
    note.title = data.get("title")
    note.content = data.get("content", "")
    note.group_name = data.get("group_name")
    note.created_at = parse_dt(data.get("created_at")) or now()
    note.updated_at = parse_dt(data.get("updated_at")) or now()
    note.deleted_at = parse_dt(data.get("deleted_at"))
    note.archived_at = parse_dt(data.get("archived_at"))
    return note


def apply_sticky_note(data):
    sticky_note = get_or_create(StickyNote, data)
    colour = data.get("colour", "yellow")
    sticky_note.title = data.get("title")
    sticky_note.content = data.get("content", "")
    sticky_note.colour = colour if colour in STICKY_COLOURS else "yellow"
    sticky_note.pinned = bool(data.get("pinned"))
    sticky_note.created_at = parse_dt(data.get("created_at")) or now()
    sticky_note.updated_at = parse_dt(data.get("updated_at")) or now()
    sticky_note.expires_at = parse_dt(data.get("expires_at"))
    return sticky_note


def apply_todo(data):
    todo = get_or_create(Todo, data)
    state = data.get("state", "open")
    todo.title = data.get("title")
    todo.content = data.get("content", "")
    todo.state = state if state in TODO_STATES else "open"
    todo.group_name = data.get("group_name")
    todo.created_at = parse_dt(data.get("created_at")) or now()
    todo.updated_at = parse_dt(data.get("updated_at")) or now()
    todo.completed_at = parse_dt(data.get("completed_at"))
    todo.active_at = parse_dt(data.get("active_at"))
    todo.deadline = parse_dt(data.get("deadline"))
    todo.deleted_at = parse_dt(data.get("deleted_at"))
    todo.archived_at = parse_dt(data.get("archived_at"))
    return todo


@data_bp.get("/")
def index():
    return render_template("data/index.jinja")


@data_bp.get("/export")
def export():
    payload = {
        "exported_at": iso(now()),
        "notes": [note_to_dict(note) for note in Note.query.all()],
        "sticky_notes": [
            sticky_note_to_dict(sticky_note) for sticky_note in StickyNote.query.all()
        ],
        "todos": [todo_to_dict(todo) for todo in Todo.query.all()],
    }
    filename = f"shelf-export-{now().strftime('%Y%m%d-%H%M%S')}.json"
    return Response(
        json.dumps(payload, indent=4),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@data_bp.post("/import")
def import_data():
    file = request.files.get("file")
    if not file or not file.filename:
        flash("Choose a JSON file to import.", "error")
        return redirect(url_for("data.index"), code=303)

    try:
        payload = json.load(file.stream)
        if not isinstance(payload, dict):
            raise ValueError("Expected a JSON object")

        counts = {"notes": 0, "sticky_notes": 0, "todos": 0}

        for data in payload.get("notes") or []:
            db.session.add(apply_note(data))
            counts["notes"] += 1

        for data in payload.get("sticky_notes") or []:
            db.session.add(apply_sticky_note(data))
            counts["sticky_notes"] += 1

        for data in payload.get("todos") or []:
            db.session.add(apply_todo(data))
            counts["todos"] += 1

        db.session.commit()
    except (ValueError, TypeError, AttributeError, KeyError):
        db.session.rollback()
        flash("That file isn't a valid Shelf export.", "error")
        return redirect(url_for("data.index"), code=303)

    flash(
        f"Imported {counts['notes']} notes, {counts['sticky_notes']} sticky notes, "
        f"{counts['todos']} todos.",
        "success",
    )
    return redirect(url_for("data.index"), code=303)


@data_bp.delete("/")
def remove_all():
    Note.query.delete()
    StickyNote.query.delete()
    Todo.query.delete()
    db.session.commit()

    flash("Removed all notes, sticky notes, and todos.", "success")
    return redirect(url_for("data.index"), code=303)
