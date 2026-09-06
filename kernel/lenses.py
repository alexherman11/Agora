"""Read-only lens resolution: explicit bindings, retained definitions, and full-fidelity content.
Never: never executes lens code, writes state, or opens files or network connections."""

from kernel import lens_schema
from kernel.locking import synchronized
from kernel.schema import DESK
from kernel.store import Store


@synchronized
def render(
    world: Store,
    entity: str = "",
    revision: int | None = None,
    selected: str | None = None,
    offset: int = 0,
) -> dict:
    if (
        not isinstance(entity, str)
        or revision is not None
        and (type(revision) is not int or revision < 1)
    ):
        raise ValueError("lens needs an entity reference and a positive definition revision")
    display = world.facet(DESK, "core.display")
    if not entity:
        if display and display.body.get("kind") == "component":
            return {"active": False, "component": True, "display_revision": display.revision}
        if not display or not display.body.get("lens"):
            return {"active": False, "display_revision": display.revision if display else 0}
        entity, revision = display.body["lens"], display.body["revision"]
    record = world.facet(entity, "core.lens")
    if revision is not None and (not record or record.revision != revision):
        record = world.historical(entity, "core.lens", revision)
    if not record:
        raise ValueError("no such lens revision")
    definition = record.body
    lens_schema.validate(definition)
    source = definition["source"]
    if "scene" in source:
        if world.facet(source["scene"], "core.scene") is None:
            raise ValueError("lens source is not a scene")
        refs = [a.entity for a in world.appearances(source["scene"])]
    else:
        refs = source["entities"]
    if type(offset) is not int or offset < 0:
        raise ValueError("offset must be a nonnegative integer")
    items = []
    for ref in dict.fromkeys(refs):
        records = {r.type: r for r in world.facets(ref)}
        if not world.entity(ref) or source.get("facet") and source["facet"] not in records:
            continue
        items.append((ref, records))
    chosen = next(((ref, rs) for ref, rs in items if ref == selected), None)
    if selected is not None and chosen is None:
        raise ValueError("selected entity is outside this lens source")
    if chosen is None and items[offset:]:
        chosen = items[offset]
    listing = definition["list"]
    rows = [
        {
            "entity": ref,
            "label": _field(rs, listing["field"]) or ref,
            "secondary": [_field(rs, f) for f in listing.get("secondary", [])],
        }
        for ref, rs in items[offset : offset + 100]
    ]
    return {
        "active": True,
        "entity": entity,
        "revision": record.revision,
        "display_revision": display.revision if display else 0,
        "definition": definition,
        "rows": rows,
        "total": len(items),
        "offset": offset,
        "selected": chosen[0] if chosen else None,
        "detail": _field(chosen[1], definition["detail"]["field"]) if chosen else "",
    }


def _field(records, field):
    if field in ("written_by", "revision"):
        record = records.get("core.text") or records.get("core.name")
        return str(getattr(record, field)) if record else ""
    facet, name = field.rsplit(".", 1)
    record = records.get(facet)
    return str(record.body.get(name, "")) if record else ""
