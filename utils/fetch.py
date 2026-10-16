from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

TIMEOUT = 5
MAX_PAGE_BYTES = 1024 * 1024
MAX_ICON_BYTES = 256 * 1024
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Shelf/1.0)",
    "Accept-Language": "en-GB,en;q=0.8,nl;q=0.6",
}
TITLE_LENGTH = 200
ICON_TYPES = {
    "svg": "image/svg+xml",
    "png": "image/png",
    "ico": "image/x-icon",
    "gif": "image/gif",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
}


def get(url, limit):
    try:
        with requests.get(
            url, headers=HEADERS, timeout=TIMEOUT, stream=True
        ) as response:
            if not response.ok:
                return None
            body = b""
            for chunk in response.iter_content(16384):
                body += chunk
                if len(body) > limit:
                    return None
            return response.url, response.headers.get("Content-Type", ""), body
    except (requests.RequestException, ValueError):
        return None


def fetch_page(url):
    result = get(url, MAX_PAGE_BYTES)
    if result is None:
        return url, None
    final_url, content_type, body = result
    if "html" not in content_type.lower():
        return final_url, None
    return final_url, BeautifulSoup(body, "html.parser")


def page_title(soup):
    if soup is None:
        return None
    meta = soup.find("meta", property="og:title")
    title = meta.get("content") if meta else None
    if not title and soup.title:
        title = soup.title.get_text()
    title = " ".join((title or "").split())
    return title[:TITLE_LENGTH] or None


def fetch_title(url):
    _, soup = fetch_page(url)
    return page_title(soup)


def icon_size(link):
    sizes = (link.get("sizes") or "").lower()
    if sizes == "any":
        return 10_000
    best = 0
    for size in sizes.split():
        width, _, _ = size.partition("x")
        if width.isdigit():
            best = max(best, int(width))
    return best


def icon_rank(link):
    rels = [rel.lower() for rel in link.get("rel") or []]
    href = link["href"].lower().split("?", 1)[0]
    is_svg = link.get("type") == "image/svg+xml" or href.endswith(".svg")
    return (is_svg, "icon" in rels, icon_size(link))


def icon_candidates(page_url, soup):
    links = []
    if soup is not None:
        for link in soup.find_all("link", href=True):
            rels = [rel.lower() for rel in link.get("rel") or []]
            if "mask-icon" in rels or not any("icon" in rel for rel in rels):
                continue
            if link["href"].startswith("data:"):
                continue
            links.append(link)
    links.sort(key=icon_rank, reverse=True)
    urls = [urljoin(page_url, link["href"]) for link in links]
    urls.append(urljoin(page_url, "/favicon.ico"))
    return list(dict.fromkeys(urls))


def icon_mime(url, content_type):
    mime = content_type.split(";", 1)[0].strip().lower()
    if mime.startswith("image/"):
        return mime
    extension = url.lower().split("?", 1)[0].rsplit(".", 1)[-1]
    return ICON_TYPES.get(extension)


def fetch_favicon(url):
    page_url, soup = fetch_page(url)
    for icon_url in icon_candidates(page_url, soup):
        result = get(icon_url, MAX_ICON_BYTES)
        if result is None:
            continue
        final_url, content_type, body = result
        mime = icon_mime(final_url, content_type)
        if body and mime:
            return body, mime
    return None
