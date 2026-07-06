import re

from sqlalchemy import and_, func, or_

from models import TODO_STATES, Note, StickyNote, Todo, make_snippet, now


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


def parse_bool(value):
    return value.lower() in ("yes", "true", "1", "y")


def parse_query(raw_query):
    types = None
    state = None
    group = None
    archived = None
    pinned = None
    overdue = None
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

    return {
        "types": effective_types,
        "state": state,
        "group": group,
        "archived": archived,
        "pinned": pinned,
        "overdue": overdue,
        "text": " ".join(words).strip(),
    }


def search(raw_query, limit=50):
    parsed = parse_query(raw_query)
    types = parsed["types"]
    results = []

    if "note" in types:
        query = Note.query.filter(Note.deleted_at.is_(None))
        if parsed["archived"] is not None:
            query = query.filter(
                Note.archived_at.isnot(None)
                if parsed["archived"]
                else Note.archived_at.is_(None)
            )
        if parsed["group"]:
            query = query.filter(func.lower(Note.group_name) == parsed["group"].lower())
        if parsed["text"]:
            like = f"%{parsed['text']}%"
            query = query.filter(or_(Note.title.ilike(like), Note.content.ilike(like)))
        for note in query.all():
            results.append(
                {
                    "kind": "note",
                    "title": note.display_title,
                    "snippet": note.snippet,
                    "updated_at": note.updated_at,
                    "endpoint": "notes.view_note",
                    "url_kwargs": {"note_id": note.id},
                    "group_name": note.group_name,
                    "archived": note.archived,
                }
            )

    if "todo" in types:
        query = Todo.query.filter(Todo.deleted_at.is_(None))
        if parsed["archived"] is not None:
            query = query.filter(
                Todo.archived_at.isnot(None)
                if parsed["archived"]
                else Todo.archived_at.is_(None)
            )
        if parsed["state"]:
            query = query.filter(Todo.state == parsed["state"])
        if parsed["group"]:
            query = query.filter(func.lower(Todo.group_name) == parsed["group"].lower())
        if parsed["overdue"] is not None:
            current_time = now().replace(tzinfo=None)
            is_overdue = and_(
                Todo.deadline.isnot(None),
                Todo.state.notin_(["done", "cancelled"]),
                Todo.deadline < current_time,
            )
            query = query.filter(is_overdue if parsed["overdue"] else ~is_overdue)
        if parsed["text"]:
            like = f"%{parsed['text']}%"
            query = query.filter(or_(Todo.title.ilike(like), Todo.content.ilike(like)))
        for todo in query.all():
            results.append(
                {
                    "kind": "todo",
                    "title": todo.display_title,
                    "snippet": todo.snippet,
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
        query = StickyNote.query
        if parsed["pinned"] is not None:
            query = query.filter(StickyNote.pinned == parsed["pinned"])
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
                    "updated_at": sticky_note.updated_at,
                    "endpoint": "sticky_notes.edit_sticky_note",
                    "url_kwargs": {"sticky_note_id": sticky_note.id},
                    "pinned": sticky_note.pinned,
                    "expired": sticky_note.expired,
                }
            )

    results.sort(key=lambda result: result["updated_at"], reverse=True)
    return results[:limit], parsed
