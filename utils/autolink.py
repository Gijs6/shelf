import xml.etree.ElementTree as etree

from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor


BARE_URL_RE = r"https?://[^\s<>\[\]\"']+"

TRAILING_PUNCTUATION = ".,;:!?)]}\"'"


class BareLinkInlineProcessor(InlineProcessor):
    def handleMatch(self, m, data):
        url = m.group(0)
        while url:
            last = url[-1]
            if last not in TRAILING_PUNCTUATION:
                break
            if last == ")" and url.count("(") >= url.count(")"):
                break
            url = url[:-1]

        if not url:
            return None, None, None

        el = etree.Element("a")
        el.set("href", url)
        el.text = url
        return el, m.start(0), m.start(0) + len(url)


class AutoLinkExtension(Extension):
    def extendMarkdown(self, md):
        md.inlinePatterns.register(
            BareLinkInlineProcessor(BARE_URL_RE, md), "bare_link", 50
        )
