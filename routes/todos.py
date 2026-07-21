from flask import (
    Blueprint,
    Response,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from datetime import datetime

from models import TODO_STATES, Note, StickyNote, Todo, db, now
from utils.checklist import toggle_item_checkbox
from utils.flash import flash_with_undo
from utils.groups import all_group_names, group_sections, normalize_group_name
from utils.ical import build_todo_calendar
from utils.settings import CALENDAR_TOKEN_KEY, get_setting


todos_bp = Blueprint("todos", __name__, url_prefix="/todos")


def parse_deadline(raw):
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def parse_todo_form(form):
    title = form.get("title", "").strip() or None
    content = form.get("content", "")
    group_name = normalize_group_name(form.get("group", ""))
    deadline = parse_deadline(form.get("deadline"))

    error = None
    if not title and not content.strip():
        error = "Add a title or some content."

    fields = {
        "title": title,
        "content": content,
        "group_name": group_name,
        "deadline": deadline,
    }
    return fields, error


@todos_bp.get("/")
def list_todos():
    query = Todo.query.filter(~Todo.deleted, ~Todo.archived)

    if "state" in request.args:
        selected_states = [s for s in request.args.getlist("state") if s in TODO_STATES]
    else:
        selected_states = ["open", "active"]

    query = query.filter(Todo.state.in_(selected_states))
    todos = query.order_by(Todo.created_at.desc()).all()

    selected = set(selected_states)
    chip_links = {}
    for s in TODO_STATES:
        toggled = selected ^ {s}
        chip_links[s] = url_for(
            "todos.list_todos", state=sorted(toggled) if toggled else "none"
        )

    return render_template(
        "todos/list.jinja",
        sections=group_sections(todos),
        states=TODO_STATES,
        selected_states=selected,
        chip_links=chip_links,
    )


@todos_bp.get("/trash")
def trash():
    todos = Todo.query.filter(Todo.deleted).order_by(Todo.deleted_at.desc()).all()
    return render_template("todos/trash.jinja", todos=todos)


@todos_bp.get("/archived")
def archived():
    todos = (
        Todo.query.filter(Todo.archived, ~Todo.deleted)
        .order_by(Todo.archived_at.desc())
        .all()
    )
    return render_template("todos/archived.jinja", todos=todos)


@todos_bp.get("/calendar/<token>.ics")
def ical_feed(token):
    expected_token = get_setting(CALENDAR_TOKEN_KEY)
    if not expected_token or token != expected_token:
        abort(403)

    todos = (
        Todo.query.filter(
            ~Todo.deleted,
            ~Todo.archived,
            Todo.deadline.isnot(None),
            Todo.state.notin_(["done", "cancelled"]),
        )
        .order_by(Todo.deadline.asc())
        .all()
    )
    return Response(build_todo_calendar(todos), mimetype="text/calendar")


@todos_bp.get("/new")
def new_todo():
    return render_template(
        "todos/form.jinja",
        todo=None,
        groups=all_group_names(),
        states=TODO_STATES,
    )


@todos_bp.post("/")
def create_todo():
    fields, error = parse_todo_form(request.form)

    if error:
        flash(error, "error")
        todo = Todo(**fields)
        return render_template(
            "todos/form.jinja",
            todo=todo,
            groups=all_group_names(),
            states=TODO_STATES,
        ), 400

    todo = Todo(**fields)
    db.session.add(todo)
    db.session.commit()
    flash("Todo created.", "success")
    return redirect(url_for("todos.view_todo", todo_id=todo.id), code=303)


@todos_bp.get("/<todo_id>")
def view_todo(todo_id):
    todo = Todo.query.filter(Todo.id == todo_id, ~Todo.deleted).first_or_404()
    return render_template("todos/view.jinja", todo=todo, states=TODO_STATES)


@todos_bp.patch("/<todo_id>/checkbox")
def toggle_todo_checkbox(todo_id):
    todo = Todo.query.filter(Todo.id == todo_id, ~Todo.deleted).first_or_404()
    return toggle_item_checkbox(todo, show_updated_at=True)


@todos_bp.get("/<todo_id>/edit")
def edit_todo(todo_id):
    todo = Todo.query.filter(Todo.id == todo_id, ~Todo.deleted).first_or_404()
    return render_template(
        "todos/form.jinja",
        todo=todo,
        groups=all_group_names(),
        states=TODO_STATES,
    )


@todos_bp.put("/<todo_id>")
def update_todo(todo_id):
    todo = Todo.query.filter(Todo.id == todo_id, ~Todo.deleted).first_or_404()

    fields, error = parse_todo_form(request.form)

    if error:
        flash(error, "error")
        for key, value in fields.items():
            setattr(todo, key, value)
        return render_template(
            "todos/form.jinja",
            todo=todo,
            groups=all_group_names(),
            states=TODO_STATES,
        ), 400

    for key, value in fields.items():
        setattr(todo, key, value)
    todo.updated_at = now()
    db.session.commit()
    flash("Todo saved.", "success")
    return redirect(url_for("todos.view_todo", todo_id=todo.id), code=303)


@todos_bp.post("/<todo_id>/duplicate")
def duplicate_todo(todo_id):
    todo = Todo.query.filter(Todo.id == todo_id, ~Todo.deleted).first_or_404()

    duplicate = Todo(
        title=todo.title,
        content=todo.content,
        group_name=todo.group_name,
        deadline=todo.deadline,
    )
    db.session.add(duplicate)
    db.session.commit()
    flash("Todo duplicated.", "success")
    return redirect(url_for("todos.view_todo", todo_id=duplicate.id), code=303)


@todos_bp.patch("/<todo_id>/state")
def set_state(todo_id):
    todo = Todo.query.filter(Todo.id == todo_id, ~Todo.deleted).first_or_404()
    state = request.form.get("state")
    if state not in TODO_STATES:
        flash("Invalid state.", "error")
        return render_template("todos/view.jinja", todo=todo, states=TODO_STATES), 400

    was_done = todo.state == "done"
    todo.state = state
    todo.completed_at = now() if state == "done" else None
    todo.active_at = now() if state == "active" else None
    todo.updated_at = now()
    if state == "done" and not todo.archived:
        todo.archived_at = now()
    elif was_done and state != "done":
        todo.archived_at = None
    db.session.commit()
    flash("Todo updated.", "success")
    return redirect(
        request.referrer or url_for("todos.view_todo", todo_id=todo.id), code=303
    )


def dropped_todo_fields(todo, include_group):
    dropped = []
    if include_group and todo.group_name:
        dropped.append(f"group: {todo.group_name}")
    if todo.state != "open":
        dropped.append(f"state: {todo.state.replace('_', ' ')}")
    if todo.deadline:
        dropped.append(f"deadline: {todo.deadline.strftime('%d %b %Y, %H:%M')}")
    return dropped


@todos_bp.post("/<todo_id>/convert/note")
def convert_todo_to_note(todo_id):
    todo = Todo.query.filter(Todo.id == todo_id, ~Todo.deleted).first_or_404()

    dropped = dropped_todo_fields(todo, include_group=False)
    content = todo.content
    if dropped:
        note_line = f"_Converted from todo ({', '.join(dropped)})_"
        content = f"{note_line}\n\n{content}" if content else note_line

    note = Note(
        title=todo.title,
        content=content,
        group_name=todo.group_name,
        created_at=todo.created_at,
        archived_at=todo.archived_at,
    )
    db.session.add(note)
    db.session.delete(todo)
    db.session.commit()
    flash("Todo converted to note.", "success")
    return redirect(url_for("notes.view_note", note_id=note.id), code=303)


@todos_bp.post("/<todo_id>/convert/sticky-note")
def convert_todo_to_sticky_note(todo_id):
    todo = Todo.query.filter(Todo.id == todo_id, ~Todo.deleted).first_or_404()

    dropped = dropped_todo_fields(todo, include_group=True)
    content = todo.content
    if dropped:
        note_line = f"_Converted from todo ({', '.join(dropped)})_"
        content = f"{note_line}\n\n{content}" if content else note_line

    sticky_note = StickyNote(
        title=todo.title,
        content=content,
        created_at=todo.created_at,
    )
    db.session.add(sticky_note)
    db.session.delete(todo)
    db.session.commit()
    flash("Todo converted to sticky note.", "success")
    return redirect(
        url_for("sticky_notes.list_sticky_notes", open=sticky_note.id),
        code=303,
    )


@todos_bp.delete("/<todo_id>")
def delete_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    todo.deleted_at = now()
    db.session.commit()
    flash_with_undo(
        "Todo moved to trash.", url_for("todos.restore_todo", todo_id=todo.id)
    )
    return redirect(url_for("todos.list_todos"), code=303)


@todos_bp.patch("/<todo_id>/restore")
def restore_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    todo.deleted_at = None
    db.session.commit()
    flash_with_undo(
        "Todo restored.",
        url_for("todos.delete_todo", todo_id=todo.id),
        undo_method="DELETE",
    )
    return redirect(url_for("todos.trash"), code=303)


@todos_bp.delete("/<todo_id>/purge")
def purge_todo(todo_id):
    todo = Todo.query.filter(Todo.id == todo_id, Todo.deleted).first_or_404()
    db.session.delete(todo)
    db.session.commit()
    flash("Todo permanently deleted.", "success")
    return redirect(url_for("todos.trash"), code=303)


@todos_bp.patch("/<todo_id>/archive")
def archive_todo(todo_id):
    todo = Todo.query.filter(Todo.id == todo_id, ~Todo.deleted).first_or_404()
    todo.archived_at = now()
    db.session.commit()
    flash_with_undo("Todo archived.", url_for("todos.unarchive_todo", todo_id=todo.id))
    return redirect(request.referrer or url_for("todos.list_todos"), code=303)


@todos_bp.patch("/<todo_id>/unarchive")
def unarchive_todo(todo_id):
    todo = Todo.query.filter(Todo.id == todo_id, ~Todo.deleted).first_or_404()
    todo.archived_at = None
    db.session.commit()
    flash_with_undo("Todo unarchived.", url_for("todos.archive_todo", todo_id=todo.id))
    return redirect(request.referrer or url_for("todos.archived"), code=303)
