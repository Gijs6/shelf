from datetime import timezone

from models import now


def escape_ics_text(text):
    text = text or ""
    text = text.replace("\\", "\\\\")
    text = text.replace(";", "\\;")
    text = text.replace(",", "\\,")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.replace("\n", "\\n")


def fold_line(line):
    if len(line) <= 75:
        return line
    parts = [line[:75]]
    rest = line[75:]
    while rest:
        parts.append(" " + rest[:74])
        rest = rest[74:]
    return "\r\n".join(parts)


def format_ics_datetime(dt, utc=False):
    if utc:
        return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return dt.strftime("%Y%m%dT%H%M%S")


def build_todo_calendar(todos):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Shelf//Todos//EN",
        "CALSCALE:GREGORIAN",
    ]
    stamp = format_ics_datetime(now(), utc=True)
    for todo in todos:
        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{todo.id}@shelf")
        lines.append(f"DTSTAMP:{stamp}")
        lines.append(f"DTSTART:{format_ics_datetime(todo.deadline)}")
        lines.append(f"SUMMARY:{escape_ics_text(todo.display_title)}")
        if todo.group_name:
            lines.append(f"CATEGORIES:{escape_ics_text(todo.group_name)}")
        if todo.content.strip():
            lines.append(f"DESCRIPTION:{escape_ics_text(todo.content)}")
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")

    return "\r\n".join(fold_line(line) for line in lines) + "\r\n"
