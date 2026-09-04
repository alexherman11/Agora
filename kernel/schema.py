"""Event and facet record shapes, as data: the forever format of the log and the store.
Never: no I/O, no ids minted, no imports from the rest of the kernel; fields are only ever added."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

SCHEMA_VERSION = 1

# The well-known desk scene. M1 has one desk per world; its id is a name, not a credential.
DESK = "ent_desk"

# Event kinds and their payload shapes. Shipped fields are permanent; new fields are optional.
#   entity-minted      {"entity": id, "facets": {type: body, ...}}
#   facet-attached     {"entity": id, "type": type, "body": body}
#   text-edited        {"entity": id, "type": "core.text", "body": {"text": str, "snapshot": b64}}
#   appearance-placed  {"scene": id, "entity": id, "mode": mode, "transform": {x, y, scale}}
EVENT_KINDS = ("entity-minted", "facet-attached", "text-edited", "appearance-placed")

MODES = ("icon", "summary", "full")


@dataclass(frozen=True)
class Event:
    """One line of the log. `seq` is its position, assigned at replay, never serialized."""

    id: str
    ts: float
    actor: str
    kind: str
    payload: dict[str, Any]
    v: int = SCHEMA_VERSION
    seq: int = field(default=0, compare=False)

    def to_line(self) -> str:
        record = asdict(self)
        del record["seq"]
        return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def from_line(cls, line: str, seq: int) -> Event:
        record = json.loads(line)
        return cls(
            id=record["id"],
            ts=record["ts"],
            actor=record["actor"],
            kind=record["kind"],
            payload=record["payload"],
            v=record.get("v", SCHEMA_VERSION),
            seq=seq,
        )


@dataclass(frozen=True)
class EntityRecord:
    id: str
    minted_by: str
    minted_at: float


@dataclass(frozen=True)
class FacetRecord:
    entity: str
    type: str
    body: dict[str, Any]
    revision: int
    written_by: str
    written_at: float


@dataclass(frozen=True)
class Appearance:
    """A scene record placing an entity on a surface. Entities have no position of their own."""

    entity: str
    mode: str
    transform: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {"entity": self.entity, "mode": self.mode, "transform": dict(self.transform)}

    @classmethod
    def from_dict(cls, record: dict[str, Any]) -> Appearance:
        return cls(
            entity=record["entity"],
            mode=record.get("mode", "icon"),
            transform=dict(record.get("transform", {})),
        )


DEFAULT_TRANSFORM: dict[str, float] = {"x": 0.0, "y": 0.0, "scale": 1.0}


@dataclass(frozen=True)
class Param:
    """One verb parameter, as data, so tools can be derived from it."""

    kind: str  # "str" | "dict" | "int" | "float" | "list"
    required: bool
    doc: str


@dataclass(frozen=True)
class VerbDef:
    name: str
    doc: str
    params: dict[str, Param]
