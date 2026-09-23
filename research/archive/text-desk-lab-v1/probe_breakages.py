"""Retain constructive counterexamples instead of concealing simulator limitations."""

import json
from pathlib import Path

from desk import Desk
from hard_desk import overlaps
from scenarios import build, fixture
from test_desk import do


def probe():
    results = {}
    desk = build("meeting")
    for source in ["risk-live", "risk-old", "agenda"]:
        do(desk, "reference", "questions", source=source)
    page_one = desk.look("questions", "structure", limit=1)["text"]
    do(desk, "remove", "appearance-1")
    continuation = desk.look("questions", "structure", limit=1, offset=1)["text"]
    results["offset_skips_unread_sibling_after_removal"] = {
        "page_one": page_one,
        "continuation": continuation,
        "missed": "appearance-2",
        "still_present": "appearance-2" in desk.nodes,
        "reproduced": "appearance-2" not in continuation and "appearance-3" in continuation,
    }

    desk = build("release")
    receipt = do(desk, "reference", "done", source="t-sign")
    results["task_reference_into_done_without_completion"] = {
        "receipt": receipt,
        "task_status": desk.get("t-sign")["status"],
        "done_children": [n["id"] for n in desk.children("done")],
        "reproduced": desk.get("t-sign")["status"] == "doing" and len(desk.children("done")) == 1,
    }

    nodes = fixture()
    nodes["p-agenda"].update(x=16, y=16)
    desk = Desk(nodes)
    receipt = do(desk, "tile", "planning", items=["p-risk"], columns=1)
    results["tile_overlaps_unselected_pinned_card"] = {
        "receipt": receipt,
        "reproduced": overlaps(desk.get("p-risk"), desk.get("p-agenda")),
        "pinned_card_preserved": desk.get("p-agenda") == desk.initial["p-agenda"],
    }
    return results


if __name__ == "__main__":
    result = probe()
    Path(__file__).with_name("architecture-counterexamples.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps({key: value["reproduced"] for key, value in result.items()}))
