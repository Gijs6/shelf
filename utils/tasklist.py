import re
import xml.etree.ElementTree as etree

from flask import url_for
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor


TASK_MARKER_RE = re.compile(r"^\[([ xX])\]\s?(.*)$", re.DOTALL)

FENCE_RE = re.compile(r"^\s*(```|~~~)")
CHECKBOX_LINE_RE = re.compile(
    r"^(?P<indent>\s*)(?P<bullet>[-*+]|\d+[.)])\s+\[(?P<mark>[ xX])\](?P<rest>\s.*|)$"
)

CHECKBOX_ENDPOINTS = {
    "note": ("notes.toggle_note_checkbox", "note_id"),
    "todo": ("todos.toggle_todo_checkbox", "todo_id"),
    "sticky": ("sticky_notes.toggle_sticky_note_checkbox", "sticky_note_id"),
}


class TaskListTreeprocessor(Treeprocessor):
    def __init__(self, md, kind, item_id):
        super().__init__(md)
        self.kind = kind
        self.item_id = item_id

    def run(self, root):
        index = 0
        for parent in root.iter():
            if parent.tag not in ("ul", "ol"):
                continue
            has_task = False
            for li in list(parent):
                if li.tag != "li" or not li.text:
                    continue
                match = TASK_MARKER_RE.match(li.text)
                if not match:
                    continue

                mark, rest = match.groups()
                checkbox = etree.Element("input")
                checkbox.set("type", "checkbox")
                checkbox.set("class", "task-list__checkbox")
                if mark.lower() == "x":
                    checkbox.set("checked", "checked")

                if self.kind and self.item_id and self.kind in CHECKBOX_ENDPOINTS:
                    endpoint, url_kwarg = CHECKBOX_ENDPOINTS[self.kind]
                    url = url_for(endpoint, **{url_kwarg: self.item_id})
                    checkbox.set("hx-patch", f"{url}?index={index}")
                    checkbox.set("hx-trigger", "change")
                    checkbox.set("hx-swap", "none")
                else:
                    checkbox.set("disabled", "disabled")

                li.set("class", f"{li.get('class', '')} task-list__item".strip())
                li.text = None
                checkbox.tail = f" {rest}" if rest else " "
                li.insert(0, checkbox)
                index += 1
                has_task = True

            if has_task:
                parent.set("class", f"{parent.get('class', '')} task-list".strip())

        return root


class TaskListExtension(Extension):
    def __init__(self, **kwargs):
        self.config = {
            "kind": ["", "Item kind for the checkbox toggle endpoint"],
            "item_id": ["", "Item id for the checkbox toggle endpoint"],
        }
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        kind = self.getConfig("kind")
        item_id = self.getConfig("item_id")
        md.treeprocessors.register(
            TaskListTreeprocessor(md, kind, item_id), "task_list", 5
        )


def iter_checkbox_lines(content):
    in_fence = False
    fence_marker = None
    for i, line in enumerate(content.splitlines()):
        fence_match = FENCE_RE.match(line)
        if fence_match:
            marker = fence_match.group(1)
            if not in_fence:
                in_fence, fence_marker = True, marker
            elif marker == fence_marker:
                in_fence, fence_marker = False, None
            continue
        if in_fence:
            continue
        match = CHECKBOX_LINE_RE.match(line)
        if match:
            yield i, match


def toggle_checkbox(content, index):
    lines = content.splitlines()
    count = 0
    for i, match in iter_checkbox_lines(content):
        if count == index:
            new_mark = " " if match.group("mark").lower() == "x" else "x"
            start, end = match.span("mark")
            lines[i] = lines[i][:start] + new_mark + lines[i][end:]
            return "\n".join(lines)
        count += 1
    return content
