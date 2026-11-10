"""Invalid authored row queries report lens refusals without breaking native writes."""

import io
import json
import pickle
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import deskd
import explore
import lens_ir
import roomworld
import scene
import store
from world import Refusal

VALID = 'root : column\n  of house doing=working\n  each worker\nworker : text "$resident"'
INVALID = VALID.replace("house doing=working", "house resident=rowan,alex doing=working")


@pytest.fixture
def case(monkeypatch, tmp_path):
    desk, _ = roomworld.build()
    w = desk.world
    w.me = "alex"
    style = w.add_subject("note", "Test Style", "token accent = #123456", tags=["style"])
    style_item = w.place(style, w.root, 0, 0, 100, 100)
    lens = w.add_subject("note", "Test Lens", INVALID, tags=["lens"])
    w.subjects[lens]["props"]["style"] = "Test Style"
    w.place(lens, w.root, 0, 0, 100, 100)
    monkeypatch.setattr(
        scene,
        "house_rows",
        lambda *args: [{"resident": "rowan", "doing": "working", "item": style_item}],
    )
    monkeypatch.setattr(scene, "reported_views", lambda *args: ({}, None))
    monkeypatch.setattr(deskd, "SESSIONS", tmp_path)
    monkeypatch.setattr(deskd, "_trace", lambda *args: None)
    monkeypatch.setattr(deskd, "_DESKS", {})
    monkeypatch.setattr(deskd, "HOLD", [False])
    monkeypatch.delenv("DESK_LOG", raising=False)
    return SimpleNamespace(
        desk=desk,
        w=w,
        style=style,
        item=style_item,
        lens=w.subjects[lens],
        path=tmp_path / "roomworld-lens-try.pickle",
    )


def test_expected_row_query_refusal_is_a_lens_refusal(case):
    with pytest.raises(scene.LensRefusal, match="unknown term 'alex'") as error:
        lens_ir.Accessor(case.desk).rows("house resident=rowan,alex doing=working")
    assert isinstance(error.value.__cause__, Refusal)


def test_invalid_query_check_and_fresh_scene_report_refusal(case):
    ok, note = lens_ir.check(case.desk, case.lens)
    assert not ok and "does not compile" in note and "unknown term 'alex'" in note
    with pytest.raises(scene.LensRefusal, match="unknown term 'alex'"):
        lens_ir.scene_for(case.desk, "Test Lens")


def test_invalid_query_uses_last_good_lens_and_reports_fallback(case):
    case.lens["text"] = VALID
    ok, note = lens_ir.check(case.desk, case.lens)
    assert ok, note
    case.lens["text"] = INVALID
    case.lens["rev"] += 1
    ok, note = lens_ir.check(case.desk, case.lens)
    assert not ok and "last version" in note and "unknown term 'alex'" in note
    sc, printed = lens_ir.scene_for(case.desk, "Test Lens")
    assert sc["def"]["status"] == "fallback"
    assert "unknown term 'alex'" in sc["broken"]
    assert "gestures are off" in printed and "rowan" in printed


def test_style_rewrite_api_response_succeeds_and_native_write_is_durable(case):
    store.genesis(case.desk, case.path, why="isolated row refusal test")
    explore.save_desk(case.path, case.desk)
    updated = "token accent = #654321"
    line = f'read {case.item}; do rewrite {case.item} text="{updated}"'
    body = json.dumps({"session": case.path.stem, "as": "alex", "line": line}).encode()
    handler = deskd.Handler.__new__(deskd.Handler)
    handler.path, handler.headers = "/api/do", {"Content-Length": str(len(body))}
    handler.rfile, handler._json = io.BytesIO(body), Mock()
    handler._post()
    response = handler._json.call_args.args[0]
    assert response["error"] is None, response
    assert "style Test Style parses" in response["text"]
    assert "now refusing: 1" in response["text"]
    assert "unknown term 'alex'" in response["text"]
    assert response["events"]
    saved = pickle.loads(case.path.read_bytes())
    assert saved.world.subjects[case.style]["text"] == updated
    facts, _, _ = store.Log(store.log_path(case.path)).flat()
    assert facts[(case.style, "text")] == updated
    assert facts == store.flatten(saved.world)


def test_selection_refusal_is_a_lens_refusal(case):
    # a5398: a let's count() over in:<a note> raised the native Refusal out of the compiler
    with pytest.raises(scene.LensRefusal, match="in: needs a surface id") as error:
        lens_ir.Accessor(case.desk).select(f"kind:task,in:{case.item}")
    assert isinstance(error.value.__cause__, Refusal)
    case.lens["text"] = f'root : column\n  let k = count(kind:task,in:{case.item})\n  t : text "$(k)"'
    ok, note = lens_ir.check(case.desk, case.lens)
    assert not ok and "in: needs a surface id" in note


def test_unexpected_row_source_bug_still_propagates(case, monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("unexpected row source bug")

    monkeypatch.setattr(scene, "rows", broken)
    with pytest.raises(RuntimeError, match="unexpected row source bug"):
        lens_ir.check(case.desk, case.lens)
