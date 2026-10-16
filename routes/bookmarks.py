from flask import (
    Blueprint,
    Response,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from datetime import timedelta
from urllib.parse import urlsplit

from markupsafe import escape

from models import Bookmark, db, now, now_naive
from utils.fetch import fetch_favicon, fetch_title
from utils.flash import flash_with_undo
from utils.urls import normalize_url

bookmarks_bp = Blueprint("bookmarks", __name__, url_prefix="/bookmarks")

FAVICON_MAX_AGE = timedelta(days=30)
FAVICON_HEADERS = {
    "Cache-Control": "private, max-age=86400",
    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; sandbox",
    "X-Content-Type-Options": "nosniff",
}
PLACEHOLDER_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">'
    '<rect width="16" height="16" fill="#8884"/>'
    '<text x="8" y="12" font-family="sans-serif" font-size="11" '
    'text-anchor="middle" fill="#888">{letter}</text>'
    "</svg>"
)


def form_values():
    raw_url = request.form.get("url", "").strip()
    return (
        raw_url,
        normalize_url(raw_url),
        request.form.get("title", "").strip() or None,
        request.form.get("description", ""),
    )


def warn_if_duplicate(bookmark):
    existing = Bookmark.query.filter(
        Bookmark.url == bookmark.url, Bookmark.id != bookmark.id, ~Bookmark.deleted
    ).first()
    if existing:
        flash(
            f'You already bookmarked this URL as "{escape(existing.display_title)}".',
            "warning",
        )


def reset_favicon(bookmark):
    bookmark.favicon = None
    bookmark.favicon_mime = None
    bookmark.favicon_fetched_at = None


@bookmarks_bp.get("/")
def list_bookmarks():
    bookmarks = (
        Bookmark.query.filter(~Bookmark.deleted)
        .order_by(Bookmark.created_at.desc())
        .all()
    )
    return render_template("bookmarks/list.jinja", bookmarks=bookmarks)


@bookmarks_bp.get("/new")
def new_bookmark():
    return render_template("bookmarks/form.jinja", bookmark=None)


@bookmarks_bp.get("/title")
def prefill_title():
    if request.args.get("title", "").strip():
        return "", 204
    url = normalize_url(request.args.get("url"))
    title = fetch_title(url) if url else None
    if not title:
        return "", 204
    return render_template("bookmarks/title_input.jinja", title=title)


@bookmarks_bp.post("/")
def create_bookmark():
    raw_url, url, title, description = form_values()

    if not url:
        flash("Enter a valid http(s) URL.", "error")
        bookmark = Bookmark(url=raw_url, title=title, description=description)
        return render_template("bookmarks/form.jinja", bookmark=bookmark), 400

    bookmark = Bookmark(url=url, title=title, description=description)
    db.session.add(bookmark)
    db.session.commit()
    warn_if_duplicate(bookmark)
    flash("Bookmark added.", "success")
    return redirect(
        url_for("bookmarks.view_bookmark", bookmark_id=bookmark.id), code=303
    )


@bookmarks_bp.get("/<bookmark_id>")
def view_bookmark(bookmark_id):
    bookmark = Bookmark.query.filter(
        Bookmark.id == bookmark_id, ~Bookmark.deleted
    ).first_or_404()
    return render_template("bookmarks/view.jinja", bookmark=bookmark)


@bookmarks_bp.get("/<bookmark_id>/favicon")
def favicon(bookmark_id):
    bookmark = Bookmark.query.get_or_404(bookmark_id)

    fetched_at = bookmark.favicon_fetched_at
    if fetched_at is None or now_naive() - fetched_at > FAVICON_MAX_AGE:
        result = fetch_favicon(bookmark.url)
        if result:
            bookmark.favicon, bookmark.favicon_mime = result
        bookmark.favicon_fetched_at = now()
        db.session.commit()

    if bookmark.favicon:
        return Response(
            bookmark.favicon, mimetype=bookmark.favicon_mime, headers=FAVICON_HEADERS
        )

    host = (urlsplit(bookmark.url).hostname or "?").removeprefix("www.")
    svg = PLACEHOLDER_SVG.format(letter=escape(host[0].upper()))
    return Response(svg, mimetype="image/svg+xml", headers=FAVICON_HEADERS)


@bookmarks_bp.get("/<bookmark_id>/edit")
def edit_bookmark(bookmark_id):
    bookmark = Bookmark.query.filter(
        Bookmark.id == bookmark_id, ~Bookmark.deleted
    ).first_or_404()
    return render_template("bookmarks/form.jinja", bookmark=bookmark)


@bookmarks_bp.put("/<bookmark_id>")
def update_bookmark(bookmark_id):
    bookmark = Bookmark.query.filter(
        Bookmark.id == bookmark_id, ~Bookmark.deleted
    ).first_or_404()

    raw_url, url, title, description = form_values()

    if not url:
        flash("Enter a valid http(s) URL.", "error")
        bookmark.url = raw_url
        bookmark.title = title
        bookmark.description = description
        return render_template("bookmarks/form.jinja", bookmark=bookmark), 400

    url_changed = url != bookmark.url
    if url_changed:
        bookmark.url = url
        reset_favicon(bookmark)
    bookmark.title = title
    bookmark.description = description
    bookmark.updated_at = now()
    db.session.commit()
    if url_changed:
        warn_if_duplicate(bookmark)
    flash("Bookmark saved.", "success")
    return redirect(
        url_for("bookmarks.view_bookmark", bookmark_id=bookmark.id), code=303
    )


@bookmarks_bp.delete("/<bookmark_id>")
def delete_bookmark(bookmark_id):
    bookmark = Bookmark.query.get_or_404(bookmark_id)
    bookmark.deleted_at = now()
    db.session.commit()
    flash_with_undo(
        "Bookmark deleted.",
        url_for("bookmarks.restore_bookmark", bookmark_id=bookmark.id),
    )
    return redirect(url_for("bookmarks.list_bookmarks"), code=303)


@bookmarks_bp.patch("/<bookmark_id>/restore")
def restore_bookmark(bookmark_id):
    bookmark = Bookmark.query.get_or_404(bookmark_id)
    bookmark.deleted_at = None
    db.session.commit()
    flash_with_undo(
        "Bookmark restored.",
        url_for("bookmarks.delete_bookmark", bookmark_id=bookmark.id),
        undo_method="DELETE",
    )
    return redirect(url_for("storage.trash"), code=303)


@bookmarks_bp.delete("/<bookmark_id>/purge")
def purge_bookmark(bookmark_id):
    bookmark = Bookmark.query.filter(
        Bookmark.id == bookmark_id, Bookmark.deleted
    ).first_or_404()
    db.session.delete(bookmark)
    db.session.commit()
    flash("Bookmark purged.", "success")
    return redirect(url_for("storage.trash"), code=303)
