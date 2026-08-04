from sqlalchemy import func

from models import Note, Todo


def group_sections(items):
    ungrouped = [item for item in items if not item.group_name]
    grouped = {}
    for item in items:
        if item.group_name:
            grouped.setdefault(item.group_name, []).append(item)

    sections = []
    if ungrouped:
        sections.append(("No group", ungrouped))
    for name in sorted(grouped, key=str.lower):
        sections.append((name, grouped[name]))
    return sections


def all_group_names():
    names = set()
    for model in (Note, Todo):
        rows = (
            model.query.filter(
                ~model.deleted,
                ~model.archived,
                model.group_name.isnot(None),
            )
            .with_entities(model.group_name)
            .distinct()
        )
        names.update(name for (name,) in rows)
    return sorted(names, key=str.lower)


def find_existing_group_name(raw, exclude=None):
    for model in (Note, Todo):
        query = model.query.filter(
            ~model.deleted, func.lower(model.group_name) == raw.lower()
        )
        if exclude is not None:
            query = query.filter(model.group_name != exclude)
        match = query.with_entities(model.group_name).first()
        if match:
            return match[0]
    return None


def normalize_group_name(raw, exclude=None):
    cleaned = "".join((raw or "").split())
    if not cleaned:
        return None
    return find_existing_group_name(cleaned, exclude=exclude) or cleaned


def group_name_counts():
    counts = {}
    for model, key in ((Note, "notes"), (Todo, "todos")):
        rows = (
            model.query.filter(
                ~model.deleted,
                ~model.archived,
                model.group_name.isnot(None),
            )
            .with_entities(model.group_name, func.count())
            .group_by(model.group_name)
            .all()
        )
        for name, count in rows:
            counts.setdefault(name, {"notes": 0, "todos": 0})[key] = count
    return dict(sorted(counts.items(), key=lambda item: item[0].lower()))
