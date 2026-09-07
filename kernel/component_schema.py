"""Versioned executable-component records and owned-state shapes.
Never: never runs code, reads objects, grants permissions, or writes state."""

import json
import re

KINDS = {
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "object": dict,
    "array": list,
}
NAME = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{0,47}$")


def definitions(make, field):
    return {
        "core.component": make(
            "core.component",
            "Executable JS object expression with render, handle, and actions.",
            {
                "version": field("int", True, "1"),
                "title": field("str", True, "visible title"),
                "source": field(
                    "str",
                    True,
                    "JS expression ({render(ctx),handle(ctx,event),actions:{name(ctx,args)}})",
                ),
                "bindings": field(
                    "dict", True, "{entity_ref:[core.name,core.text,core.scene]} readable inputs"
                ),
                "permissions": field(
                    "dict", True, "{place?:{scene,entities},attach?:{ref:[facet]},state?:boolean}"
                ),
                "state_schema": field(
                    "dict", True, "{field:string|number|integer|boolean|object|array}; all required"
                ),
                "initial_state": field("dict", True, "initial values matching state_schema"),
                "actions": field("dict", True, "{name:{description,params:{field:JSON type}}}"),
            },
            limits={"title": 200, "source": 100_000},
        ),
        "core.component-state": make(
            "core.component-state",
            "Runtime-owned component state.",
            {
                "schema": field("dict", True),
                "data": field("dict", True),
            },
        ),
        "core.component-test": make(
            "core.component-test",
            "Trusted candidate test receipt.",
            {
                "definition": field("str", True),
                "fingerprint": field("str", True),
                "cases": field("list", True),
                "results": field("list", True),
            },
        ),
        "core.component-admission": make(
            "core.component-admission",
            "Trusted admitted source hashes.",
            {
                "definitions": field("list", True),
            },
        ),
    }


def bounded(value, limit=100_000):
    if len(json.dumps(value, allow_nan=False)) > limit:
        raise ValueError(f"component data exceeds {limit} characters")


def shape(schema, value):
    if not isinstance(schema, dict) or len(schema) > 32:
        raise ValueError("state/action schema must map at most 32 field names to types")
    if not isinstance(value, dict) or set(value) != set(schema):
        raise ValueError(f"data must have exactly the schema fields: {list(schema)}")
    for key, kind in schema.items():
        if not isinstance(key, str) or not NAME.fullmatch(key) or kind not in KINDS:
            raise ValueError("schema fields need simple names and supported JSON types")
        if not isinstance(value[key], KINDS[kind]) or (
            kind in ("number", "integer") and isinstance(value[key], bool)
        ):
            raise ValueError(f"{key} must be {kind}")
    bounded(value, 32_000)


def validate(body):
    if type(body["version"]) is not int or body["version"] != 1:
        raise ValueError("component version must be 1")
    bindings = body["bindings"]
    if not isinstance(bindings, dict) or len(bindings) > 64:
        raise ValueError("bindings must map at most 64 entity refs to readable facet lists")
    for ref, fields in bindings.items():
        if not isinstance(ref, str) or not isinstance(fields, list) or not fields:
            raise ValueError("each binding needs an entity ref and nonempty facet list")
        if len(fields) > 8 or not all(
            f in ("core.name", "core.text", "core.scene") for f in fields
        ):
            raise ValueError("readable facets are core.name, core.text, and core.scene")
    permissions = body["permissions"]
    if not isinstance(permissions, dict) or set(permissions) - {"place", "attach", "state"}:
        raise ValueError("permissions may contain place, attach, and state only")
    if type(permissions.get("state", False)) is not bool:
        raise ValueError("state permission must be boolean")
    placement = permissions.get("place")
    if placement is not None:
        if not isinstance(placement, dict) or set(placement) != {"scene", "entities"}:
            raise ValueError("place permission needs scene and entities")
        if (
            not isinstance(placement["entities"], list)
            or not all(isinstance(e, str) and e in bindings for e in placement["entities"])
            or "core.scene" not in bindings.get(placement["scene"], [])
        ):
            raise ValueError("placement subjects and scene must be explicit readable bindings")
    writes = permissions.get("attach", {})
    if not isinstance(writes, dict):
        raise ValueError("attach permission must map entity refs to writable facets")
    for ref, fields in writes.items():
        if (
            ref not in bindings
            or not isinstance(fields, list)
            or not all(f in ("core.name", "core.text") and f in bindings[ref] for f in fields)
        ):
            raise ValueError("writes require explicit core.name/core.text read bindings")
    shape(body["state_schema"], body["initial_state"])
    actions = body["actions"]
    if not isinstance(actions, dict) or len(actions) > 16:
        raise ValueError("actions must map at most 16 names to description and params")
    for name, action in actions.items():
        if (
            not NAME.fullmatch(name)
            or not isinstance(action, dict)
            or set(action) != {"description", "params"}
        ):
            raise ValueError("actions need simple names, description, and params")
        if not isinstance(action["description"], str) or len(action["description"]) > 500:
            raise ValueError("action description must be at most 500 characters")
        params = action["params"]
        if (
            not isinstance(params, dict)
            or len(params) > 16
            or not all(NAME.fullmatch(k) and v in KINDS for k, v in params.items())
        ):
            raise ValueError("action params must map simple names to JSON types")
    bounded(body, 150_000)
