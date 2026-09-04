"""mint, attach, read, place: the one write path, and the only place judgment about a write lives.
Never: never constructs an event record, never writes the store, never acts without an actor."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from kernel import events, facets, store
from kernel.events import LogError, World
from kernel.facets import FacetError
from kernel.schema import DEFAULT_TRANSFORM, DESK, MODES, Appearance, FacetRecord, Param, VerbDef
from kernel.store import Store


class VerbError(Exception):
    """A refused call. Instructive and side-effect-free: nothing was logged."""


def open_world(path: str | os.PathLike[str]) -> Store:
    """The client's handle on a world: a synced store over a world directory."""
    return store.open_store(events.open_world(path))


def revision(world: Store) -> int:
    """How many events the world has applied. Clients poll this to notice change."""
    return world.sync()


def check_authority(world: Store, actor: str, verb: str, entity: str | None) -> None:
    """M2: authority modes per facet definition. Always allows in M1."""


def check_grants(world: Store, actor: str, verb: str, entity: str | None) -> None:
    """M2: grants from the keep. Always allows in M1."""


def mint(world: Store, actor: str, facets: dict[str, Any] | None = None) -> str:
    """Bring a new entity into the world, optionally with initial facets, as one intent."""
    _actor(actor)
    initial = {}
    for facet_type, body in (facets or {}).items():
        initial[facet_type] = _prepare(world.world, facet_type, body)
    check_authority(world, actor, "mint", None)
    check_grants(world, actor, "mint", None)
    entity = events.new_id("ent")
    _append(world.world, actor, "entity-minted", {"entity": entity, "facets": initial})
    return entity


def attach(world: Store, actor: str, entity: str, facet_type: str, body: Any) -> FacetRecord:
    """Attach a facet, or update it if the entity already carries one of that type."""
    _actor(actor)
    _exists(world, entity)
    prepared = _prepare(world.world, facet_type, body)
    check_authority(world, actor, "attach", entity)
    check_grants(world, actor, "attach", entity)
    kind = "facet-attached"
    if facet_type == "core.text" and world.facet(entity, facet_type) is not None:
        kind = "text-edited"
    _append(world.world, actor, kind, {"entity": entity, "type": facet_type, "body": prepared})
    record = world.facet(entity, facet_type)
    assert record is not None
    return record


def read(world: Store, actor: str, entity: str, facet_type: str | None = None) -> dict[str, Any]:
    """Raw facets at full fidelity. Projection is for budgets; this is for lenses."""
    _actor(actor)
    _exists(world, entity)
    check_authority(world, actor, "read", entity)
    check_grants(world, actor, "read", entity)
    records = world.facets(entity)
    if facet_type is not None:
        records = [r for r in records if r.type == facet_type]
        if not records:
            known = [r.type for r in world.facets(entity)]
            raise VerbError(f"{entity} has no {facet_type}; it carries {known}")
    return {"entity": entity, "facets": {r.type: _view(r) for r in records}}


def place(
    world: Store,
    actor: str,
    entity: str,
    mode: str = "icon",
    transform: dict[str, float] | None = None,
    scene: str = DESK,
) -> Appearance:
    """Give an entity an appearance on a scene. Placing again replaces the appearance."""
    _actor(actor)
    _exists(world, entity)
    if scene == DESK:
        ensure_desk(world, actor)
    elif world.facet(scene, "core.scene") is None:
        raise VerbError(f"{scene} is not a scene: it carries no core.scene facet")
    if mode not in MODES:
        raise VerbError(f"mode must be one of {list(MODES)}; got {mode!r}")
    merged = {**DEFAULT_TRANSFORM, **(transform or {})}
    try:
        facets.validate_appearance({"entity": entity, "mode": mode, "transform": merged})
    except FacetError as exc:
        raise VerbError(str(exc)) from exc
    check_authority(world, actor, "place", entity)
    check_grants(world, actor, "place", entity)
    payload = {"scene": scene, "entity": entity, "mode": mode, "transform": merged}
    _append(world.world, actor, "appearance-placed", payload)
    return Appearance(entity, mode, merged)


def ensure_desk(world: Store, actor: str = "system") -> str:
    """Mint the desk scene if this world has none. Idempotent: appends nothing otherwise."""
    if world.entity(DESK) is None:
        _actor(actor)
        desk = {"entity": DESK, "facets": {"core.scene": {"appearances": []}}}
        _append(world.world, actor, "entity-minted", desk)
    return DESK


# The registry: what a client may derive tools from. Never hand-written elsewhere.


def _verb(name: str, doc: str, **params: tuple[str, bool, str]) -> VerbDef:
    return VerbDef(name, doc, {k: Param(*v) for k, v in params.items()})


_ENTITY = ("str", True, "the entity id")
REGISTRY: tuple[VerbDef, ...] = (
    _verb(
        "mint",
        "Bring a new entity into the world, optionally with initial facets. Returns its id.",
        facets=("dict", False, "{facet_type: body} to attach at birth"),
    ),
    _verb(
        "attach",
        "Attach a facet to an entity, or update the one it has.",
        entity=_ENTITY,
        facet_type=("str", True, "one of the known facet types"),
        body=("dict", True, "the facet body, in that type's shape"),
    ),
    _verb(
        "read",
        "Read an entity's facets at full fidelity.",
        entity=_ENTITY,
        facet_type=("str", False, "read only this facet type"),
    ),
    _verb(
        "place",
        "Place an entity on the desk (or another scene).",
        entity=_ENTITY,
        mode=("str", False, "icon | summary | full (default icon)"),
        transform=("dict", False, "{x, y, scale}; missing keys default"),
        scene=("str", False, "scene id; defaults to the desk"),
    ),
)

VERBS = {"mint": mint, "attach": attach, "read": read, "place": place}


def facet_types() -> list[dict[str, Any]]:
    return facets.describe()


def _view(r: FacetRecord) -> dict[str, Any]:
    return {k: getattr(r, k) for k in ("body", "revision", "written_by", "written_at")}


def _actor(actor: Any) -> None:
    if not isinstance(actor, str) or not actor:
        raise VerbError("every verb call carries an actor: a non-empty string naming who acts")


def _exists(world: Store, entity: Any) -> None:
    if not isinstance(entity, str) or world.entity(entity) is None:
        raise VerbError(f"no entity {entity!r} in this world; mint one, or use an id from the desk")


def _prepare(world: World, facet_type: str, body: Any) -> dict[str, Any]:
    """Validate, then resolve any file import so the logged body is self-contained."""
    try:
        body = facets.validate(facet_type, body)
    except FacetError as exc:
        raise VerbError(str(exc)) from exc
    if facet_type == "core.text" and "path" in body:
        data = _read_file(body["path"])
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise VerbError(
                f"{body['path']} is not UTF-8 text; attach core.file-backing instead"
            ) from exc
        body = {k: v for k, v in body.items() if k != "path"} | {"text": text}
    if facet_type == "core.file-backing":
        data = _read_file(body["path"])
        body = dict(body) | {"hash": events.put_blob(world, data), "size": len(data)}
    return body


def _read_file(path: str) -> bytes:
    target = Path(path).expanduser()
    if not target.is_file():
        raise VerbError(f"no file at {path!r}; give a path to an existing file")
    return target.read_bytes()


def _append(world: World, actor: str, kind: str, payload: dict[str, Any]) -> None:
    try:
        events.append(world, actor, kind, payload)
    except LogError as exc:
        raise VerbError(str(exc)) from exc
