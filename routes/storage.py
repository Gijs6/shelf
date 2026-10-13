from flask import Blueprint, render_template

from models import Note, StickyNote, Todo

storage_bp = Blueprint("storage", __name__)


def non_empty(sections):
    return [(label, items) for label, items in sections if items]


@storage_bp.get("/trash")
def trash():
    sections = [
        (
            "Notes",
            Note.query.filter(Note.deleted).order_by(Note.deleted_at.desc()).all(),
        ),
        (
            "Todos",
            Todo.query.filter(Todo.deleted).order_by(Todo.deleted_at.desc()).all(),
        ),
        (
            "Sticky notes",
            StickyNote.query.filter(StickyNote.deleted)
            .order_by(StickyNote.deleted_at.desc())
            .all(),
        ),
    ]
    return render_template("trash.jinja", sections=non_empty(sections))


@storage_bp.get("/archive")
def archive():
    sections = [
        (
            "Notes",
            Note.query.filter(Note.archived, ~Note.deleted)
            .order_by(Note.archived_at.desc())
            .all(),
        ),
        (
            "Todos",
            Todo.query.filter(Todo.archived, ~Todo.deleted)
            .order_by(Todo.archived_at.desc())
            .all(),
        ),
    ]
    return render_template("archive.jinja", sections=non_empty(sections))
