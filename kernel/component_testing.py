"""Exercise authored interactions against a disposable world and record verified observations.
Never: never lets a candidate write its source world or fabricate a successful test receipt."""

import tempfile

from kernel import component_commands as commands
from kernel import component_data as data
from kernel import component_schema, component_tree, events, store


def test(world, actor, entity, revision, cases, commit):
    record = data.definition(world, entity, revision)
    component_schema.bounded(cases, 64_000)
    if not isinstance(cases, list) or not 1 <= len(cases) <= 24:
        raise ValueError("provide 1–24 candidate interaction cases with expectations")
    fingerprint = data.fingerprint(world, record)
    observations = []
    # This directory is created here solely for this candidate and removed on every exit.
    with tempfile.TemporaryDirectory(prefix="agora-candidate-") as directory:
        candidate_world = events.open_world(directory)
        events.copy_log(world.world, candidate_world)
        candidate = store.open_store(candidate_world)
        try:
            frame = commands.frame(candidate, entity, record.revision)
            for index, case in enumerate(cases):
                if (
                    not isinstance(case, dict)
                    or set(case) - {"event", "action", "args", "expect"}
                    or "expect" not in case
                ):
                    raise ValueError("case needs event or action/args, and expect")
                if ("event" in case) == ("action" in case):
                    raise ValueError("case needs exactly one event or action")
                frame = commands.interact(
                    candidate,
                    actor,
                    entity,
                    record.revision,
                    case.get("event", case.get("args", {})),
                    frame["local"],
                    None,
                    frame["fingerprint"],
                    commit,
                    candidate=True,
                    action=case.get("action", ""),
                )
                observe(candidate, record, frame, case["expect"])
                observations.append(
                    {
                        "case": index + 1,
                        "passed": True,
                        "tree": frame["tree"],
                        "effects": frame.get("effects", []),
                        "state": data.context(candidate, record)["state"],
                    }
                )
        finally:
            candidate.close()
    commit(
        world.world,
        actor,
        "component-committed",
        {
            "changes": [
                {
                    "entity": entity,
                    "type": "core.component-test",
                    "body": {
                        "definition": data.digest(record.body),
                        "fingerprint": fingerprint,
                        "cases": cases,
                        "results": [{"case": o["case"], "passed": True} for o in observations],
                    },
                }
            ],
            "placements": [],
            "component": entity,
            "definition_revision": record.revision,
        },
    )
    return {
        "passed": True,
        "entity": entity,
        "revision": record.revision,
        "fingerprint": fingerprint,
        "observations": observations,
    }


def observe(world, record, frame, expect):
    if (
        not isinstance(expect, dict)
        or not expect
        or set(expect) - {"text_contains", "state", "effect_count", "placement", "node", "value"}
    ):
        raise ValueError(
            "expect must check text_contains, state, effect_count, placement, node, or value"
        )
    nodes = component_tree.validate(frame["tree"])
    for key, wanted in expect.items():
        if key == "text_contains":
            ok = isinstance(wanted, str) and wanted in "\n".join(
                n.get("text", "") for n in nodes.values()
            )
        elif key == "state":
            ok = data.context(world, record)["state"] == wanted
        elif key == "effect_count":
            ok = len(frame.get("effects", [])) == wanted
        elif key == "value":
            ok = frame.get("value") == wanted
        elif key == "node":
            found = nodes.get(wanted.get("id")) if isinstance(wanted, dict) else None
            ok = found is not None and _matches(found, wanted)
        else:
            matches = [
                a for a in world.appearances(wanted["scene"]) if a.entity == wanted["entity"]
            ]
            ok = bool(matches) and all(
                matches[0].transform.get(k) == v for k, v in wanted["transform"].items()
            )
        if not ok:
            raise ValueError(f"candidate expectation failed: {key} should be {wanted!r}")


def _matches(actual, wanted):
    """Assert requested node fields recursively; unrelated style fields are immaterial."""
    if isinstance(wanted, dict):
        return isinstance(actual, dict) and all(
            key in actual and _matches(actual[key], value) for key, value in wanted.items()
        )
    return actual == wanted
