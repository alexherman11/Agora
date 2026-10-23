"""Replay only captured metadata against both policies, with no world/session access."""
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from stage import LAB, candidates

sys.path.insert(0, str(LAB))
import task_flow

POLICY = {"role": "task-transition-policy", "version": "1", "enabled": "on",
          "states": "ready,landed,failed,done", "milestones": "completed,failed"}
EMPTY_HASH = __import__("hashlib").sha256(b"").hexdigest()


def modules():
    _, sources = candidates()
    out = {}
    for name, source in sources.items():
        module = ModuleType("staged_" + name[:-3])
        module.__file__ = str(LAB / name)
        sys.modules[module.__name__] = module
        exec(compile(source, module.__file__, "exec"), module.__dict__)
        out[name[:-3]] = module
    out["house"].task_flow = out["task_flow"]
    return out


def props(row, side):
    p = dict(row[side])
    p.update({k: "" if v == EMPTY_HASH else "sha256:" + v
              for k, v in row[side + "_hashes"].items()})
    return p


def replay():
    candidate = modules()["task_flow"]
    rows = json.loads(Path(__file__).with_name("captured-metadata.json").read_text())
    world = SimpleNamespace(subjects={"policy": {"props": POLICY}}, events=[])
    result, receipts = [], {}
    for row in rows:
        old_routes, new_routes = [], []
        if "task" in row:
            before, after = props(row, "old"), props(row, "new")
            event = {"id": row["event"], "by": row["by"], "verb": row["verb"],
                     "target": row["target"],
                     "args": {k: after.get(k, "") for k in row["arg_keys"]}}
            card = {"id": row["task"], "kind": "task", "title": "Captured task"}
            for implementation, routes in ((task_flow, old_routes), (candidate, new_routes)):
                with patch.object(implementation, "_card", return_value=(card, before, after)), \
                     patch.object(implementation, "_creator", return_value=row["creator"]), \
                     patch.object(implementation.persons, "holds", side_effect=lambda w, value, actor:
                                  actor in row["resident_bindings"].get(value, [])
                                  or actor in str(value).split(",")), \
                     patch.object(implementation, "_residents",
                                  side_effect=lambda w, value: row["resident_bindings"].get(value, [])):
                    notices = implementation.notices(world, event)
                for n in notices:
                    if implementation is candidate:
                        n = candidate.accept_notice(receipts.setdefault(n["recipient"], {}), n)
                    if n:
                        routes.append({"recipient": n["recipient"], "kinds": n["kinds"]})
            assert old_routes == row["transition_routes"], row["event"]
            assert new_routes == row["candidate_routes"], row["event"]
        result.append({"event": row["event"], "before": old_routes, "after": new_routes})
    return rows, result


def main():
    rows, result = replay()
    changed = [r for r in result if r["before"] != r["after"]]
    report = {
        "interval": ["e26500", "e27216"], "records": len(rows),
        "transition_notices_before": sum(len(r["before"]) for r in result),
        "transition_notices_after": sum(len(r["after"]) for r in result),
        "other_route_events_before": sum(bool(r["other_routes"]) for r in rows),
        "other_route_events_after": sum(bool(r["candidate_other_routes"]) for r in rows),
        "other_route_changes": [
            {"event": r["event"], "verb": r["verb"],
             "before": r["other_routes"], "after": r["candidate_other_routes"]}
            for r in rows if r["other_routes"] != r["candidate_other_routes"]],
        "question_events": sum(r["question"] for r in rows),
        "human_route_events": sum(r["human"] and bool(r["other_routes"]) for r in rows),
        "changed_events": changed,
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
