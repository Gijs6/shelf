import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_

from models import STICKY_COLOURS, TODO_STATES, Note, StickyNote, Todo, make_snippet


TYPE_ALIASES = {
    "note": "note",
    "notes": "note",
    "todo": "todo",
    "todos": "todo",
    "sticky": "sticky",
    "stickynote": "sticky",
    "stickynotes": "sticky",
    "sticky-note": "sticky",
    "sticky-notes": "sticky",
    "sticky_note": "sticky",
    "sticky_notes": "sticky",
}

ALL_TYPES = {"note", "todo", "sticky"}

TOKEN_RE = re.compile(r"(\S+):(\S+)|(\S+)")


SORT_KEYS = ("title", "created", "updated")
DUE_KEYS = ("today", "week")


def parse_bool(value):
    return value.lower() in ("yes", "true", "1", "y")


def parse_date(value):
    try:
        local_midnight = datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None
    return local_midnight.astimezone().astimezone(timezone.utc)


def parse_query(raw_query):
    types = None
    state = None
    group = None
    archived = None
    pinned = None
    overdue = None
    before = None
    after = None
    due = None
    sort = None
    colour = None
    words = []

    for match in TOKEN_RE.finditer(raw_query or ""):
        key, value, word = match.groups()

        if key is None:
            words.append(word)
            continue

        key = key.lower()
        if key == "is" and value.lower() in TYPE_ALIASES:
            types = (types or set()) | {TYPE_ALIASES[value.lower()]}
        elif key == "state" and value.lower() in TODO_STATES:
            state = value.lower()
        elif key == "group":
            group = value
        elif key == "archived":
            archived = parse_bool(value)
        elif key == "pinned":
            pinned = parse_bool(value)
        elif key == "overdue":
            overdue = parse_bool(value)
        elif key == "before" and parse_date(value) is not None:
            before = parse_date(value)
        elif key == "after" and parse_date(value) is not None:
            after = parse_date(value)
        elif key == "due" and value.lower() in DUE_KEYS:
            due = value.lower()
        elif key == "sort" and value.lower() in SORT_KEYS:
            sort = value.lower()
        elif key == "colour" and value.lower() in STICKY_COLOURS:
            colour = value.lower()
        else:
            words.append(f"{key}:{value}")

    effective_types = types if types is not None else set(ALL_TYPES)
    if state is not None:
        effective_types &= {"todo"}
    if pinned is not None:
        effective_types &= {"sticky"}
    if overdue is not None:
        effective_types &= {"todo"}
    if archived is not None:
        effective_types &= {"note", "todo"}
    if due is not None:
        effective_types &= {"todo"}
    if colour is not None:
        effective_types &= {"sticky"}

    return {
        "types": effective_types,
        "state": state,
        "group": group,
        "archived": archived,
        "pinned": pinned,
        "overdue": overdue,
        "before": before,
        "after": after,
        "due": due,
        "sort": sort,
        "colour": colour,
        "text": " ".join(words).strip(),
    }


def search(raw_query, limit=50):
    parsed = parse_query(raw_query)
    types = parsed["types"]
    results = []

    if "note" in types:
        query = Note.query.filter(~Note.deleted)
        if parsed["archived"] is not None:
            query = query.filter(Note.archived.is_(parsed["archived"]))
        if parsed["group"]:
            query = query.filter(func.lower(Note.group_name) == parsed["group"].lower())
        if parsed["before"] is not None:
            query = query.filter(Note.created_at < parsed["before"])
        if parsed["after"] is not None:
            query = query.filter(Note.created_at >= parsed["after"])
        if parsed["text"]:
            like = f"%{parsed['text']}%"
            query = query.filter(or_(Note.title.ilike(like), Note.content.ilike(like)))
        for note in query.all():
            results.append(
                {
                    "kind": "note",
                    "title": note.display_title,
                    "snippet": note.snippet,
                    "created_at": note.created_at,
                    "updated_at": note.updated_at,
                    "endpoint": "notes.view_note",
                    "url_kwargs": {"note_id": note.id},
                    "group_name": note.group_name,
                    "archived": note.archived,
                }
            )

    if "todo" in types:
        query = Todo.query.filter(~Todo.deleted)
        if parsed["archived"] is not None:
            query = query.filter(Todo.archived.is_(parsed["archived"]))
        if parsed["state"]:
            query = query.filter(Todo.state == parsed["state"])
        if parsed["group"]:
            query = query.filter(func.lower(Todo.group_name) == parsed["group"].lower())
        if parsed["overdue"] is not None:
            query = query.filter(Todo.overdue if parsed["overdue"] else ~Todo.overdue)
        if parsed["before"] is not None:
            query = query.filter(Todo.created_at < parsed["before"])
        if parsed["after"] is not None:
            query = query.filter(Todo.created_at >= parsed["after"])
        if parsed["due"] == "today":
            day_start = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            query = query.filter(
                Todo.deadline.isnot(None),
                Todo.deadline >= day_start,
                Todo.deadline < day_start + timedelta(days=1),
                Todo.state.notin_(["done", "cancelled"]),
            )
        elif parsed["due"] == "week":
            current_time = datetime.now()
            query = query.filter(
                Todo.deadline.isnot(None),
                Todo.deadline >= current_time,
                Todo.deadline < current_time + timedelta(days=7),
                Todo.state.notin_(["done", "cancelled"]),
            )
        if parsed["text"]:
            like = f"%{parsed['text']}%"
            query = query.filter(or_(Todo.title.ilike(like), Todo.content.ilike(like)))
        for todo in query.all():
            results.append(
                {
                    "kind": "todo",
                    "title": todo.display_title,
                    "snippet": todo.snippet,
                    "created_at": todo.created_at,
                    "updated_at": todo.updated_at,
                    "endpoint": "todos.view_todo",
                    "url_kwargs": {"todo_id": todo.id},
                    "group_name": todo.group_name,
                    "archived": todo.archived,
                    "state": todo.state,
                    "overdue": todo.overdue,
                }
            )

    if "sticky" in types:
        query = StickyNote.query.filter(~StickyNote.deleted)
        if parsed["pinned"] is not None:
            query = query.filter(StickyNote.pinned == parsed["pinned"])
        if parsed["colour"]:
            query = query.filter(StickyNote.colour == parsed["colour"])
        if parsed["before"] is not None:
            query = query.filter(StickyNote.created_at < parsed["before"])
        if parsed["after"] is not None:
            query = query.filter(StickyNote.created_at >= parsed["after"])
        if parsed["text"]:
            like = f"%{parsed['text']}%"
            query = query.filter(
                or_(StickyNote.title.ilike(like), StickyNote.content.ilike(like))
            )
        for sticky_note in query.all():
            results.append(
                {
                    "kind": "sticky",
                    "title": sticky_note.display_title,
                    "snippet": make_snippet(sticky_note.content),
                    "created_at": sticky_note.created_at,
                    "updated_at": sticky_note.updated_at,
                    "endpoint": "sticky_notes.expired"
                    if sticky_note.expired
                    else "sticky_notes.list_sticky_notes",
                    "url_kwargs": {"_anchor": f"sticky-{sticky_note.id}"},
                    "pinned": sticky_note.pinned,
                    "expired": sticky_note.expired,
                    "colour": sticky_note.colour,
                }
            )

    if parsed["sort"] == "title":
        results.sort(key=lambda result: result["title"].lower())
    elif parsed["sort"] == "created":
        results.sort(key=lambda result: result["created_at"], reverse=True)
    else:
        results.sort(key=lambda result: result["updated_at"], reverse=True)

    return results[:limit], parsed
