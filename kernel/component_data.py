"""Resolve pinned component definitions, scoped inputs, and admitted versions.
Never: never executes code, grants authority from a claim, or writes world state."""

import hashlib
import json

from kernel import component_schema
from kernel.schema import DESK

PROTECTED = {"core.component-test", "core.component-admission", "core.component-state"}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def definition(world, entity, revision=None):
    if (
        not isinstance(entity, str)
        or revision is not None
        and (type(revision) is not int or revision < 1)
    ):
        raise ValueError("component needs an entity reference and positive revision")
    record = world.facet(entity, "core.component")
    if revision is not None and (not record or record.revision != revision):
        record = world.historical(entity, "core.component", revision)
    if not record:
        raise ValueError("no such executable component revision")
    component_schema.validate(record.body)
    return record


def admitted(world, entity, revision):
    record = definition(world, entity, revision)
    admission = world.facet(entity, "core.component-admission")
    if not admission or digest(record.body) not in admission.body["definitions"]:
        raise ValueError("component revision has not passed candidate testing and activation")
    return record


def context(world, record, local=None, viewport=None):
    objects = {}
    for ref, types in record.body["bindings"].items():
        if world.entity(ref) is None:
            raise ValueError(f"component binding is missing: {ref}")
        facets = {}
        for type_ in types:
            facet = world.facet(ref, type_)
            if not facet:
                raise ValueError(f"component binding {ref} lacks {type_}")
            facets[type_] = {
                "body": {k: v for k, v in facet.body.items() if k != "snapshot"},
                "revision": facet.revision,
                "written_by": facet.written_by,
            }
        objects[ref] = {"entity": ref, "facets": facets}
    saved = world.facet(record.entity, "core.component-state")
    state = saved.body["data"] if saved else record.body["initial_state"]
    component_schema.shape(record.body["state_schema"], state)
    local = {} if local is None else local
    if not isinstance(local, dict):
        raise ValueError("local state must be an object")
    component_schema.bounded(local, 32_000)
    viewport = viewport or {"width": 900, "height": 650}
    if (
        not isinstance(viewport, dict)
        or set(viewport) != {"width", "height"}
        or not all(type(v) in (int, float) and 1 <= v <= 10000 for v in viewport.values())
    ):
        raise ValueError("viewport needs finite width and height between 1 and 10000")
    return {"objects": objects, "state": state, "local": local, "viewport": viewport}


def fingerprint(world, record):
    # Interaction-local state and viewport are not persistent prerequisites.
    return digest({"definition": record.body, "inputs": context(world, record)})


def active(world):
    display = world.facet(DESK, "core.display")
    if not display or display.body.get("kind") != "component" or not display.body["lens"]:
        return None
    return admitted(world, display.body["lens"], display.body["revision"])


def actions(world):
    record = active(world)
    if not record:
        return []
    return [
        {"component": record.entity, "revision": record.revision, "name": name, **spec}
        for name, spec in record.body["actions"].items()
    ]
