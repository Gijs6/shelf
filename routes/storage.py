from flask import Blueprint, flash, redirect, render_template, url_for

from models import Bookmark, Note, StickyNote, Todo, db
from routes.settings import count_summary

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
        (
            "Bookmarks",
            Bookmark.query.filter(Bookmark.deleted)
            .order_by(Bookmark.deleted_at.desc())
            .all(),
        ),
    ]
    return render_template("trash.jinja", sections=non_empty(sections))


@storage_bp.delete("/trash")
def purge_trash():
    counts = {
        "notes": Note.query.filter(Note.deleted).delete(synchronize_session=False),
        "sticky_notes": StickyNote.query.filter(StickyNote.deleted).delete(
            synchronize_session=False
        ),
        "todos": Todo.query.filter(Todo.deleted).delete(synchronize_session=False),
        "bookmarks": Bookmark.query.filter(Bookmark.deleted).delete(
            synchronize_session=False
        ),
    }
    db.session.commit()

    flash(f"Purged {count_summary(counts)} from trash.", "success")
    return redirect(url_for("storage.trash"), code=303)


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
