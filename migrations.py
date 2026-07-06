from sqlalchemy import inspect, text

from models import Todo, db


PENDING_COLUMNS = [
    (Todo, "notify_before_days", "INTEGER"),
]


def run_migrations():
    inspector = inspect(db.engine)
    for model, column_name, column_type in PENDING_COLUMNS:
        existing = {col["name"] for col in inspector.get_columns(model.__tablename__)}
        if column_name not in existing:
            db.session.execute(
                text(
                    f"ALTER TABLE {model.__tablename__} ADD COLUMN {column_name} {column_type}"
                )
            )
    db.session.commit()
