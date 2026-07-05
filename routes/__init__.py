from .notes import notes_bp
from .sticky_notes import sticky_notes_bp
from .todos import todos_bp


def register_routes(app):
    app.register_blueprint(notes_bp)
    app.register_blueprint(sticky_notes_bp)
    app.register_blueprint(todos_bp)
