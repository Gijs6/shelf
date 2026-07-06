import calendar
from datetime import timedelta

from models import Todo, db, now


def advance_deadline(deadline, interval, unit):
    if unit == "day":
        return deadline + timedelta(days=interval)
    if unit == "week":
        return deadline + timedelta(weeks=interval)
    if unit == "month":
        month_index = deadline.month - 1 + interval
        year = deadline.year + month_index // 12
        month = month_index % 12 + 1
        day = min(deadline.day, calendar.monthrange(year, month)[1])
        return deadline.replace(year=year, month=month, day=day)
    raise ValueError(f"Unknown recur unit: {unit}")


def next_due_date(deadline, interval, unit):
    current_time = now().replace(tzinfo=None)
    next_deadline = advance_deadline(deadline, interval, unit)
    while next_deadline <= current_time:
        next_deadline = advance_deadline(next_deadline, interval, unit)
    return next_deadline


def process_due_recurrences():
    due = Todo.query.filter(
        Todo.recur_interval.isnot(None),
        Todo.recur_unit.isnot(None),
        Todo.deadline.isnot(None),
        Todo.deadline <= now().replace(tzinfo=None),
        Todo.deleted_at.is_(None),
    ).all()

    for todo in due:
        db.session.add(
            Todo(
                title=todo.title,
                content=todo.content,
                group_name=todo.group_name,
                deadline=next_due_date(
                    todo.deadline, todo.recur_interval, todo.recur_unit
                ),
                recur_interval=todo.recur_interval,
                recur_unit=todo.recur_unit,
            )
        )

        todo.recur_interval = None
        todo.recur_unit = None

    if due:
        db.session.commit()
