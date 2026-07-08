import markdown
from datetime import datetime, timezone
from markupsafe import Markup


def ensure_tz(dt, local=True):
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.astimezone() if local else dt.replace(tzinfo=timezone.utc)
    return dt.astimezone()


def strftime_filter(value, fmt="%d %b %Y", local=True):
    value = ensure_tz(value, local=local)
    if value is None:
        return "-"
    return value.strftime(fmt)


def isoformat_filter(value, local=True):
    value = ensure_tz(value, local=local)
    if value is None:
        return ""
    return value.isoformat()


def timeago_filter(value, local=True):
    value = ensure_tz(value, local=local)
    if value is None:
        return "never"

    now = datetime.now(timezone.utc)
    secs = int((now - value).total_seconds())
    future = secs < 0
    secs = abs(secs)

    def fmt(n, unit):
        unit = unit if n == 1 else unit + "s"
        return f"{n} {unit}"

    if secs < 10:
        return "now"

    if secs < 60:
        unit = fmt(secs, "second")
    elif secs < 3600:
        unit = fmt(secs // 60, "minute")
    elif secs < 86400:
        unit = fmt(secs // 3600, "hour")
    elif secs < 604800:
        unit = fmt(secs // 86400, "day")
    elif secs < 2629800:
        unit = fmt(secs // 604800, "week")
    elif secs < 31557600:
        unit = fmt(secs // 2629800, "month")
    else:
        unit = fmt(secs // 31557600, "year")

    return f"in {unit}" if future else f"{unit} ago"


def pluralize_filter(n, unit):
    return unit if n == 1 else unit + "s"


def markdown_filter(text):
    if not text:
        return ""
    return Markup(markdown.markdown(text, extensions=["fenced_code", "nl2br"]))


FILTERS = {
    "strftime": strftime_filter,
    "timeago": timeago_filter,
    "isoformat": isoformat_filter,
    "pluralize": pluralize_filter,
    "markdown": markdown_filter,
}


def register_filters(app):
    for name, fn in FILTERS.items():
        app.template_filter(name)(fn)
