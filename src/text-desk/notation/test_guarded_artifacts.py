"""Guarded selection preflight plus the real durable comment/resident transport."""

import copy
import hashlib
import io
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import guarded_artifacts as artifacts
import image_comments
import pytest
import store
from test_image_comments import case  # noqa: F401 — shared disposable PNG/world
from world import Refusal

RUN = "2026-10-20-225210-1280x800"
SHOT = "01-busy-declined.png"


@pytest.fixture
def fixture(case):  # noqa: F811 — pytest injects the imported fixture
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "desktop"))
    from agora_tmp import directory
    tmp_path = Path(directory("guarded-artifact-test-"))
    d, target, image = case
    import base64
    raw = base64.b64decode(image["data_url"].split(",")[1])
    folder = tmp_path / RUN
    folder.mkdir()
    shot = folder / SHOT
    shot.write_bytes(raw)
    report = {
        "guard": [0, "alex: untouched by the sandbox (input desktop stayed Default)"],
        "size": [1280, 800], "world_at": None,
        "rows": [{"id": "busy", "outcome": "pass", "shots": [SHOT]}],
    }
    path = folder / "report.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    os.utime(shot, ns=(1_000_000_000, 1_000_000_000))
    kwargs = dict(artifact=RUN + "/" + SHOT, sha256=hashlib.sha256(raw).hexdigest(),
                  recipient="pike", target=target, prompt="Describe two visible details.",
                  root=tmp_path)
    return d, kwargs, path, shot


def test_guarded_delivery_is_actual_pixels_and_saved_refs(fixture):
    import house
    d, kwargs, _, _ = fixture
    before = copy.deepcopy(d.snapshot())
    prepared = artifacts.prepare(d.snapshot(), **kwargs)
    assert d.snapshot() == before  # Preflight has no effects.
    assert prepared["provenance"]["world_at"] is None  # Don't invent missing provenance.
    result = d.dispatch("desk", {k: prepared[k] for k in ("line", "image_context")})
    assert not result.get("error"), result
    assert "ERR" not in result.get("text", ""), result
    comment = d.world.subjects[d.world.nodes[kwargs["target"]]["subject"]]["comments"][-1]
    assert "untrusted evidence" in comment["text"]
    assert comment["image"]["data_url"] == prepared["image_context"]["data_url"]
    r = house.Resident.__new__(house.Resident)
    r.state = {"session": "saved"}
    r.save, r.log = Mock(), Mock()
    r.house = SimpleNamespace(load=lambda: d.world)
    r.proc = SimpleNamespace(stdin=io.StringIO())
    house.House._knocked(None, r, d.world.events[-1],
                         d.world.subjects[d.world.nodes[kwargs["target"]]["subject"]], False)
    # JSON round-trip models persisted pending refs; bytes stay in the comment.
    r.state = json.loads(json.dumps(r.state))
    r.send("The addressed image review")
    message = json.loads(r.proc.stdin.getvalue())["message"]["content"]
    assert message[-1]["type"] == "image"
    assert message[-1]["source"]["data"] == comment["image"]["data_url"].split(",")[1]
    sys.path.insert(0, str(artifacts.CODEX))
    try:
        from codex_resident import resident_inputs
        inputs = resident_inputs(message)
        assert inputs[-1]["url"] == comment["image"]["data_url"]
        assert resident_inputs("text-only unchanged") == "text-only unchanged"
    finally:
        sys.path.remove(str(artifacts.CODEX))
    pending = r.state.pop("pending")
    r.hold_unanswered(pending, "saved session resumes")
    assert not r.state.get("image_comments")
    r.state.pop("session")
    r.hold_unanswered(pending, "saved session lost")
    assert r.state["image_comments"] == [comment["id"]]


@pytest.mark.parametrize("change", [
    {"artifact": "../sessions/frontier.pickle"},
    {"artifact": "https://example.com/shot.png"},
    {"artifact": RUN + "/../../.env"},
    {"artifact": RUN + "/report.json"},
    {"artifact": RUN + "/99-unlisted.png"},
    {"sha256": "0" * 64},
    {"sha256": ""},
    {"recipient": "nobody"},
    {"recipient": "pike\n@juniper"},
    {"target": "f1"},
    {"prompt": "@juniper: also look"},
])
def test_invalid_selection_has_no_effect(fixture, change):
    d, kwargs, _, _ = fixture
    before = store.flatten(d.world)
    with pytest.raises(Refusal):
        artifacts.prepare(d.snapshot(), **(kwargs | change))
    assert store.flatten(d.world) == before


@pytest.mark.parametrize("guard", [None, [1, "alex: untouched by the sandbox (input desktop)"],
                                  [False, "alex: untouched by the sandbox (input desktop)"],
                                  [0, "not guarded"]])
def test_guard_failure_refuses(fixture, guard):
    d, kwargs, path, _ = fixture
    report = json.loads(path.read_text())
    report["guard"] = guard
    path.write_text(json.dumps(report))
    with pytest.raises(Refusal, match="Guard"):
        artifacts.prepare(d.snapshot(), **kwargs)


def test_provider_refusal_happens_before_file_access(fixture, monkeypatch):
    d, kwargs, _, _ = fixture
    snapshot = d.snapshot()
    resident = next(n for n in snapshot["nodes"].values()
                    if n.get("props", {}).get("actor") == "pike")
    resident["props"]["provider"] = "unsupported"
    monkeypatch.setattr(artifacts, "_read", Mock(side_effect=AssertionError("read too soon")))
    with pytest.raises(Refusal, match="provider"):
        artifacts.prepare(snapshot, **kwargs)
    resident["props"].update(provider="codex", model="text-only")
    monkeypatch.setattr(artifacts, "_codex_image_model", lambda _: False)
    with pytest.raises(Refusal, match="image-input"):
        artifacts.prepare(snapshot, **kwargs)


def test_replaced_after_guard_and_corrupt_png_refuse(fixture):
    d, kwargs, path, shot = fixture
    os.utime(shot, ns=(path.stat().st_mtime_ns + 10_000, ) * 2)
    with pytest.raises(Refusal, match="after"):
        artifacts.prepare(d.snapshot(), **kwargs)
    raw = b"not a png"
    shot.write_bytes(raw)
    os.utime(shot, ns=(1_000_000_000,) * 2)
    with pytest.raises(Refusal):
        artifacts.prepare(d.snapshot(), **(kwargs | {"sha256": hashlib.sha256(raw).hexdigest()}))


def test_existing_reviewed_codex_image_model():
    assert artifacts._codex_image_model("gpt-6-astra")


@pytest.mark.parametrize("size,animated", [((2049, 1), False), ((3, 3), True)])
def test_oversized_or_animated_images_refuse(fixture, size, animated):
    from PIL import Image
    d, kwargs, path, shot = fixture
    image = Image.new("RGB", size, "red")
    if animated:
        image.save(shot, save_all=True, append_images=[Image.new("RGB", size, "blue")])
    else:
        image.save(shot)
    os.utime(shot, ns=(1_000_000_000,) * 2)
    kwargs["sha256"] = hashlib.sha256(shot.read_bytes()).hexdigest()
    with pytest.raises(Refusal, match="2048px|static PNG"):
        artifacts.prepare(d.snapshot(), **kwargs)


def test_byte_limit_refuses(fixture):
    d, kwargs, _, shot = fixture
    shot.write_bytes(b"x" * (image_comments.MAX_BYTES + 1))
    os.utime(shot, ns=(1_000_000_000,) * 2)
    kwargs["sha256"] = hashlib.sha256(shot.read_bytes()).hexdigest()
    with pytest.raises(Refusal, match="byte limit"):
        artifacts.prepare(d.snapshot(), **kwargs)


def test_reparse_point_refuses(fixture, monkeypatch):
    d, kwargs, _, shot = fixture
    original = Path.lstat

    def lstat(path, *a, **kw):
        if path == shot:
            return SimpleNamespace(st_mode=0, st_file_attributes=0x400)
        return original(path, *a, **kw)
    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(Refusal, match="reparse"):
        artifacts.prepare(d.snapshot(), **kwargs)


def test_report_is_bounded_and_named_once(fixture):
    d, kwargs, path, _ = fixture
    report = json.loads(path.read_text())
    report["rows"] *= 2
    path.write_text(json.dumps(report))
    with pytest.raises(Refusal, match="listed once"):
        artifacts.prepare(d.snapshot(), **kwargs)
    path.write_bytes(b"x" * (artifacts.MAX_REPORT + 1))
    with pytest.raises(Refusal, match="byte limit"):
        artifacts.prepare(d.snapshot(), **kwargs)


@pytest.mark.parametrize("report", [[], {"rows": [None]}])
def test_malformed_report_refuses(fixture, report):
    d, kwargs, path, _ = fixture
    path.write_text(json.dumps(report))
    with pytest.raises(Refusal, match="schema"):
        artifacts.prepare(d.snapshot(), **kwargs)


def test_delivery_carries_recipient_and_source_revision_fences(fixture):
    d, kwargs, _, _ = fixture
    snapshot = d.snapshot()
    prepared = artifacts.prepare(snapshot, **kwargs)
    reads = prepared["observed"]["reads"]
    recipient = next(n for n in snapshot["nodes"].values()
                     if n.get("props", {}).get("actor") == "pike")
    assert [recipient["id"], recipient["rev"], []] in reads
    node = snapshot["nodes"][kwargs["target"]]
    subject = snapshot["subjects"][node["subject"]]
    assert [subject["id"], subject["rev"], []] in reads
    assert prepared["provenance"]["model"]  # Resolved house default, never unknown.


def test_cli_honors_worker_off_boundary(monkeypatch):
    monkeypatch.setenv("DESKD", "off")
    monkeypatch.setattr(sys, "argv", [
        "guarded_artifacts.py", RUN + "/" + SHOT, "--sha256", "0" * 64,
        "--recipient", "pike", "--target", "a20", "--prompt", "Describe it.",
        "--as", "worker-a7940", "--send",
    ])
    with pytest.raises(SystemExit) as failure:
        artifacts.main()
    assert failure.value.code == 2
