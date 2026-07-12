from datetime import timezone

from icalendar import Calendar, Event

from models import now


def to_utc(dt):
    if dt.tzinfo is None:
        dt = dt.astimezone()
    return dt.astimezone(timezone.utc)


def build_todo_calendar(todos):
    calendar = Calendar()
    calendar.add("version", "2.0")
    calendar.add("prodid", "-//Shelf//Todos//EN")
    calendar.add("calscale", "GREGORIAN")
    calendar.add("method", "PUBLISH")
    calendar.add("x-wr-calname", "Shelf todos")

    stamp = to_utc(now())
    for todo in todos:
        event = Event()
        event.add("uid", f"{todo.id}@shelf")
        event.add("dtstamp", stamp)
        deadline = to_utc(todo.deadline)
        event.add("dtstart", deadline)
        event.add("dtend", deadline)
        event.add("summary", todo.display_title)
        if todo.group_name:
            event.add("categories", todo.group_name)
        if todo.content.strip():
            event.add("description", todo.content)
        calendar.add_component(event)

    return calendar.to_ical().decode("utf-8")
