from flask import Blueprint, render_template, request

from utils.search import TYPE_ALIASES, search

search_bp = Blueprint("search", __name__, url_prefix="/search")

TYPE_FILTERS = [
    (None, "All"),
    ("todo", "Todos"),
    ("note", "Notes"),
    ("sticky", "Sticky notes"),
]

SECTION_LABELS = {"todo": "Todos", "note": "Notes", "sticky": "Sticky notes"}


def type_filters(query):
    words = query.split()
    chosen = set()
    rest = []
    for word in words:
        key, _, value = word.partition(":")
        if key.lower() == "is" and value.lower() in TYPE_ALIASES:
            chosen.add(TYPE_ALIASES[value.lower()])
        else:
            rest.append(word)

    filters = []
    for kind, label in TYPE_FILTERS:
        filter_query = " ".join(rest + [f"is:{kind}"] if kind else rest)
        current = chosen == {kind} if kind else not chosen
        filters.append({"label": label, "query": filter_query, "current": current})
    return filters


def type_sections(results):
    sections = {}
    for result in results:
        sections.setdefault(result["kind"], []).append(result)
    return [(kind, SECTION_LABELS[kind], items) for kind, items in sections.items()]


@search_bp.get("/")
def search_view():
    query = request.args.get("q", "").strip()
    results, parsed = search(query, limit=50 if query else 10)
    return render_template(
        "search.jinja",
        query=query,
        sections=type_sections(results),
        filters=type_filters(query),
        parsed=parsed,
    )
