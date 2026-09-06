"""mint, attach, read, place: the one write path, and the only place judgment about a write lives.
Never: never constructs an event record, never writes the store, never acts without an actor."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from kernel import (
    component_api,
    component_data,
    events,
    facets,
    imports,
    lenses,
    store,
)
from kernel.events import LogError, World
from kernel.facets import FacetError
from kernel.locking import synchronized
from kernel.schema import DEFAULT_TRANSFORM, DESK, MODES, Appearance, FacetRecord
from kernel.store import Store
from kernel.vocabulary import REGISTRY as REGISTRY


class VerbError(Exception):
    """A refused call. Instructive and side-effect-free: nothing was logged."""


def open_world(path: str | os.PathLike[str], *, import_roots=None) -> Store:
    """The client's handle on a world: a synced store over a world directory."""
    result = store.open_store(events.open_world(path))
    if import_roots is not None:
        result.import_roots = tuple(Path(p).expanduser().resolve() for p in import_roots)
    return result


def revision(world: Store) -> int:
    """How many events the world has applied. Clients poll this to notice change."""
    return world.sync()


def check_authority(world: Store, actor: str, verb: str, entity: str | None) -> None:
    """M2: authority modes per facet definition. Always allows in M1."""


def check_grants(world: Store, actor: str, verb: str, entity: str | None) -> None:
    """M2: grants from the keep. Always allows in M1."""


@synchronized
def mint(world: Store, actor: str, facets: dict[str, Any] | None = None) -> str:
    """Bring a new entity into the world, optionally with initial facets, as one intent."""
    _actor(actor)
    if facets is not None and not isinstance(facets, dict):
        raise VerbError("facets must be an object mapping facet types to bodies")
    check_authority(world, actor, "mint", None)
    check_grants(world, actor, "mint", None)
    initial, blobs = {}, []
    for facet_type, body in (facets or {}).items():
        initial[facet_type], blob = _prepare(world, facet_type, body)
        if blob is not None:
            blobs.append(blob)
    entity = events.new_id("ent")
    _append(world.world, actor, "entity-minted", {"entity": entity, "facets": initial}, blobs)
    return entity


@synchronized
def attach(
    world: Store,
    actor: str,
    entity: str,
    facet_type: str,
    body: Any,
    expected_revision: int | None = None,
) -> FacetRecord:
    """Attach a facet, or update it if the entity already carries one of that type."""
    _actor(actor)
    _exists(world, entity)
    if not isinstance(facet_type, str):
        raise VerbError("facet_type must be a string")
    check_authority(world, actor, "attach", entity)
    check_grants(world, actor, "attach", entity)
    current = world.facet(entity, facet_type)
    if expected_revision is not None and (
        type(expected_revision) is not int
        or expected_revision != (current.revision if current else 0)
    ):
        raise VerbError("stale facet revision; read the current value before changing it")
    prepared, blob = _prepare(world, facet_type, body)
    kind = "facet-attached"
    if facet_type == "core.text" and world.facet(entity, facet_type) is not None:
        kind = "text-edited"
    _append(
        world.world,
        actor,
        kind,
        {"entity": entity, "type": facet_type, "body": prepared},
        [blob] if blob is not None else [],
    )
    record = world.facet(entity, facet_type)
    assert record is not None
    return record


@synchronized
def read(
    world: Store,
    actor: str,
    entity: str,
    facet_type: str | None = None,
    revision: int | None = None,
) -> dict[str, Any]:
    """Raw facets at full fidelity. Projection is for budgets; this is for lenses."""
    _actor(actor)
    _exists(world, entity)
    check_authority(world, actor, "read", entity)
    check_grants(world, actor, "read", entity)
    if revision is not None:
        if not facet_type or type(revision) is not int or revision < 1:
            raise VerbError("historical read needs a facet_type and positive revision")
        record = world.historical(entity, facet_type, revision)
        if record is None:
            raise VerbError("no such facet revision")
        return {"entity": entity, "facets": {facet_type: _view(record)}}
    records = world.facets(entity)
    if facet_type is not None:
        records = [r for r in records if r.type == facet_type]
        if not records:
            known = [r.type for r in world.facets(entity)]
            raise VerbError(f"{entity} has no {facet_type}; it carries {known}")
    return {"entity": entity, "facets": {r.type: _view(r) for r in records}}


@synchronized
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
    if mode not in MODES:
        raise VerbError(f"mode must be one of {list(MODES)}; got {mode!r}")
    if transform is not None and not isinstance(transform, dict):
        raise VerbError("transform must be an object with x, y, and scale")
    merged = {**DEFAULT_TRANSFORM, **(transform or {})}
    try:
        facets.validate_appearance({"entity": entity, "mode": mode, "transform": merged})
    except FacetError as exc:
        raise VerbError(str(exc)) from exc
    check_authority(world, actor, "place", entity)
    check_grants(world, actor, "place", entity)
    appearances = world.appearances(scene)
    if len(appearances) >= 1000 and not any(a.entity == entity for a in appearances):
        raise VerbError("a scene is limited to 1000 appearances")
    if scene == DESK:
        ensure_desk(world, actor)
    elif world.facet(scene, "core.scene") is None:
        raise VerbError(f"{scene} is not a scene: it carries no core.scene facet")
    payload = {"scene": scene, "entity": entity, "mode": mode, "transform": merged}
    _append(world.world, actor, "appearance-placed", payload)
    return Appearance(entity, mode, merged)


@synchronized
def ensure_desk(world: Store, actor: str = "system") -> str:
    """Mint the desk scene if this world has none. Idempotent: appends nothing otherwise."""
    if world.entity(DESK) is None:
        _actor(actor)
        desk = {"entity": DESK, "facets": {"core.scene": {"appearances": []}}}
        _append(world.world, actor, "entity-minted", desk)
    return DESK


@synchronized
def preview_lens(
    world: Store,
    actor: str,
    entity: str,
    revision: int | None = None,
    selected: str | None = None,
    offset: int = 0,
) -> dict:
    """Inspect a lens and its full-fidelity preview without activating or editing it."""
    _actor(actor)
    check_authority(world, actor, "read", entity)
    check_grants(world, actor, "read", entity)
    try:
        return lenses.render(world, entity, revision, selected, offset)
    except ValueError as exc:
        raise VerbError(str(exc)) from exc


@synchronized
def activate_lens(
    world: Store,
    actor: str,
    entity: str = "",
    revision: int | None = None,
    expected_revision: int | None = None,
) -> FacetRecord:
    """Activate a validated lens revision, or return to the default desk with an empty entity."""
    _actor(actor)
    if not isinstance(entity, str):
        raise VerbError("lens entity must be a string reference, or empty for the default desk")
    current = world.facet(DESK, "core.display")
    if expected_revision is not None and (
        type(expected_revision) is not int
        or expected_revision != (current.revision if current else 0)
    ):
        raise VerbError("stale display revision; preview the current display before replacing it")
    if entity:
        preview = preview_lens(world, actor, entity, revision)
        revision = preview["revision"]
    else:
        revision = 0
    ensure_desk(world, actor)
    return attach(
        world,
        actor,
        DESK,
        "core.display",
        {"lens": entity, "revision": revision},
        expected_revision=expected_revision,
    )


# The registry: what a client may derive tools from. Never hand-written elsewhere.


VERBS = {
    "mint": mint,
    "attach": attach,
    "read": read,
    "place": place,
    "preview_lens": preview_lens,
    "activate_lens": activate_lens,
}


def facet_types() -> list[dict[str, Any]]:
    return facets.describe()


def _view(r: FacetRecord) -> dict[str, Any]:
    result = {k: getattr(r, k) for k in ("body", "revision", "written_by", "written_at")}
    if r.type == "core.text":
        result["body"] = {k: v for k, v in r.body.items() if k != "snapshot"}
    return result


def _actor(actor: Any) -> None:
    if not isinstance(actor, str) or not actor:
        raise VerbError("every verb call carries an actor: a non-empty string naming who acts")


def _exists(world: Store, entity: Any) -> None:
    if not isinstance(entity, str) or world.entity(entity) is None:
        raise VerbError(f"no entity {entity!r} in this world; mint one, or use an id from the desk")


def _prepare(world: Store, facet_type: str, body: Any):
    try:
        if facet_type in component_data.PROTECTED:
            raise ValueError("component state, test receipts, and admission are runtime-owned")
        prepared, blob = imports.prepare(facet_type, body, world.import_roots)
        if facet_type == "core.display":
            if prepared.get("kind", "lens") not in ("lens", "component"):
                raise ValueError("display kind must be lens or component")
            if prepared.get("kind") == "component":
                raise ValueError("use activate_component for executable displays")
            if prepared["lens"]:
                lenses.render(world, prepared["lens"], prepared["revision"])
            elif prepared["revision"] != 0:
                raise ValueError("the default display uses revision 0")
        return prepared, blob
    except (FacetError, ValueError, TypeError) as exc:
        raise VerbError(str(exc)) from exc


def _append(world: World, actor: str, kind: str, payload: dict[str, Any], blobs=()) -> None:
    try:
        import json

        json.dumps(payload, allow_nan=False)
        for blob in blobs:
            events.put_blob(world, blob)
        events.append(world, actor, kind, payload)
    except (LogError, ValueError, OSError) as exc:
        raise VerbError(str(exc)) from exc


# Bind once to this module's commit gateway; all component writes still enter _append.
VERBS.update(component_api.bind(_append, VerbError, _actor))
open_component_candidate = VERBS["open_component_candidate"]
candidate_event = VERBS["candidate_event"]
close_component_candidate = VERBS["close_component_candidate"]
component_view = VERBS["component_view"]
test_component = VERBS["test_component"]
activate_component = VERBS["activate_component"]
component_event = VERBS["component_event"]
component_actions = VERBS["component_actions"]
invoke_component = VERBS["invoke_component"]
