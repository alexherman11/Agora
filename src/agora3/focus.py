"""One bounded read describing what deserves attention now: the world.focus snapshot.
Never include a fact without its source object id and revision; never subscribe or write.
"""

from agora3.world import Refusal

SET_FACETS = ("agent.focus-set", "focus.set")
DEPTHS = ("name", "state", "content")
MAX_ENTRIES = 8
MAX_VIEWS = 12
TEXT_HEAD = 600

SPEC = {
    "name": "world.focus",
    "description": (
        "Read a bounded snapshot of current attention: open application views and up to "
        f"{MAX_ENTRIES} focus entries. Entries come from the resident's focus object "
        "('<resident id>.focus', e.g. jeff0.focus) carrying an 'agent.focus-set' facet "
        "(entries: [{ref, depth, mode}]; depth 0-3 renders name/state/content; mode "
        "auto|pinned is the writer's partition), else the most recently changed ordinary "
        "objects. Pass 'since' (a previous watermark) to learn whether anything included "
        "changed; unchanged content is still returned, so render or skip it by the "
        "'changed' flags. Pass 'set' to read another focus object. One paginated-scale "
        "read, not a subscription; conversation messages and drafts are excluded."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "since": {"type": "integer", "minimum": 0},
            "set": {"type": "string"},
        },
        "additionalProperties": False,
    },
}


def _depth(value):
    """JEFF's stored integers 0-3 and the legacy strings both name a render tier."""
    if isinstance(value, int):
        return DEPTHS[min(max(value, 0), len(DEPTHS) - 1)]
    return value if value in DEPTHS else "state"


def _entry(obj, depth, since):
    row = {
        "id": obj["id"],
        "revision": obj["revision"],
        "event": obj["event"],
        "depth": depth,
        "changed": since is None or obj["event"] > since,
        "title": obj["facets"].get("core.title", {}).get("text"),
    }
    if depth != "name":
        row["facets"] = sorted(obj["facets"])
        row["written_by"] = obj["written_by"]
    if depth == "content":
        text = obj["facets"].get("core.text", {}).get("text")
        if isinstance(text, str):
            row["text"] = text[:TEXT_HEAD]
            row["text_truncated"] = len(text) > TEXT_HEAD
    return row


def _set_candidates(table, explicit):
    if explicit:
        return [explicit]
    resident = table.get("agora.agent.resident", {}).get("facets", {}).get("agora.agent", {})
    candidates = []
    if isinstance(resident.get("id"), str):
        candidates.append(resident["id"] + ".focus")
    candidates += ["jeff.focus", "jeff0.focus"]
    return candidates


def _selected(table, explicit):
    """The declared focus set when present, else recent ordinary objects."""
    for candidate in _set_candidates(table, explicit):
        obj = table.get(candidate)
        if obj is None:
            continue
        for facet in SET_FACETS:
            source = obj["facets"].get(facet)
            if isinstance(source, dict) and isinstance(source.get("entries"), list):
                refs = [
                    (item["ref"], _depth(item.get("depth")))
                    for item in source["entries"][:MAX_ENTRIES]
                    if isinstance(item, dict) and isinstance(item.get("ref"), str)
                ]
                header = {"set": candidate, "revision": obj["revision"], "event": obj["event"]}
                return header, refs
    recent = [
        row
        for row in table.values()
        if not row["id"].startswith("agora.")
        and not {"core.message", "core.draft"} & set(row["facets"])
        and not any(facet in row["facets"] for facet in SET_FACETS)
    ]
    recent.sort(key=lambda row: row["event"], reverse=True)
    return {"set": None, "mode": "recent"}, [(row["id"], "state") for row in recent[:MAX_ENTRIES]]


def read(gateway, args):
    since = args.get("since")
    page = gateway.world.query(limit=1000)
    table = {row["id"]: row for row in page["items"]}
    source, refs = _selected(table, args.get("set"))
    entries = []
    for ref, depth in refs:
        obj = table.get(ref)
        if obj is None:
            try:
                obj = gateway.world.get(ref)
            except Refusal:
                entries.append({"id": ref, "absent": True, "changed": False})
                continue
        entries.append(_entry(obj, depth, since))
    views = []
    for row in table.values():
        value = row["facets"].get("agora.application-view")
        if not value or not value.get("open"):
            continue
        subject = table.get(value["subject"], {})
        views.append(
            {
                "id": row["id"],
                "event": row["event"],
                "package": value["package"],
                "subject": value["subject"],
                "subject_title": subject.get("facets", {}).get("core.title", {}).get("text"),
                "changed": since is None or row["event"] > since,
            }
        )
    views.sort(key=lambda row: row["event"], reverse=True)
    views = views[:MAX_VIEWS]
    changed = (
        since is None
        or any(entry.get("changed") for entry in entries)
        or any(view["changed"] for view in views)
        or (source.get("event") or 0) > since
    )
    return {
        "watermark": page["watermark"],
        "since": since,
        "changed": changed,
        "source": source,
        "complete_scan": page["complete"],
        "views": views,
        "entries": entries,
    }
