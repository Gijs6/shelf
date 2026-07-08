from flask import abort, render_template, request

from models import db, now
from utils.tasklist import toggle_checkbox


def toggle_item_checkbox(item, show_updated_at=False):
    try:
        index = int(request.args.get("index", ""))
    except ValueError:
        abort(400)

    item.content = toggle_checkbox(item.content, index)
    item.updated_at = now()
    db.session.commit()

    if show_updated_at:
        return render_template("partials/updated_at_oob.jinja", item=item)
    return "", 204
