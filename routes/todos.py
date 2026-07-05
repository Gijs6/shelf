from flask import Blueprint, flash, redirect, render_template, request, url_for

from datetime import datetime

from models import TODO_STATES, Todo, db, now
from utils.groups import all_group_names, group_sections


todos_bp = Blueprint("todos", __name__, url_prefix="/todos")


def parse_deadline(raw):
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


@todos_bp.get("/")
def list_todos():
    query = Todo.query.filter(Todo.deleted_at.is_(None), Todo.archived_at.is_(None))

    state = request.args.get("state")
    if state in TODO_STATES:
        query = query.filter_by(state=state)

    todos = query.order_by(Todo.created_at.desc()).all()

    return render_template(
        "todos/list.jinja",
        sections=group_sections(todos),
        states=TODO_STATES,
        active_state=state,
    )


@todos_bp.get("/trash")
def trash():
    todos = (
        Todo.query.filter(Todo.deleted_at.isnot(None))
        .order_by(Todo.deleted_at.desc())
        .all()
    )
    return render_template("todos/trash.jinja", todos=todos)


@todos_bp.get("/archived")
def archived():
    todos = (
        Todo.query.filter(Todo.archived_at.isnot(None), Todo.deleted_at.is_(None))
        .order_by(Todo.archived_at.desc())
        .all()
    )
    return render_template("todos/archived.jinja", todos=todos)


@todos_bp.get("/new")
def new_todo():
    return render_template(
        "todos/form.jinja", todo=None, groups=all_group_names(), states=TODO_STATES
    )


@todos_bp.post("/")
def create_todo():
    title = request.form.get("title", "").strip() or None
    content = request.form.get("content", "")
    group_name = request.form.get("group", "").strip() or None
    deadline = parse_deadline(request.form.get("deadline"))

    if not title and not content.strip():
        flash("Add a title or some content.", "error")
        todo = Todo(
            title=title, content=content, group_name=group_name, deadline=deadline
        )
        return render_template(
            "todos/form.jinja",
            todo=todo,
            groups=all_group_names(),
            states=TODO_STATES,
        ), 400

    todo = Todo(title=title, content=content, group_name=group_name, deadline=deadline)
    db.session.add(todo)
    db.session.commit()
    flash("Todo created.", "success")
    return redirect(url_for("todos.view_todo", todo_id=todo.id), code=303)


@todos_bp.get("/<todo_id>")
def view_todo(todo_id):
    todo = Todo.query.filter(
        Todo.id == todo_id, Todo.deleted_at.is_(None)
    ).first_or_404()
    return render_template("todos/view.jinja", todo=todo, states=TODO_STATES)


@todos_bp.get("/<todo_id>/edit")
def edit_todo(todo_id):
    todo = Todo.query.filter(
        Todo.id == todo_id, Todo.deleted_at.is_(None)
    ).first_or_404()
    return render_template(
        "todos/form.jinja", todo=todo, groups=all_group_names(), states=TODO_STATES
    )


@todos_bp.put("/<todo_id>")
def update_todo(todo_id):
    todo = Todo.query.filter(
        Todo.id == todo_id, Todo.deleted_at.is_(None)
    ).first_or_404()

    title = request.form.get("title", "").strip() or None
    content = request.form.get("content", "")
    group_name = request.form.get("group", "").strip() or None
    deadline = parse_deadline(request.form.get("deadline"))

    if not title and not content.strip():
        flash("Add a title or some content.", "error")
        todo.title = title
        todo.content = content
        todo.group_name = group_name
        todo.deadline = deadline
        return render_template(
            "todos/form.jinja",
            todo=todo,
            groups=all_group_names(),
            states=TODO_STATES,
        ), 400

    todo.title = title
    todo.content = content
    todo.group_name = group_name
    todo.deadline = deadline
    todo.updated_at = now()
    db.session.commit()
    flash("Todo saved.", "success")
    return redirect(url_for("todos.view_todo", todo_id=todo.id), code=303)


@todos_bp.patch("/<todo_id>/state")
def set_state(todo_id):
    todo = Todo.query.filter(
        Todo.id == todo_id, Todo.deleted_at.is_(None)
    ).first_or_404()
    state = request.form.get("state")
    if state not in TODO_STATES:
        flash("Invalid state.", "error")
        return redirect(url_for("todos.view_todo", todo_id=todo.id), code=303)

    todo.state = state
    todo.completed_at = now() if state == "done" else None
    todo.active_at = now() if state == "active" else None
    todo.updated_at = now()
    if state == "done" and todo.archived_at is None:
        todo.archived_at = now()
    db.session.commit()
    flash("Todo updated.", "success")
    return redirect(
        request.referrer or url_for("todos.view_todo", todo_id=todo.id), code=303
    )


@todos_bp.delete("/<todo_id>/delete")
def delete_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    todo.deleted_at = now()
    db.session.commit()
    flash("Todo moved to trash.", "success")
    return redirect(url_for("todos.list_todos"), code=303)


@todos_bp.patch("/<todo_id>/restore")
def restore_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    todo.deleted_at = None
    db.session.commit()
    flash("Todo restored.", "success")
    return redirect(url_for("todos.trash"), code=303)


@todos_bp.delete("/<todo_id>/purge")
def purge_todo(todo_id):
    todo = Todo.query.filter(
        Todo.id == todo_id, Todo.deleted_at.isnot(None)
    ).first_or_404()
    db.session.delete(todo)
    db.session.commit()
    flash("Todo permanently deleted.", "success")
    return redirect(url_for("todos.trash"), code=303)


@todos_bp.patch("/<todo_id>/archive")
def archive_todo(todo_id):
    todo = Todo.query.filter(
        Todo.id == todo_id, Todo.deleted_at.is_(None)
    ).first_or_404()
    todo.archived_at = now()
    db.session.commit()
    flash("Todo archived.", "success")
    return redirect(url_for("todos.list_todos"), code=303)


@todos_bp.patch("/<todo_id>/unarchive")
def unarchive_todo(todo_id):
    todo = Todo.query.filter(
        Todo.id == todo_id, Todo.deleted_at.is_(None)
    ).first_or_404()
    todo.archived_at = None
    db.session.commit()
    flash("Todo unarchived.", "success")
    return redirect(url_for("todos.archived"), code=303)
