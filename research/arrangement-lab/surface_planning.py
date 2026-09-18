"""Pure application-facing geometry contract. It grants no read or write authority."""

import hashlib
import json

from model import Lab, Refusal, key, wire
from planners import layer, place, tile


def contribute(builder, surface, operations, measurement):
    for op in operations:
        kind = op.get("operator")
        if kind == "tile":
            tile(builder, surface, op["targets"], op["region"], op["columns"], measurement)
        elif kind == "place":
            place(builder, surface, op["target"], op["bounds"])
        elif kind in ("sink", "raise"):
            layer(builder, surface, op["targets"], kind)
        else:
            raise Refusal(
                "Unknown operator. Author a planner returning explicit place operations, or use tile/place/sink/raise."
            )


def plan_surface(snapshot, operations):
    """Caller owns the snapshot, its provenance, admission guards, and final storage.

    A freeform surface advertises geometry; ordered lists keep their own order policy.
    This function neither resolves subjects nor silently imposes a desktop schema.
    """
    if snapshot.get("contract") != "freeform/v1":
        raise Refusal("Expected freeform/v1; lists must retain their own ordering policy.")
    items = snapshot["items"]
    if not 1 <= len(items) <= 100:
        raise Refusal("Supply 1-100 occurrences.")
    ids = [item["id"] for item in items]
    if (
        len(set(ids)) != len(ids)
        or set(snapshot["order"]) != set(ids)
        or len(snapshot["order"]) != len(ids)
    ):
        raise Refusal("Occurrence IDs must be unique and order must contain each exactly once.")
    surface = snapshot["surface"]
    data = {
        key("surface", surface, "members"): ids,
        key("surface", surface, "parent"): None,
        key("surface", surface, "contract"): "freeform/v1",
        key("surface", surface, "stack:normal"): snapshot["order"],
    }
    for item in items:
        oid = item["id"]
        data[key("occurrence", oid, "binding")] = {"surface": surface, "subject": item["subject"]}
        data[key("occurrence", oid, "placement")] = {"mode": "free", "rect": item["bounds"]}
        data[key("occurrence", oid, "minimum")] = item.get("minimum", [1, 1])
        data[key("occurrence", oid, "stratum")] = "normal"
    lab = Lab(data)
    lab.observe(
        "frame",
        {
            "surface": surface,
            **snapshot["viewport"],
            "active": True,
            "transform": [1, 0, 0, 1, 0, 0],
        },
    )
    builder = lab.builder("planner")
    contribute(builder, surface, operations, "frame")
    plan = builder.finish(register=False)
    return {
        "input_digest": hashlib.sha256(wire(snapshot).encode()).hexdigest(),
        "effects": [
            {"address": address, "value": json.loads(payload)} for address, payload in plan.effects
        ],
        "native_writes": 0,
        "admission": "Application must revalidate its snapshot and commit through its existing authenticated action; this result conveys no authority.",
    }
