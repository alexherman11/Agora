"""Pure ordered reference-list edits; permission and freshness remain the caller's ordinary world checks.

Only explicit appearance/surface/subject identities are accepted, not selections, names or URLs.
No lookup, canonicalization to another appearance, mutation, or navigation occurs here.
"""
import re

REFERENCE = re.compile(r"[afs][1-9][0-9]*")
MAX_ITEMS = 256
MAX_BYTES = 16384


def _one(value):
    if not isinstance(value, str) or not REFERENCE.fullmatch(value):
        raise ValueError("reference list needs one explicit thing identity")
    return value


def _read(raw):
    if not isinstance(raw, str) or len(raw.encode("utf-8")) > MAX_BYTES:
        raise ValueError("reference list must be bounded text")
    items = [x for x in re.split(r"[,\s]+", raw) if x]
    if len(items) > MAX_ITEMS:
        raise ValueError("reference list has more than 256 items")
    for item in items:
        _one(item)
    if len(set(items)) != len(items):
        raise ValueError("reference list contains duplicate identities")
    return items


def edit(raw, item, action, before=""):
    """Add at end, remove, or move an existing member before another (empty anchor means end).

    Semantic no-ops preserve the original spelling, so an ordinary guarded prop can avoid a write.
    Existing unrelated references retain order, including references no longer available to the caller.
    """
    items = _read(raw)
    _one(item)
    if action == "add":
        if item in items:
            return raw
        if len(items) == MAX_ITEMS:
            raise ValueError("reference list has no room for another item")
        items.append(item)
    elif action == "remove":
        if item not in items:
            return raw
        items.remove(item)
    elif action == "before":
        if item not in items or (before and _one(before) not in items):
            raise ValueError("reference-list move needs an existing member and anchor")
        if before == item:
            return raw
        moved = [x for x in items if x != item]
        moved.insert(moved.index(before) if before else len(moved), item)
        if moved == items:
            return raw
        items = moved
    else:
        raise ValueError("unknown reference-list edit")
    result = "\n".join(items)
    if len(result.encode("utf-8")) > MAX_BYTES:
        raise ValueError("reference-list result exceeds bounded text")
    return result
