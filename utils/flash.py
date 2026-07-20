from flask import flash


def flash_with_undo(message, undo_url, undo_method="PATCH", category="success"):
    flash({"text": message, "undo_url": undo_url, "undo_method": undo_method}, category)
