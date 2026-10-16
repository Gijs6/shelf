from flask import Blueprint, flash, redirect, render_template, request, url_for

from models import Note, db, now
from utils.checklist import toggle_item_checkbox
from utils.flash import flash_with_undo
from utils.groups import all_group_names, group_sections, normalize_group_name

notes_bp = Blueprint("notes", __name__, url_prefix="/notes")


@notes_bp.get("/")
def list_notes():
    notes = (
        Note.query.filter(~Note.deleted, ~Note.archived)
        .order_by(Note.updated_at.desc())
        .all()
    )

    return render_template("notes/list.jinja", sections=group_sections(notes))


@notes_bp.get("/new")
def new_note():
    return render_template("notes/form.jinja", note=None, groups=all_group_names())


@notes_bp.post("/")
def create_note():
    title = request.form.get("title", "").strip() or None
    content = request.form.get("content", "")
    group_name = normalize_group_name(request.form.get("group", ""))

    if not title and not content.strip():
        flash("Add a title or some content.", "error")
        note = Note(title=title, content=content, group_name=group_name)
        return render_template(
            "notes/form.jinja", note=note, groups=all_group_names()
        ), 400

    note = Note(title=title, content=content, group_name=group_name)
    db.session.add(note)
    db.session.commit()
    flash("Note added.", "success")
    return redirect(url_for("notes.view_note", note_id=note.id), code=303)


@notes_bp.get("/<note_id>")
def view_note(note_id):
    note = Note.query.filter(Note.id == note_id, ~Note.deleted).first_or_404()
    return render_template("notes/view.jinja", note=note)


@notes_bp.patch("/<note_id>/checkbox")
def toggle_note_checkbox(note_id):
    note = Note.query.filter(Note.id == note_id, ~Note.deleted).first_or_404()
    return toggle_item_checkbox(note, show_updated_at=True)


@notes_bp.get("/<note_id>/edit")
def edit_note(note_id):
    note = Note.query.filter(Note.id == note_id, ~Note.deleted).first_or_404()
    return render_template("notes/form.jinja", note=note, groups=all_group_names())


@notes_bp.put("/<note_id>")
def update_note(note_id):
    note = Note.query.filter(Note.id == note_id, ~Note.deleted).first_or_404()

    title = request.form.get("title", "").strip() or None
    content = request.form.get("content", "")
    group_name = normalize_group_name(request.form.get("group", ""))

    if not title and not content.strip():
        flash("Add a title or some content.", "error")
        note.title = title
        note.content = content
        note.group_name = group_name
        return render_template(
            "notes/form.jinja", note=note, groups=all_group_names()
        ), 400

    note.title = title
    note.content = content
    note.group_name = group_name
    note.updated_at = now()
    db.session.commit()
    flash("Note saved.", "success")
    return redirect(url_for("notes.view_note", note_id=note.id), code=303)


@notes_bp.post("/<note_id>/duplicate")
def duplicate_note(note_id):
    note = Note.query.filter(Note.id == note_id, ~Note.deleted).first_or_404()

    duplicate = Note(title=note.title, content=note.content, group_name=note.group_name)
    db.session.add(duplicate)
    db.session.commit()
    flash("Note duplicated.", "success")
    return redirect(url_for("notes.view_note", note_id=duplicate.id), code=303)


@notes_bp.delete("/<note_id>")
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    note.deleted_at = now()
    db.session.commit()
    flash_with_undo("Note deleted.", url_for("notes.restore_note", note_id=note.id))
    if request.args.get("next") == "archive":
        return redirect(url_for("storage.archive"), code=303)
    return redirect(url_for("notes.list_notes"), code=303)


@notes_bp.patch("/<note_id>/restore")
def restore_note(note_id):
    note = Note.query.get_or_404(note_id)
    note.deleted_at = None
    db.session.commit()
    flash_with_undo(
        "Note restored.",
        url_for("notes.delete_note", note_id=note.id),
        undo_method="DELETE",
    )
    return redirect(url_for("storage.trash"), code=303)


@notes_bp.delete("/<note_id>/purge")
def purge_note(note_id):
    note = Note.query.filter(Note.id == note_id, Note.deleted).first_or_404()
    db.session.delete(note)
    db.session.commit()
    flash("Note purged.", "success")
    return redirect(url_for("storage.trash"), code=303)


@notes_bp.patch("/<note_id>/archive")
def archive_note(note_id):
    note = Note.query.filter(Note.id == note_id, ~Note.deleted).first_or_404()
    note.archived_at = now()
    db.session.commit()
    flash_with_undo("Note archived.", url_for("notes.unarchive_note", note_id=note.id))
    return redirect(request.referrer or url_for("notes.list_notes"), code=303)


@notes_bp.patch("/<note_id>/unarchive")
def unarchive_note(note_id):
    note = Note.query.filter(Note.id == note_id, ~Note.deleted).first_or_404()
    note.archived_at = None
    db.session.commit()
    flash_with_undo("Note unarchived.", url_for("notes.archive_note", note_id=note.id))
    return redirect(request.referrer or url_for("storage.archive"), code=303)
