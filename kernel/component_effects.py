"""Validate a component's entire requested mutation batch against its pinned permissions.
Never: never accepts actor claims, performs external effects, or appends events."""

import copy
import hashlib

from kernel import component_schema, facets
from kernel.schema import DEFAULT_TRANSFORM


def prepare(world, record, output):
    permissions = record.body["permissions"]
    changes, placements, touched = [], [], set()
    for effect in output.get("effects", []):
        if not isinstance(effect, dict) or set(effect) != {"verb", "args"}:
            raise ValueError("effects need exactly verb and args")
        args = effect["args"]
        if not isinstance(args, dict):
            raise ValueError("effect args must be an object")
        if effect["verb"] == "place":
            if set(args) - {"entity", "scene", "transform", "mode"} or not {
                "entity",
                "scene",
                "transform",
            } <= set(args):
                raise ValueError("place effects need entity, scene, transform, and optional mode")
            grant = permissions.get("place", {})
            if args["scene"] != grant.get("scene") or args["entity"] not in grant.get(
                "entities", []
            ):
                raise ValueError("component lacks placement permission for this entity and scene")
            if not isinstance(args["transform"], dict):
                raise ValueError("transform must be an object")
            transform = dict(DEFAULT_TRANSFORM, **args["transform"])
            placement = dict(args, transform=transform, mode=args.get("mode", "icon"))
            facets.validate_appearance(placement)
            if (
                world.entity(args["entity"]) is None
                or world.facet(args["scene"], "core.scene") is None
            ):
                raise ValueError("placement binding no longer exists")
            appearances = world.appearances(args["scene"])
            added = {p["entity"] for p in placements if p["scene"] == args["scene"]}
            if len({a.entity for a in appearances} | added | {args["entity"]}) > 1000:
                raise ValueError("scene limit is 1000 appearances")
            placements.append(placement)
        elif effect["verb"] == "attach":
            if set(args) != {"entity", "facet_type", "body"}:
                raise ValueError("attach effects need entity, facet_type, body")
            ref, type_ = args["entity"], args["facet_type"]
            if not isinstance(ref, str) or type_ not in permissions.get("attach", {}).get(ref, []):
                raise ValueError("component lacks write permission for this entity and facet")
            body = args["body"]
            if not isinstance(body, dict) or "path" in body or "snapshot" in body:
                raise ValueError("component writes cannot import paths or supply storage snapshots")
            facets.validate(type_, body)
            if (ref, type_) in touched:
                raise ValueError("one facet may be changed only once in an interaction")
            touched.add((ref, type_))
            changes.append({"entity": ref, "type": type_, "body": body})
        else:
            raise ValueError(
                "component effects may only place or attach within declared permissions"
            )
    if "state" in output:
        if not permissions.get("state", False):
            raise ValueError("component lacks persistent-state permission")
        component_schema.shape(record.body["state_schema"], output["state"])
        changes.append(
            {
                "entity": record.entity,
                "type": "core.component-state",
                "body": {
                    "schema": record.body["state_schema"],
                    "data": output["state"],
                },
            }
        )
    if output.get("selected") is not None and output["selected"] not in record.body["bindings"]:
        raise ValueError("component selection must be one of its readable bindings")
    return {
        "changes": changes,
        "placements": placements,
        "component": record.entity,
        "definition_revision": record.revision,
        "source_hash": hashlib.sha256(record.body["source"].encode()).hexdigest(),
    }


def projected_context(ctx, batch, output, actor):
    """Render the proposed state before committing it, so render failures leave no write."""
    result = copy.deepcopy(ctx)
    result["local"] = output["local"]
    if "state" in output:
        result["state"] = output["state"]
    for change in batch["changes"]:
        obj = result["objects"].get(change["entity"])
        if obj and change["type"] in obj["facets"]:
            facet = obj["facets"][change["type"]]
            facet.update(body=change["body"], revision=facet["revision"] + 1, written_by=actor)
    for placement in batch["placements"]:
        facet = result["objects"][placement["scene"]]["facets"]["core.scene"]
        appearances = facet["body"].get("appearances", [])
        facet["body"]["appearances"] = [
            a for a in appearances if a["entity"] != placement["entity"]
        ] + [{k: placement[k] for k in ("entity", "mode", "transform")}]
        facet.update(revision=facet["revision"] + 1, written_by=actor)
    return result
