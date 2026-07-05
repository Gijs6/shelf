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
                model.deleted_at.is_(None),
                model.archived_at.is_(None),
                model.group_name.isnot(None),
            )
            .with_entities(model.group_name)
            .distinct()
        )
        names.update(name for (name,) in rows)
    return sorted(names, key=str.lower)
