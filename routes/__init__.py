from .notes import notes_bp
from .search import search_bp
from .settings import settings_bp
from .sticky_notes import sticky_notes_bp
from .storage import storage_bp
from .todos import todos_bp


def register_routes(app):
    app.register_blueprint(notes_bp)
    app.register_blueprint(sticky_notes_bp)
    app.register_blueprint(todos_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(storage_bp)
