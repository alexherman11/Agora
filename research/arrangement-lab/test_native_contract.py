"""Native admission invariants exposed by the live conversations."""

import sys
from copy import deepcopy

sys.path[:0] = [
    "C:/Projects/Agora/local/arrangement-trials-20260916/baseline/src",
    "C:/Projects/Agora/local/arrangement-trials-20260916/baseline/scripts",
]
import pytest
from agora3.applications import VIEW
from agora3.world import Refusal
from live_trials import seed
from native_arrangement import ArrangementGateway
from surface_planning import plan_surface


class Measurement:
    def call(self, **args):
        return {"width": 1300, "height": 1000, "x": 0, "y": 0}


@pytest.fixture
def setup(tmp_path):
    g = ArrangementGateway(tmp_path)
    views = seed(g, True)
    g.arrangements.browser = Measurement()
    return g, g.principal("jeff"), views[0]["id"]


def prepare(g, actor, oid):
    return g.dispatch(
        actor,
        "arrangement.prepare",
        {
            "reason": "Invariant test",
            "operations": [{"operator": "place", "target": oid, "bounds": [40, 40, 320, 300]}],
        },
    )


def patch_view(g, actor, oid, **patch):
    obj = g.world.get(oid)
    g.commit(
        actor,
        [
            {
                "id": oid,
                "expected_revision": obj["revision"],
                "facets": {VIEW: {**obj["facets"][VIEW], **patch}},
            }
        ],
        internal=True,
    )


def test_editor_state_is_not_a_layout_conflict(setup):
    g, actor, oid = setup
    original = deepcopy(g.world.get(oid)["facets"][VIEW]["bounds"])
    plan = prepare(g, actor, oid)
    patch_view(g, actor, oid, state={"draft": "Before apply"})
    receipt = g.dispatch(actor, "arrangement.apply", {"plan": plan["plan"]})
    patch_view(g, actor, oid, state={"draft": "After apply"})
    g.dispatch(actor, "arrangement.undo", {"intent": receipt["intent"]})
    value = g.world.get(oid)["facets"][VIEW]
    assert value["bounds"] == original and value["state"]["draft"] == "After apply"
    assert g.world.verify()["ok"]


@pytest.mark.parametrize("phase", ["apply", "undo"])
def test_layout_aba_refuses_without_a_write(setup, phase):
    g, actor, oid = setup
    plan = prepare(g, actor, oid)
    receipt = (
        g.dispatch(actor, "arrangement.apply", {"plan": plan["plan"]}) if phase == "undo" else None
    )
    original = deepcopy(g.world.get(oid)["facets"][VIEW]["bounds"])
    patch_view(g, actor, oid, bounds={**original, "x": original["x"] + 1})
    patch_view(g, actor, oid, bounds=original)
    before = g.world.query(limit=1)["watermark"]
    with pytest.raises(Refusal):
        g.dispatch(
            actor,
            "arrangement." + phase,
            {"intent": receipt["intent"]} if receipt else {"plan": plan["plan"]},
        )
    assert g.world.query(limit=1)["watermark"] == before


def test_binding_change_blocks_undo(setup):
    g, actor, oid = setup
    plan = prepare(g, actor, oid)
    receipt = g.dispatch(actor, "arrangement.apply", {"plan": plan["plan"]})
    patch_view(g, actor, oid, open=False)
    with pytest.raises(Refusal):
        g.dispatch(actor, "arrangement.undo", {"intent": receipt["intent"]})


def test_application_planning_uses_existing_lease_and_writes_nothing(setup):
    g, actor, oid = setup
    args = {
        "snapshot": {
            "surface": "local-board",
            "contract": "freeform/v1",
            "items": [{"id": "card", "subject": "supplied-data", "bounds": [0, 0, 200, 200]}],
            "order": ["card"],
            "viewport": {"width": 800, "height": 600},
        },
        "operations": [{"operator": "place", "target": "card", "bounds": [20, 20, 200, 200]}],
    }
    request = {
        "view": oid,
        "lease": g.world.get(oid)["facets"][VIEW]["lease"],
        "method": "arrangement.plan",
        "args": args,
    }
    before = g.world.query(limit=1)["watermark"]
    assert g.dispatch(actor, "application.request", request)["native_writes"] == 0
    with pytest.raises(Refusal):
        g.dispatch(actor, "application.request", {**request, "lease": "revoked"})
    assert g.world.query(limit=1)["watermark"] == before


def test_authored_surface_has_independent_occurrences_and_no_write_authority():
    snapshot = {
        "surface": "board",
        "contract": "freeform/v1",
        "items": [
            {"id": oid, "subject": "same-subject", "bounds": [0, 0, 200, 180]} for oid in ["a", "b"]
        ],
        "order": ["a", "b"],
        "viewport": {"width": 800, "height": 600},
    }
    original = deepcopy(snapshot)
    result = plan_surface(
        snapshot, [{"operator": "place", "target": "a", "bounds": [44, 60, 200, 180]}]
    )
    assert snapshot == original and result["native_writes"] == 0
    assert result["effects"] == [
        {
            "address": ("occurrence", "a", "placement"),
            "value": {"mode": "free", "rect": [44, 60, 200, 180]},
        }
    ]
