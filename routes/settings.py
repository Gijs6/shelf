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
import secrets

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
from utils.datetimes import parse_utc_datetime, utc_isoformat
from utils.filters import pluralize_filter as pluralize
from utils.groups import group_name_counts, normalize_group_name
from utils.settings import CALENDAR_TOKEN_KEY, delete_setting, get_setting, set_setting

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


def note_to_dict(note):
    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "created_at": utc_isoformat(note.created_at),
        "updated_at": utc_isoformat(note.updated_at),
        "group_name": note.group_name,
        "deleted_at": utc_isoformat(note.deleted_at),
        "archived_at": utc_isoformat(note.archived_at),
    }


def sticky_note_to_dict(sticky_note):
    return {
        "id": sticky_note.id,
        "content": sticky_note.content,
        "created_at": utc_isoformat(sticky_note.created_at),
        "updated_at": utc_isoformat(sticky_note.updated_at),
        "colour": sticky_note.colour,
        "pinned": sticky_note.pinned,
        "deleted_at": utc_isoformat(sticky_note.deleted_at),
    }


def todo_to_dict(todo):
    return {
        "id": todo.id,
        "title": todo.title,
        "content": todo.content,
        "created_at": utc_isoformat(todo.created_at),
        "updated_at": utc_isoformat(todo.updated_at),
        "state": todo.state,
        "completed_at": utc_isoformat(todo.completed_at),
        "active_at": utc_isoformat(todo.active_at),
        "group_name": todo.group_name,
        "deadline": utc_isoformat(todo.deadline),
        "deleted_at": utc_isoformat(todo.deleted_at),
        "archived_at": utc_isoformat(todo.archived_at),
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
    note.created_at = parse_utc_datetime(data.get("created_at")) or now()
    note.updated_at = parse_utc_datetime(data.get("updated_at")) or now()
    note.deleted_at = parse_utc_datetime(data.get("deleted_at"))
    note.archived_at = parse_utc_datetime(data.get("archived_at"))
    return note


def apply_sticky_note(data):
    sticky_note = get_or_create(StickyNote, data)
    colour = data.get("colour", "yellow")
    sticky_note.content = data.get("content", "")
    sticky_note.colour = colour if colour in STICKY_COLOURS else "yellow"
    sticky_note.pinned = bool(data.get("pinned"))
    sticky_note.created_at = parse_utc_datetime(data.get("created_at")) or now()
    sticky_note.updated_at = parse_utc_datetime(data.get("updated_at")) or now()
    sticky_note.deleted_at = parse_utc_datetime(data.get("deleted_at"))
    return sticky_note


def apply_todo(data):
    todo = get_or_create(Todo, data)
    state = data.get("state", "open")
    todo.title = data.get("title")
    todo.content = data.get("content", "")
    todo.state = state if state in TODO_STATES else "open"
    todo.group_name = data.get("group_name")
    todo.created_at = parse_utc_datetime(data.get("created_at")) or now()
    todo.updated_at = parse_utc_datetime(data.get("updated_at")) or now()
    todo.completed_at = parse_utc_datetime(data.get("completed_at"))
    todo.active_at = parse_utc_datetime(data.get("active_at"))
    todo.deadline = parse_utc_datetime(data.get("deadline"))
    todo.deleted_at = parse_utc_datetime(data.get("deleted_at"))
    todo.archived_at = parse_utc_datetime(data.get("archived_at"))
    return todo


def is_blank(data):
    return (
        not (data.get("title") or "").strip()
        and not (data.get("content") or "").strip()
    )


def count_summary(counts):
    notes = counts["notes"]
    sticky_notes = counts["sticky_notes"]
    todos = counts["todos"]
    return (
        f"{notes} {pluralize(notes, 'note')}, "
        f"{sticky_notes} sticky {pluralize(sticky_notes, 'note')} and "
        f"{todos} {pluralize(todos, 'todo')}"
    )


@settings_bp.get("/")
def index():
    calendar_token = get_setting(CALENDAR_TOKEN_KEY)
    calendar_url = (
        url_for("todos.ical_feed", token=calendar_token, _external=True)
        if calendar_token
        else None
    )
    return render_template(
        "settings/index.jinja",
        calendar_url=calendar_url,
        group_counts=group_name_counts(),
    )


@settings_bp.post("/calendar-token")
def generate_calendar_token():
    set_setting(CALENDAR_TOKEN_KEY, secrets.token_urlsafe(24))
    flash("Calendar token generated.", "success")
    return redirect(url_for("settings.index"), code=303)


@settings_bp.delete("/calendar-token")
def revoke_calendar_token():
    delete_setting(CALENDAR_TOKEN_KEY)
    flash("Calendar token revoked.", "success")
    return redirect(url_for("settings.index"), code=303)


@settings_bp.get("/export")
def export():
    payload = {
        "exported_at": utc_isoformat(now()),
        "notes": [note_to_dict(note) for note in Note.query.all()],
        "sticky_notes": [
            sticky_note_to_dict(sticky_note) for sticky_note in StickyNote.query.all()
        ],
        "todos": [todo_to_dict(todo) for todo in Todo.query.all()],
        "settings": {"calendar_token": get_setting(CALENDAR_TOKEN_KEY)},
    }
    filename = f"shelf-export-{now().strftime('%Y%m%d-%H%M%S')}.json"
    return Response(
        json.dumps(payload, indent=4),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@settings_bp.post("/import")
def import_data():
    file = request.files.get("file")
    if not file or not file.filename:
        flash("Choose a JSON file to import.", "error")
        return index(), 400

    try:
        payload = json.load(file.stream)
        if not isinstance(payload, dict):
            raise TypeError("Expected a JSON object")

        counts = {"notes": 0, "sticky_notes": 0, "todos": 0}

        for data in payload.get("notes") or []:
            if is_blank(data):
                continue
            db.session.add(apply_note(data))
            counts["notes"] += 1

        for data in payload.get("sticky_notes") or []:
            if is_blank(data):
                continue
            db.session.add(apply_sticky_note(data))
            counts["sticky_notes"] += 1

        for data in payload.get("todos") or []:
            if is_blank(data):
                continue
            db.session.add(apply_todo(data))
            counts["todos"] += 1

        db.session.commit()
    except (ValueError, TypeError, AttributeError, KeyError):
        db.session.rollback()
        flash("That file isn't a valid Shelf export.", "error")
        return index(), 400

    calendar_token = (payload.get("settings") or {}).get("calendar_token")
    if calendar_token:
        set_setting(CALENDAR_TOKEN_KEY, calendar_token)

    flash(f"Imported {count_summary(counts)}.", "success")
    return redirect(url_for("settings.index"), code=303)


@settings_bp.post("/groups/rename")
def rename_group():
    old_name = (request.form.get("old_name") or "").strip()
    new_name = normalize_group_name(request.form.get("new_name"), exclude=old_name)

    if not old_name or not new_name:
        flash("Enter a new group name.", "error")
        return index(), 400

    note_count = Note.query.filter(Note.group_name == old_name).update(
        {"group_name": new_name}, synchronize_session=False
    )
    todo_count = Todo.query.filter(Todo.group_name == old_name).update(
        {"group_name": new_name}, synchronize_session=False
    )
    db.session.commit()

    item_count = note_count + todo_count
    flash(
        f'Renamed "{old_name}" to "{new_name}" ({item_count} {pluralize(item_count, "item")}).',
        "success",
    )
    return redirect(url_for("settings.index"), code=303)
