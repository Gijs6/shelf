from urllib.parse import urlsplit

DISPLAY_URL_LENGTH = 60


def normalize_url(raw):
    url = (raw or "").strip()
    if not url:
        return None
    if "://" not in url:
        url = f"https://{url}"
    parts = urlsplit(url)
    if parts.scheme.lower() not in ("http", "https") or not parts.hostname:
        return None
    return url


def display_url(url, length=DISPLAY_URL_LENGTH):
    parts = urlsplit(url or "")
    text = (parts.netloc + parts.path).removeprefix("www.").rstrip("/")
    if length and len(text) > length:
        return text[:length].rstrip() + "…"
    return text
