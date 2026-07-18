import markdown
import re
from datetime import datetime, timezone
from markupsafe import Markup

from utils.autolink import AutoLinkExtension
from utils.tasklist import TaskListExtension


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

    if secs < 1:
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


BLOCK_TAG_RE = re.compile(
    r"</?(?:p|h[1-6]|ul|ol|li|blockquote|pre|hr|table|thead|tbody|tr|th|td|dl|dt|dd|div)(?:\s[^>]*)?/?>"
)
LINK_TAG_RE = re.compile(r"</?a(?:\s[^>]*)?>")
ANY_TAG_RE = re.compile(r"<[^>]+>")

INLINE_MD = markdown.Markdown(extensions=[AutoLinkExtension()])


def render_inline(text, links=True):
    html = INLINE_MD.reset().convert(text)
    html = BLOCK_TAG_RE.sub(" ", html)
    if not links:
        html = LINK_TAG_RE.sub("", html)
    return " ".join(html.split())


def markdown_inline_filter(text, links=True):
    if not text:
        return ""
    return Markup(render_inline(text, links=links))


def markdown_plain_filter(text):
    if not text:
        return ""
    return Markup(" ".join(ANY_TAG_RE.sub("", render_inline(text)).split()))


def markdown_filter(text, kind=None, item_id=None):
    if not text:
        return ""
    extensions = [
        "fenced_code",
        "nl2br",
        "tables",
        "sane_lists",
        "codehilite",
        "admonition",
        AutoLinkExtension(),
        TaskListExtension(kind=kind or "", item_id=item_id or ""),
    ]
    return Markup(
        markdown.markdown(
            text,
            extensions=extensions,
            extension_configs={"codehilite": {"guess_lang": True}},
        )
    )


FILTERS = {
    "strftime": strftime_filter,
    "timeago": timeago_filter,
    "isoformat": isoformat_filter,
    "pluralize": pluralize_filter,
    "markdown": markdown_filter,
    "markdown_inline": markdown_inline_filter,
    "markdown_plain": markdown_plain_filter,
}


def register_filters(app):
    for name, fn in FILTERS.items():
        app.template_filter(name)(fn)
