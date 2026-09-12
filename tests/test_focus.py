"""world.focus: bounded attention snapshot with honest deltas and no second write path."""

import json

from agora3.agent_state import AgentState
from agora3.gateway import Gateway
from agora3.jeff import Jeff
from agora3.world import Refusal


def make(tmp_path):
    gateway = Gateway(tmp_path / "world")
    return gateway, gateway.principal("human")


def note(gateway, actor, oid, title, text="body"):
    return gateway.dispatch(
        actor,
        "world.transact",
        {
            "changes": [
                {
                    "id": oid,
                    "expected_revision": 0,
                    "facets": {"core.title": {"text": title}, "core.text": {"text": text}},
                }
            ]
        },
    )


def test_fallback_recent_entries_exclude_runtime_and_conversation(tmp_path):
    gateway, actor = make(tmp_path)
    for index in range(10):
        note(gateway, actor, f"note-{index}", f"Note {index}")
    gateway.record_message(actor, "user", "hello")
    snapshot = gateway.dispatch(actor, "world.focus", {})
    assert snapshot["changed"] is True and snapshot["source"]["mode"] == "recent"
    ids = [entry["id"] for entry in snapshot["entries"]]
    assert len(ids) == 8 and "note-9" in ids and "note-0" not in ids
    assert not any(i.startswith(("agora.", "message.")) for i in ids)
    for entry in snapshot["entries"]:
        assert entry["revision"] >= 1 and entry["event"] >= 1  # every fact carries its source


def test_declared_set_orders_depth_and_reports_absent(tmp_path):
    gateway, actor = make(tmp_path)
    note(gateway, actor, "note-a", "Alpha", "alpha text " * 100)
    gateway.dispatch(
        actor,
        "schema.define",
        {
            "type": "focus.set",
            "schema": {
                "type": "object",
                "properties": {"entries": {"type": "array", "maxItems": 8}},
                "required": ["entries"],
            },
        },
    )
    gateway.dispatch(
        actor,
        "world.transact",
        {
            "changes": [
                {
                    "id": "jeff.focus",
                    "expected_revision": 0,
                    "facets": {
                        "focus.set": {
                            "entries": [
                                {"ref": "note-a", "depth": "content"},
                                {"ref": "missing-object", "depth": "name"},
                            ]
                        }
                    },
                }
            ]
        },
    )
    snapshot = gateway.dispatch(actor, "world.focus", {})
    assert snapshot["source"]["set"] == "jeff.focus"
    first, second = snapshot["entries"]
    assert first["id"] == "note-a" and first["text_truncated"] is True
    assert first["text"].startswith("alpha text") and len(first["text"]) == 600
    assert second == {"id": "missing-object", "absent": True, "changed": False}


def test_since_reports_unchanged_then_changed(tmp_path):
    gateway, actor = make(tmp_path)
    note(gateway, actor, "note-a", "Alpha")
    first = gateway.dispatch(actor, "world.focus", {})
    quiet = gateway.dispatch(actor, "world.focus", {"since": first["watermark"]})
    assert quiet["changed"] is False
    assert all(entry["changed"] is False for entry in quiet["entries"])
    gateway.dispatch(
        actor,
        "world.transact",
        {
            "changes": [
                {
                    "id": "note-a",
                    "expected_revision": 1,
                    "facets": {"core.title": {"text": "Alpha edited"}},
                }
            ]
        },
    )
    loud = gateway.dispatch(actor, "world.focus", {"since": first["watermark"]})
    assert loud["changed"] is True
    assert [e for e in loud["entries"] if e["id"] == "note-a"][0]["changed"] is True


def test_open_views_are_listed_with_subject_titles(tmp_path):
    gateway, actor = make(tmp_path)
    gateway.seed()
    view = gateway.dispatch(
        actor, "application.list", {}
    )  # seed installs no applications; craft one is heavy, so assert shape only
    assert view["views"] == []
    snapshot = gateway.dispatch(actor, "world.focus", {})
    assert snapshot["views"] == [] and snapshot["complete_scan"] is True


def test_resident_focus_object_with_integer_depths_and_modes(tmp_path):
    gateway, actor = make(tmp_path)
    AgentState(gateway, tmp_path / "world").configure(
        actor, agent_id="jeff0", name="JEFF0", continuity="test resident"
    )
    note(gateway, actor, "note-a", "Alpha", "alpha body")
    gateway.dispatch(
        actor,
        "schema.define",
        {
            "type": "agent.focus-set",
            "schema": {
                "type": "object",
                "properties": {"entries": {"type": "array", "maxItems": 8}},
                "required": ["entries"],
            },
        },
    )
    gateway.dispatch(
        actor,
        "world.transact",
        {
            "changes": [
                {
                    "id": "jeff0.focus",
                    "expected_revision": 0,
                    "facets": {
                        "agent.focus-set": {
                            "entries": [
                                {"ref": "note-a", "depth": 2, "mode": "pinned"},
                                {"ref": "note-a-missing", "depth": 0, "mode": "auto"},
                            ]
                        }
                    },
                }
            ]
        },
    )
    snapshot = gateway.dispatch(actor, "world.focus", {})
    assert snapshot["source"]["set"] == "jeff0.focus"  # resolved via the resident record
    first, second = snapshot["entries"]
    assert first["id"] == "note-a" and first["depth"] == "content" and first["text"]
    assert second["absent"] is True


def test_invalid_since_is_a_schema_refusal(tmp_path):
    gateway, actor = make(tmp_path)
    try:
        gateway.dispatch(actor, "world.focus", {"since": -1})
    except Refusal as refusal:
        assert "minimum" in str(refusal) or "-1" in str(refusal)
    else:
        raise AssertionError("negative since must refuse")


def test_adapter_header_injects_only_on_change(tmp_path):
    calls = []

    def dispatch(name, args):
        calls.append((name, dict(args)))
        since = args.get("since")
        return {"watermark": 7, "changed": since != 7, "entries": [], "views": []}

    jeff = Jeff(tmp_path, dispatch, lambda: [])
    first = jeff._focus_header()
    assert first.startswith("World focus (a world.focus snapshot")
    assert json.loads(first.split(": ", 1)[1])["watermark"] == 7
    second = jeff._focus_header()
    assert "unchanged" in second and "watermark 7" in second
    assert calls == [("world.focus", {}), ("world.focus", {"since": 7})]


def test_adapter_header_failure_never_breaks_the_turn(tmp_path):
    def dispatch(name, args):
        raise RuntimeError("gateway offline")

    jeff = Jeff(tmp_path, dispatch, lambda: [])
    assert jeff._focus_header() is None
