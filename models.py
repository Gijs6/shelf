import secrets
import string

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import validates

from utils.datetimes import as_utc, now, now_naive
from utils.urls import display_url

db = SQLAlchemy()

STICKY_COLOURS = ["yellow", "pink", "blue", "green", "purple", "orange"]
TODO_STATES = ["shelved", "open", "active", "done", "cancelled"]
SNIPPET_LENGTH = 80

ID_LENGTH = 8


def generate_id():
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(ID_LENGTH))


def normalize_group_name_value(value):
    if value is None:
        return None
    return "".join(value.split()) or None


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

    @validates("group_name")
    def validate_group_name(self, key, value):
        return normalize_group_name_value(value)

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
    content = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now)
    colour = db.Column(db.String(20), nullable=False, default="yellow")
    pinned = db.Column(db.Boolean, nullable=False, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    @hybrid_property
    def deleted(self):
        return self.deleted_at is not None

    @deleted.expression
    def deleted(cls):
        return cls.deleted_at.isnot(None)

    @property
    def display_title(self):
        return make_snippet(self.content) or "Untitled"

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

    @validates("group_name")
    def validate_group_name(self, key, value):
        return normalize_group_name_value(value)

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
            and self.deadline < now_naive()
        )

    @overdue.expression
    def overdue(cls):
        return and_(
            cls.deadline.isnot(None),
            cls.state.notin_(["done", "cancelled"]),
            cls.deadline < now_naive(),
        )

    @property
    def kind(self):
        return "todo"


class Bookmark(db.Model):
    id = db.Column(db.String(ID_LENGTH), primary_key=True, default=generate_id)
    url = db.Column(db.String(2000), nullable=False)
    title = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now)
    favicon = db.Column(db.LargeBinary, nullable=True)
    favicon_mime = db.Column(db.String(100), nullable=True)
    favicon_fetched_at = db.Column(db.DateTime, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    @hybrid_property
    def deleted(self):
        return self.deleted_at is not None

    @deleted.expression
    def deleted(cls):
        return cls.deleted_at.isnot(None)

    @property
    def display_url(self):
        return display_url(self.url)

    @property
    def snippet(self):
        return make_snippet(self.description)

    @property
    def display_title(self):
        return self.title or display_url(self.url, length=None)

    @property
    def favicon_version(self):
        if self.favicon_fetched_at is None:
            return 0
        return int(as_utc(self.favicon_fetched_at).timestamp())

    @property
    def kind(self):
        return "bookmark"
