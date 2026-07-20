import secrets
import string
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
from sqlalchemy.ext.hybrid import hybrid_property


db = SQLAlchemy()

STICKY_COLOURS = ["yellow", "pink", "blue", "green", "purple", "orange"]
TODO_STATES = ["shelved", "open", "active", "done", "cancelled"]
SNIPPET_LENGTH = 80

ID_LENGTH = 8


def generate_id():
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(ID_LENGTH))


def now():
    return datetime.now(timezone.utc)


def make_snippet(content, length=SNIPPET_LENGTH):
    first_line = (content or "").split("\n", 1)[0]
    text = " ".join(first_line.split())
    if len(text) <= length:
        return text
    return text[:length].rstrip() + "…"


class Setting(db.Model):
    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.String(200), nullable=True)


class Note(db.Model):
    id = db.Column(db.String(ID_LENGTH), primary_key=True, default=generate_id)
    title = db.Column(db.String(200), nullable=True)
    content = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now)
    group_name = db.Column(db.String(100), nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    archived_at = db.Column(db.DateTime, nullable=True)

    @hybrid_property
    def deleted(self):
        return self.deleted_at is not None

    @deleted.expression
    def deleted(cls):
        return cls.deleted_at.isnot(None)

    @hybrid_property
    def archived(self):
        return self.archived_at is not None

    @archived.expression
    def archived(cls):
        return cls.archived_at.isnot(None)

    @property
    def snippet(self):
        return make_snippet(self.content)

    @property
    def display_title(self):
        return self.title or self.snippet or "Untitled"

    @property
    def kind(self):
        return "note"


class StickyNote(db.Model):
    id = db.Column(db.String(ID_LENGTH), primary_key=True, default=generate_id)
    title = db.Column(db.String(200), nullable=True)
    content = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now)
    expires_at = db.Column(db.DateTime, nullable=True)
    colour = db.Column(db.String(20), nullable=False, default="yellow")
    pinned = db.Column(db.Boolean, nullable=False, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    @hybrid_property
    def expired(self):
        return (
            not self.pinned
            and self.expires_at is not None
            and self.expires_at < datetime.now()
        )

    @expired.expression
    def expired(cls):
        return and_(
            cls.pinned.is_(False),
            cls.expires_at.isnot(None),
            cls.expires_at < datetime.now(),
        )

    @hybrid_property
    def deleted(self):
        return self.deleted_at is not None

    @deleted.expression
    def deleted(cls):
        return cls.deleted_at.isnot(None)

    @property
    def display_title(self):
        return self.title or make_snippet(self.content) or "Untitled"

    @property
    def kind(self):
        return "sticky"


class Todo(db.Model):
    id = db.Column(db.String(ID_LENGTH), primary_key=True, default=generate_id)
    title = db.Column(db.String(200), nullable=True)
    content = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now)
    state = db.Column(db.String(20), nullable=False, default="open")
    completed_at = db.Column(db.DateTime, nullable=True)
    active_at = db.Column(db.DateTime, nullable=True)
    group_name = db.Column(db.String(100), nullable=True)
    deadline = db.Column(db.DateTime, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    archived_at = db.Column(db.DateTime, nullable=True)

    @hybrid_property
    def deleted(self):
        return self.deleted_at is not None

    @deleted.expression
    def deleted(cls):
        return cls.deleted_at.isnot(None)

    @hybrid_property
    def archived(self):
        return self.archived_at is not None

    @archived.expression
    def archived(cls):
        return cls.archived_at.isnot(None)

    @property
    def snippet(self):
        return make_snippet(self.content)

    @property
    def display_title(self):
        return self.title or self.snippet or "Untitled"

    @hybrid_property
    def overdue(self):
        return (
            self.deadline is not None
            and self.state not in ("done", "cancelled")
            and self.deadline < datetime.now()
        )

    @overdue.expression
    def overdue(cls):
        return and_(
            cls.deadline.isnot(None),
            cls.state.notin_(["done", "cancelled"]),
            cls.deadline < datetime.now(),
        )

    @property
    def kind(self):
        return "todo"
