from datetime import datetime, timezone


def now():
    return datetime.now(timezone.utc)


def now_naive():
    return now().replace(tzinfo=None)


def parse_local_datetime(raw):
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def local_to_utc(dt):
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def utc_to_local(dt):
    if dt is None:
        return None
    return dt.replace(tzinfo=timezone.utc).astimezone()


def as_utc(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def utc_isoformat(dt):
    dt = as_utc(dt)
    return dt.isoformat() if dt is not None else None


def parse_utc_datetime(value):
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    return as_utc(parsed).replace(tzinfo=None)
