"""select() and render_tokens(): perception at a budget, the same judgment for every consumer.
Never: never writes, never shortens away uncertainty to fit a budget, never favors a viewer."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field

from kernel import facets
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
    age: float | None = None  # seconds since the newest fact changed


def tokens(text: str) -> int:
    """No tokenizer: about four characters per token, never zero."""
    return max(1, (len(text) + 3) // 4)


def select(
    world: Store, entity: str, viewer: str = "alex", purpose: str = "context", budget: int = 60
) -> Selection:
    """Choose the attributed facts that survive at this budget. Judgment lives here only."""
    selection = Selection(entity, viewer, purpose, budget, known=world.entity(entity) is not None)
    if not selection.known:
        return selection
    records = sorted(world.facets(entity), key=lambda r: (_RANK.get(_kind(r), 3), r.type))
    remaining = budget
    for record in records:
        if purpose == "label" and _RANK.get(_kind(record), 3) > 0:
            selection.omitted.append(record.type)  # a label names; it does not summarize
            continue
        text = _render(world, record, viewer, purpose, remaining)
        attribution = tokens(f" (by {record.written_by})") if _attributed(record, viewer) else 0
        cost = tokens(text) + attribution
        truncated = False
        room = remaining - attribution
        if cost > remaining and _kind(record) == "text" and room >= _MIN_TEXT_TOKENS:
            text = _head(text, room) + "…"
            cost, truncated = tokens(text) + attribution, True
        if cost > remaining:
            selection.omitted.append(record.type)
            continue
        remaining -= cost
        selection.facts.append(
            Fact(
                record.type, text, record.written_by, record.written_at, record.revision, truncated
            )
        )
    newest = max((r.written_at for r in records), default=None)
    selection.age = (time.time() - newest) if newest is not None else None
    return selection


def render_tokens(selection: Selection) -> str:
    """Dress a selection as text. Rendering only; nothing here decides what is shown."""
    if not selection.known:
        return f"unknown entity {selection.entity}"
    if not selection.facts and not selection.omitted:
        return f"{selection.entity} (no facets)"
    parts = []
    for fact in selection.facts:
        text = fact.text
        if _attributed_by(fact.written_by, selection.viewer):
            text += f" (by {fact.written_by})"
        parts.append(text)
    if selection.omitted and selection.purpose != "label":
        parts.append(f"+{len(selection.omitted)} more: {', '.join(selection.omitted)}")
    return "; ".join(parts)  # a label is a name; its omissions are the icon's whole point


def project(world: Store, entity: str, viewer: str = "alex", budget: int = 60) -> str:
    return render_tokens(select(world, entity, viewer, "context", budget))


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
        label = render_tokens(select(world, entry["entity"], viewer, purpose, TIERS[0]))
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
