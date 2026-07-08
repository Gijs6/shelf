from flask import Blueprint, flash, redirect, render_template, request, url_for

from datetime import datetime, timedelta

from models import STICKY_COLOURS, StickyNote, db, now


sticky_notes_bp = Blueprint("sticky_notes", __name__, url_prefix="/sticky-notes")

DEFAULT_EXPIRY_DAYS = 30


def parse_expires_at(raw):
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


@sticky_notes_bp.get("/")
def list_sticky_notes():
    active = (
        StickyNote.query.filter(StickyNote.deleted_at.is_(None))
        .order_by(StickyNote.pinned.desc(), StickyNote.created_at.desc())
        .all()
    )
    active = [n for n in active if not n.expired]
    pinned = [n for n in active if n.pinned]
    unpinned = [n for n in active if not n.pinned]
    return render_template(
        "sticky_notes/list.jinja",
        pinned_notes=pinned,
        active_notes=unpinned,
        colours=STICKY_COLOURS,
    )


@sticky_notes_bp.get("/expired")
def expired():
    notes = [
        n
        for n in StickyNote.query.filter(StickyNote.deleted_at.is_(None)).all()
        if n.expired
    ]
    notes.sort(key=lambda n: n.expires_at, reverse=True)
    return render_template("sticky_notes/expired.jinja", notes=notes)


@sticky_notes_bp.get("/trash")
def trash():
    notes = (
        StickyNote.query.filter(StickyNote.deleted_at.isnot(None))
        .order_by(StickyNote.deleted_at.desc())
        .all()
    )
    return render_template("sticky_notes/trash.jinja", notes=notes)


@sticky_notes_bp.get("/new")
def new_sticky_note():
    default_expires_at = datetime.now() + timedelta(days=DEFAULT_EXPIRY_DAYS)
    return render_template(
        "sticky_notes/form.jinja",
        sticky_note=None,
        colours=STICKY_COLOURS,
        default_expires_at=default_expires_at,
    )


@sticky_notes_bp.post("/")
def create_sticky_note():
    title = request.form.get("title", "").strip() or None

    colour = request.form.get("colour", "yellow")
    if colour not in STICKY_COLOURS:
        colour = "yellow"

    sticky_note = StickyNote(
        title=title,
        content=request.form.get("content", ""),
        colour=colour,
        expires_at=parse_expires_at(request.form.get("expires_at")),
        pinned=bool(request.form.get("pinned")),
    )
    db.session.add(sticky_note)
    db.session.commit()
    flash("Sticky note created.", "success")
    return redirect(url_for("sticky_notes.list_sticky_notes"), code=303)


@sticky_notes_bp.get("/<sticky_note_id>/edit")
def edit_sticky_note(sticky_note_id):
    sticky_note = StickyNote.query.filter(
        StickyNote.id == sticky_note_id, StickyNote.deleted_at.is_(None)
    ).first_or_404()
    return render_template(
        "sticky_notes/form.jinja", sticky_note=sticky_note, colours=STICKY_COLOURS
    )


@sticky_notes_bp.put("/<sticky_note_id>")
def update_sticky_note(sticky_note_id):
    sticky_note = StickyNote.query.filter(
        StickyNote.id == sticky_note_id, StickyNote.deleted_at.is_(None)
    ).first_or_404()

    colour = request.form.get("colour", "yellow")
    if colour not in STICKY_COLOURS:
        colour = "yellow"

    sticky_note.title = request.form.get("title", "").strip() or None
    sticky_note.content = request.form.get("content", "")
    sticky_note.colour = colour
    sticky_note.expires_at = parse_expires_at(request.form.get("expires_at"))
    sticky_note.pinned = bool(request.form.get("pinned"))
    sticky_note.updated_at = now()
    db.session.commit()
    flash("Sticky note saved.", "success")
    return redirect(url_for("sticky_notes.list_sticky_notes"), code=303)


@sticky_notes_bp.patch("/<sticky_note_id>/pin")
def toggle_pin(sticky_note_id):
    sticky_note = StickyNote.query.filter(
        StickyNote.id == sticky_note_id, StickyNote.deleted_at.is_(None)
    ).first_or_404()
    sticky_note.pinned = not sticky_note.pinned
    db.session.commit()
    flash(
        "Sticky note pinned." if sticky_note.pinned else "Sticky note unpinned.",
        "success",
    )
    return redirect(
        request.referrer or url_for("sticky_notes.list_sticky_notes"), code=303
    )


@sticky_notes_bp.delete("/<sticky_note_id>/delete")
def delete_sticky_note(sticky_note_id):
    sticky_note = StickyNote.query.get_or_404(sticky_note_id)
    sticky_note.deleted_at = now()
    db.session.commit()
    flash("Sticky note moved to trash.", "success")
    return redirect(
        request.referrer or url_for("sticky_notes.list_sticky_notes"), code=303
    )


@sticky_notes_bp.patch("/<sticky_note_id>/restore")
def restore_sticky_note(sticky_note_id):
    sticky_note = StickyNote.query.get_or_404(sticky_note_id)
    sticky_note.deleted_at = None
    db.session.commit()
    flash("Sticky note restored.", "success")
    return redirect(url_for("sticky_notes.trash"), code=303)


@sticky_notes_bp.delete("/<sticky_note_id>/purge")
def purge_sticky_note(sticky_note_id):
    sticky_note = StickyNote.query.filter(
        StickyNote.id == sticky_note_id, StickyNote.deleted_at.isnot(None)
    ).first_or_404()
    db.session.delete(sticky_note)
    db.session.commit()
    flash("Sticky note permanently deleted.", "success")
    return redirect(url_for("sticky_notes.trash"), code=303)
