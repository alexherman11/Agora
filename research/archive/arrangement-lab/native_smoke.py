"""Exercise native prepare/apply/undo through a disposable real gateway, without a model."""

from pathlib import Path
import json
import sys
import tempfile

sys.path[:0] = [
    "C:/Projects/Agora/local/arrangement-trials-20260916/baseline/src",
    "C:/Projects/Agora/local/arrangement-trials-20260916/baseline/scripts",
]
from native_arrangement import ArrangementGateway
from live_trials import seed


class Measurement:
    def call(self, **args):
        return {"width": 1300, "height": 1000, "x": 0, "y": 0}


with tempfile.TemporaryDirectory(
    prefix="arrangement-native-", dir="C:/Projects/Agora/local"
) as folder:
    g = ArrangementGateway(Path(folder))
    views = seed(g, True)
    g.arrangements.browser = Measurement()
    actor = g.principal("jeff")
    before = g.world.query(limit=1000)
    result = g.dispatch(
        actor,
        "arrangement.prepare",
        {
            "reason": "Native smoke",
            "operations": [
                {
                    "operator": "tile",
                    "targets": [v["id"] for v in views[:6]],
                    "region": [0, 0, 650, 900],
                    "columns": 2,
                },
                {"operator": "place", "target": views[6]["id"], "bounds": [700, 0, 500, 900]},
                {"operator": "sink", "targets": [v["id"] for v in views[7:15]]},
                {"operator": "raise", "targets": [views[6]["id"]]},
            ],
        },
    )
    assert g.world.query(limit=1)["watermark"] == before["watermark"]
    receipt = g.dispatch(actor, "arrangement.apply", {"plan": result["plan"]})
    assert receipt["event"] == before["watermark"] + 1
    assert g.dispatch(actor, "arrangement.apply", {"plan": result["plan"]})["already_applied"]
    content = g.world.get("work-02")
    g.commit(
        actor,
        [
            {
                "id": content["id"],
                "expected_revision": content["revision"],
                "facets": {"core.text": {"text": "A later edit"}},
            }
        ],
    )
    g.dispatch(actor, "arrangement.undo", {"intent": receipt["intent"]})
    assert g.world.get("work-02")["facets"]["core.text"]["text"] == "A later edit"
    for view in views:
        assert g.applications.public_view(g.world.get(view["id"]))["bounds"] == view["bounds"]
    assert g.world.verify()["ok"]
    print(
        json.dumps(
            {"passed": True, "native_atomic_prepare_apply_undo": True, "replay": g.world.verify()}
        )
    )
