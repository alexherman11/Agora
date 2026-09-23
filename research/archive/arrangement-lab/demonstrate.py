"""Generate a transparent example receipt from the actual tested model."""

import json
from pathlib import Path

from fixtures import edit, make_lab
from model import key
from planners import representative


def scene(lab):
    members = lab.value(key("surface", "desk", "members"))
    return {
        "appearances": [
            {
                "id": item,
                "subject": lab.value(key("occurrence", item, "binding"))["subject"],
                "placement": lab.value(key("occurrence", item, "placement")),
            }
            for item in members
        ],
        "stack_bottom_to_top": lab.value(key("surface", "desk", "stack:normal")),
    }


def main():
    lab = make_lab()
    before = scene(lab)
    builder = lab.builder()
    oas, mail, rest = representative(builder)
    plan = builder.finish()
    assert not lab.events
    receipt = lab.commit(plan.digest, actor="alex", request_id="oas-call")
    after = scene(lab)
    content = key("subject", "subject-oas-0", "text")
    edit(lab, {content: "A paragraph written after arranging the desk."}, "later-edit")
    undo = lab.undo_plan(receipt["event"])
    undone = lab.commit(undo.digest, actor="alex", request_id="undo-oas-call")
    restored = scene(lab)
    assert before == restored
    assert lab.cells == lab.replay()
    report = {
        "scope": "synthetic in-memory model; no live UI or semantic inference",
        "request": "OAS stuff on the left, the mail thread where I can see it, everything else out of my way",
        "resolved": {"oas": oas, "mail": mail, "remainder": rest},
        "operations": [json.loads(op) for op in plan.operations],
        "dependencies": [{"address": a, "version": version} for a, version in plan.guards],
        "accepted": receipt,
        "before": before,
        "after": after,
        "undo": undone,
        "restored": restored,
        "later_text_preserved": lab.value(content),
        "replay_matches": True,
        "event_count": len(lab.events),
    }
    destination = Path(__file__).resolve().parent / "evidence" / "scenario.json"
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(destination),
                "selected": [len(oas), len(mail), len(rest)],
                "accepted": receipt,
                "undo": undone,
                "replay_matches": True,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
