from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from models import db


MIGRATIONS = [
    "ALTER TABLE sticky_note ADD COLUMN deleted_at DATETIME",
    "ALTER TABLE todo DROP COLUMN recur_interval",
    "ALTER TABLE todo DROP COLUMN recur_unit",
    "ALTER TABLE todo DROP COLUMN notify_before_days",
]


def run_migrations():
    for statement in MIGRATIONS:
        try:
            db.session.execute(text(statement))
            db.session.commit()
        except OperationalError:
            db.session.rollback()
