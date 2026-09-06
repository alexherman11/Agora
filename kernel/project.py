"""select() and render_tokens(): perception at a budget, the same judgment for every consumer.
Never: never writes, never shortens away uncertainty to fit a budget, never favors a viewer."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field

from kernel import facets, lenses
from kernel.locking import synchronized
from kernel.schema import FacetRecord
from kernel.store import Store

TIERS = (12, 60, 250, 2000)
_RANK = {"name": 0, "scene": 0, "file": 1, "text": 2, "generic": 3}
_MIN_TEXT_TOKENS = 4


@dataclass(frozen=True)
class Fact:
    facet: str
    text: str
    written_by: str
    written_at: float
    revision: int
    truncated: bool = False


@dataclass
class Selection:
    entity: str
    viewer: str
    purpose: str
    budget: int
    known: bool
    facts: list[Fact] = field(default_factory=list)
    omitted: list[str] = field(default_factory=list)
    rendered: str = ""
    age: float | None = None  # seconds since the newest fact changed


def tokens(text: str) -> int:
    """No tokenizer: about four characters per token, never zero."""
    return max(1, (len(text) + 3) // 4)


@synchronized
def select(
    world: Store, entity: str, viewer: str = "alex", purpose: str = "context", budget: int = 60
) -> Selection:
    """Select and budget the complete wire representation, including omissions."""
    if type(budget) is not int or budget < 1:
        raise ValueError("budget must be a positive integer")
    selection = Selection(entity, viewer, purpose, budget, known=world.entity(entity) is not None)
    if not selection.known:
        selection.rendered = _bounded(f"unknown entity {entity}", budget * 4)
        return selection
    records = sorted(world.facets(entity), key=lambda r: (_RANK.get(_kind(r), 3), r.type))
    parts = []
    for index, record in enumerate(records):
        kind = _kind(record)
        if purpose == "label" and kind != "name":
            selection.omitted.append(record.type)
            continue
        suffix = f" (by {record.written_by})" if _attributed(record, viewer) else ""
        reserve = (
            len(f"; +{len(records)} more")
            if purpose != "label" and (index < len(records) - 1 or selection.omitted)
            else 0
        )
        room = budget * 4 - len("; ".join(parts)) - (2 if parts else 0) - reserve - len(suffix)
        text = _render(world, record, viewer, purpose, max(1, room // 4))
        truncated = False
        if len(text) > room and kind in ("name", "text", "scene") and room >= 4:
            text, truncated = _bounded(text, room), True
        if not text or len(text) > room:
            selection.omitted.append(record.type)
            continue
        parts.append(text + suffix)
        selection.facts.append(
            Fact(
                record.type, text, record.written_by, record.written_at, record.revision, truncated
            )
        )
    if selection.omitted and purpose != "label":
        marker = f"+{len(selection.omitted)} more"
        candidate = "; ".join(parts + [marker])
        if len(candidate) <= budget * 4:
            parts.append(marker)
    selection.rendered = "; ".join(parts) or _bounded(entity, budget * 4)
    newest = max((r.written_at for r in records), default=None)
    selection.age = time.time() - newest if newest is not None else None
    return selection


def _bounded(text: str, chars: int) -> str:
    return text if len(text) <= chars else text[: max(0, chars - 1)].rstrip() + "…"


def render_tokens(selection: Selection) -> str:
    """Rendering contains no independent selection policy."""
    return selection.rendered


def project(world: Store, entity: str, viewer: str = "alex", budget: int = 60) -> str:
    return render_tokens(select(world, entity, viewer, "context", budget))


def lens(
    world: Store,
    entity: str = "",
    revision: int | None = None,
    selected: str | None = None,
    offset: int = 0,
) -> dict:
    return lenses.render(world, entity, revision, selected, offset)


# -- per-facet rendering ---------------------------------------------------------------


def _render(world: Store, record: FacetRecord, viewer: str, purpose: str, budget: int) -> str:
    body = record.body
    match _kind(record):
        case "name":
            return str(body.get("name", ""))
        case "text":
            return " ".join(str(body.get("text", "")).split())
        case "file":
            size = body.get("size")
            name = os.path.basename(str(body.get("path", "")))
            return f"file {name}" + (f" ({size} bytes)" if size is not None else "")
        case "scene":
            return _render_scene(world, body.get("appearances", []), viewer, purpose, budget)
        case _:
            return f"{record.type} {json.dumps(body, sort_keys=True)}"


def _render_scene(
    world: Store, appearances: list[dict], viewer: str, purpose: str, budget: int
) -> str:
    count = len(appearances)
    if count == 0:
        return "an empty desk"
    lead = f"desk with {count} item{'s' if count != 1 else ''}: "
    names, spent = [], tokens(lead)
    for entry in appearances:
        label = render_tokens(select(world, entry["entity"], viewer, "label", TIERS[0]))
        item = f"{label} [{entry['entity']}]"
        if spent + tokens(item) > budget:
            break
        names.append(item)
        spent += tokens(item)
    if len(names) < count:
        names.append(f"+{count - len(names)} more")
    return lead + ", ".join(names)


def _kind(record: FacetRecord) -> str:
    fdef = facets.REGISTRY.get(record.type)
    return fdef.projection if fdef else "generic"


def _attributed(record: FacetRecord, viewer: str) -> bool:
    return _attributed_by(record.written_by, viewer)


def _attributed_by(writer: str, viewer: str) -> bool:
    """Day-one trust classes: from the viewer, or not. Everything else names its source."""
    return writer != viewer


def _head(text: str, budget: int) -> str:
    """At most budget*4 - 1 characters, so that head + '…' still fits the budget."""
    return text[: max(0, budget * 4 - 1)].rstrip()
