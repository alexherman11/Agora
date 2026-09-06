"""Component execution and activation judgments behind the public verb gateway.
Never: never writes the store or log; all commits go through the supplied verb gateway."""

from kernel import component_data as data
from kernel import component_effects, component_runtime, component_schema, component_tree
from kernel.schema import DESK


def frame(world, entity="", revision=None, local=None, viewport=None):
    record = data.definition(world, entity, revision) if entity else data.active(world)
    if not record:
        return {"active": False}
    output = component_runtime.execute(record.body, data.context(world, record, local, viewport))
    display = world.facet(DESK, "core.display")
    return {
        "active": True,
        "entity": record.entity,
        "revision": record.revision,
        "title": record.body["title"],
        "definition": record.body,
        "display_revision": display.revision if display else 0,
        "fingerprint": data.fingerprint(world, record),
        **output,
    }


def interact(
    world,
    actor,
    entity,
    revision,
    event,
    local,
    viewport,
    expected,
    commit,
    *,
    candidate=False,
    action="",
):
    record = (
        data.definition(world, entity, revision)
        if candidate
        else data.admitted(world, entity, revision)
    )
    if not candidate:
        current = data.active(world)
        if not current or (current.entity, current.revision) != (entity, revision):
            raise ValueError("this component is no longer active")
    if expected != data.fingerprint(world, record):
        raise ValueError("component inputs changed; refresh before retrying the interaction")
    ctx = data.context(world, record, local, viewport)
    if action:
        spec = record.body["actions"].get(action)
        if not spec:
            raise ValueError("no such component action")
        component_schema.shape(spec["params"], event)
    else:
        component_schema.bounded(event, 16_000)
        if not isinstance(event, dict) or not {"node", "type"} <= set(event):
            raise ValueError("interaction needs a rendered node id and event type")
        before = component_runtime.execute(record.body, ctx)
        node = component_tree.validate(before["tree"]).get(event["node"])
        if not node or event["type"] not in node.get("on", {}):
            raise ValueError("event does not target a current rendered handler")
        event = dict(event, handler=node["on"][event["type"]], entity=node.get("entity"))
    output = component_runtime.execute(record.body, ctx, event, action)
    if (
        not action
        and event.get("type") == "pointermove"
        and (output.get("effects") or "state" in output)
    ):
        raise ValueError("pointer motion must use local state; persist the decision on release")
    batch = component_effects.prepare(world, record, output)
    principal = f"component:{entity}@{revision}"
    if batch["changes"] or batch["placements"]:
        proposed = component_effects.projected_context(ctx, batch, output, principal)
        output["tree"] = component_runtime.execute(record.body, proposed)["tree"]
    if batch["changes"] or batch["placements"]:
        batch["requested_by"] = actor
        commit(world.world, principal, "component-committed", batch)
    return {
        "active": True,
        "entity": entity,
        "revision": revision,
        **output,
        "fingerprint": data.fingerprint(world, record),
    }


def activate(world, actor, entity, revision, expected_revision, commit):
    record = data.definition(world, entity, revision)
    current = world.facet(DESK, "core.display")
    if type(expected_revision) is not int or expected_revision != (
        current.revision if current else 0
    ):
        raise ValueError("stale display revision; inspect current display before activation")
    admission = world.facet(entity, "core.component-admission")
    admitted = list(admission.body["definitions"]) if admission else []
    digest = data.digest(record.body)
    if digest not in admitted:
        proof = world.facet(entity, "core.component-test")
        if (
            not proof
            or proof.body["definition"] != digest
            or proof.body["fingerprint"] != data.fingerprint(world, record)
        ):
            raise ValueError("test this exact component against current inputs before activation")
        admitted.append(digest)
    # Check state compatibility even on restoration of an already admitted version.
    frame(world, entity, record.revision)
    if world.entity(DESK) is None:
        raise ValueError("initialize the desk before activating a component")
    commit(
        world.world,
        actor,
        "component-committed",
        {
            "changes": [
                {
                    "entity": entity,
                    "type": "core.component-admission",
                    "body": {"definitions": admitted},
                },
                {
                    "entity": DESK,
                    "type": "core.display",
                    "body": {"lens": entity, "revision": record.revision, "kind": "component"},
                },
            ],
            "placements": [],
            "component": entity,
            "definition_revision": record.revision,
        },
    )
    return {
        "entity": entity,
        "revision": record.revision,
        "display_revision": world.facet(DESK, "core.display").revision,
    }
