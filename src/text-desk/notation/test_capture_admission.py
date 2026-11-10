"""Actual native engine, synthetic feed only. No private capture store or host."""
import copy
import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import message_context
import moo
import store
import worktree
from world import Refusal
from test_message_context_lifecycle import case


def send(case, **changes):
    return case.desk.cmd_do_knife("append", [case.chat], {
        "line": "Fixture words", "to": "pike", "context_from": case.draft,
        "captures": "current", "capture_generation": "0", **changes,
    })


def props(case):
    return moo.props_of(case.w, case.draft)


def compare_write(case, **changes):
    p = props(case)
    args = {
        "capture_if_generation": str(p.get("capture_generation") or "0"),
        "capture_if_context": str(p.get("context") or ""),
        "capture_if_pending": str(p.get("pending") or ""),
        "context": str(p.get("context") or ""),
        "pending": "wait-1-1", **changes,
    }
    case.desk.dispatch("desk", {"line": f"examine {case.draft}"})
    return case.desk.cmd_do_knife("prop", [case.draft], args)


def assert_refused_unchanged(case, run, match):
    before, n0 = store.flatten(case.w), len(case.w.events)
    with pytest.raises(Refusal, match=match):
        run()
    assert store.flatten(case.w) == before
    assert len(case.w.events) == n0


def test_current_capture_selected_despite_empty_painted_selection(case):
    send(case)
    line = case.w.subjects[case.chat]["lines"][-1]
    assert line["to"] == ["pike"]
    assert json.loads(line["fields"]["context"])["captures"][0]["id"] == "cap-1"
    assert props(case)["context"] == ""
    assert props(case)["capture_generation"] == "1"
    assert "capture_generation" not in line.get("fields", {})


def test_pending_refusal_keeps_text_attachments_and_events(case):
    compare_write(case)
    case.service.sent_copy.reset_mock()
    assert_refused_unchanged(case, lambda: send(case), "still attaching")
    case.service.sent_copy.assert_not_called()
    assert case.w.subjects[case.sid]["text"] == "An unfinished draft"


def test_late_capture_then_send_has_one_joined_line(case):
    case.w.subjects[case.sid]["props"]["context"] = ""
    compare_write(case)
    assert_refused_unchanged(case, lambda: send(case), "still attaching")
    compare_write(case, context="cap-1", pending="")
    send(case)
    assert len(case.w.subjects[case.chat]["lines"]) == 1
    assert props(case)["capture_generation"] == "1"
    assert_refused_unchanged(case, lambda: send(case), "another message")


def test_no_attachment_send_advances_generation(case):
    case.w.subjects[case.sid]["props"]["context"] = ""
    send(case)
    case.service.sent_copy.assert_not_called()
    assert props(case)["capture_generation"] == "1"
    assert "context" not in case.w.subjects[case.chat]["lines"][-1].get("fields", {})


def test_plain_send_no_capture_matches_ordinary_append_receipt_and_immediate_path(case):
    """Unactivated lens Send retains main's ordinary synchronous append path."""
    case.w.subjects[case.sid]["props"].update(context="", pending="")
    ordinary = copy.deepcopy(case.desk)
    observations = []
    case.desk.hooks.append(lambda _: observations.append("append"))
    n0 = len(case.w.events)
    got = case.desk.cmd_do_knife("append", [case.chat], {
        "line": "Fixture words", "to": "pike", "captures": "",
        "context_from": case.draft,
    })
    expected = ordinary.cmd_do_knife("append", [case.chat], {
        "line": "Fixture words", "to": "pike",
    })
    assert got == expected
    assert observations == ["append"]
    assert [e["verb"] for e in case.w.events[n0:]] == ["edit"]
    assert props(case).get("capture_generation") is None
    assert case.w.subjects[case.chat]["lines"][-1].get("fields", {}) == \
        ordinary.world.subjects[case.chat]["lines"][-1].get("fields", {})
    case.service.sent_copy.assert_not_called()


def test_two_captures_and_removal_use_current_list(case):
    case.w.subjects[case.sid]["props"]["context"] = "cap-1 cap-2"
    case.service.sent_copy.side_effect = lambda s, a, cid: dict(case.capture, id=cid)
    # Removal is honored even though the original scene listed both.
    compare_write(case, context="cap-2", pending="")
    send(case)
    got = json.loads(case.w.subjects[case.chat]["lines"][-1]["fields"]["context"])
    assert [c["id"] for c in got["captures"]] == ["cap-2"]
    assert props(case)["context"] == ""


@pytest.mark.parametrize("field,value", [
    ("capture_if_generation", "1"),
    ("capture_if_context", ""),
    ("capture_if_pending", "wait-9-9"),
])
def test_explicit_publication_fences_refuse_stale_read(case, field, value):
    assert_refused_unchanged(case, lambda: compare_write(case, **{field: value}), "changed since")


def test_old_generation_publication_cannot_join_next_message(case):
    send(case)
    assert_refused_unchanged(case, lambda: compare_write(
        case, capture_if_generation="0", context="cap-2", pending=""
    ), "changed since")


def test_publication_cannot_change_topic_or_generation(case):
    assert_refused_unchanged(case, lambda: compare_write(case, to="juniper"), "only context")
    assert_refused_unchanged(case, lambda: compare_write(case, capture_generation="9"), "only context")


def test_wrong_actor_refused_without_mutation(case):
    case.w.subjects[case.sid]["props"]["actor"] = "juniper"
    assert_refused_unchanged(case, lambda: send(case), "another actor")
    assert_refused_unchanged(case, lambda: compare_write(case), "another actor")


def test_reply_is_original_and_invalid_reply_never_substituted(case):
    assert_refused_unchanged(case, lambda: send(case, reply_to="m999999"), "reply")
    assert props(case).get("capture_generation") is None


@pytest.mark.parametrize("failure", ["copy", "detach", "hook"])
def test_failure_before_or_after_append_restores_generation(case, monkeypatch, failure):
    if failure == "copy":
        case.service.sent_copy.side_effect = case.service.CaptureError("fixture copy failure")
    elif failure == "detach":
        monkeypatch.setattr(moo, "v_prop", Mock(side_effect=Refusal("fixture detach failure")))
    else:
        case.desk.hooks.append(Mock(side_effect=Refusal("fixture hook failure")))
    assert_refused_unchanged(case, lambda: send(case), "fixture")


def test_hooks_see_joint_result_and_only_once(case):
    observations = []
    case.desk.hooks.append(lambda _: observations.append((
        len(case.w.subjects[case.chat]["lines"]),
        props(case)["context"], props(case)["capture_generation"],
    )))
    send(case)
    assert observations == [(1, "", "1")]


@pytest.mark.parametrize("empty", [False, True])
def test_journal_freezes_current_selection_and_replays_without_private_store(case, empty):
    if empty:
        case.w.subjects[case.sid]["props"]["context"] = ""
    original = copy.deepcopy(case.desk)
    case.desk._wt = {"journal": []}
    line = (f'do append {case.chat} line="Fixture" to=pike captures=current '
            f'context_from={case.draft} capture_generation=0')
    n0, ids = len(case.w.events), worktree.ids_of(case.desk)
    result = case.desk.dispatch("desk", {"line": line, "whole": True})
    assert not result.get("error"), result
    worktree.record(case.desk, line, "alex", ids, n0)
    journal = case.desk._wt["journal"][-1]["line"]
    assert "current" not in journal
    case.service.sent_copy.side_effect = case.service.CaptureError("private store forbidden")
    result = original.dispatch("desk", {"line": journal, "whole": True})
    assert not result.get("error"), result
    assert store.flatten(original.world) == store.flatten(case.w)


def painter_send(case):
    """Compile the real action/fence; no hand-authored observed revision."""
    import lens_ir
    import scene
    case.w.subjects[case.sid]["props"]["role"] = "capture-fixture-draft"
    src = f'''root : column
  of prop:role=capture-fixture-draft as draft
  each writing
writing : column
  say : text ""
    commit explicit
    waits "$draft.pending" "capture"
    on edit do append {case.chat} line="$value" to="$draft.to" captures=current context_from="$draft" capture_generation="$(($draft.capture_generation or "0"))"
'''
    sc = lens_ir.evaluate(case.desk, src)
    scene.emit(sc)
    return scene.painter_view(sc)["kids"][0]["kids"][0]


def fixture_handler(case, monkeypatch, tmp_path):
    import deskd

    class Session:
        def __init__(self, name, actor):
            self.name, self.actor, self.path, self.per = name, actor, tmp_path / "world.pickle", {}

        def __enter__(self):
            return case.desk

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(deskd, "Session", Session)
    monkeypatch.setattr(store, "safe_begin", lambda *args: None)
    monkeypatch.setattr(store, "safe_commit", lambda *args: None)

    def post(node, gesture="fixture-send"):
        action = next(a for a in node["acts"] if a["on"] == "edit")
        body = json.dumps({"session": "frontier", "as": "alex",
                           "line": action["line"].replace("$value", "Fixture words"),
                           "observed": node["fence"], "gesture": gesture}).encode()
        h = deskd.Handler.__new__(deskd.Handler)
        h.path, h.headers = "/api/do", {"Content-Length": str(len(body))}
        h.rfile, h._json = io.BytesIO(body), Mock()
        h._post()
        return h._json.call_args.args[0]
    return post


def test_original_painted_send_survives_attachment_completion(case, monkeypatch, tmp_path):
    case.w.subjects[case.sid]["props"].update(pending="wait-1-1", context="", to="pike")
    node = painter_send(case)
    assert node["paint"]["waits"] == "wait-1-1"
    compare_write(case, pending="", context="cap-1")
    post = fixture_handler(case, monkeypatch, tmp_path)
    result = post(node)
    assert not result.get("error"), result
    assert len(case.w.subjects[case.chat]["lines"]) == 1
    assert case.w.subjects[case.chat]["lines"][-1]["to"] == ["pike"]
    # A repeated request must not consume a later generation.
    result = post(node)
    assert result["already"]
    assert props(case)["capture_generation"] == "1"


def test_changed_audience_refuses_original_action_without_substitution(case, monkeypatch, tmp_path):
    case.w.subjects[case.sid]["props"].update(pending="wait-1-1", to="pike")
    node = painter_send(case)
    case.desk.dispatch("desk", {"line": f"examine {case.draft}"})
    changed = case.desk.dispatch("desk", {"line": f'do prop {case.draft} to=juniper pending=""'})
    assert not changed.get("error"), changed
    assert node["fence"].get("reads"), node
    before = copy.deepcopy(store.flatten(case.w))
    events = copy.deepcopy(case.w.events)
    result = fixture_handler(case, monkeypatch, tmp_path)(node)
    assert "changed since this was painted" in result.get("error", ""), result
    assert store.flatten(case.w) == before
    assert case.w.events == events
    assert not case.w.subjects[case.chat].get("lines")
    case.service.sent_copy.assert_not_called()


def native_producer(case):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "desktop" / "capture"))
    import capture

    def door(line):
        result = case.desk.dispatch("desk", {"line": line, "whole": True})
        return not result.get("error"), result.get("text", "") + result.get("error", "")

    return capture, SimpleNamespace(draft=case.draft, who="alex", do=door)


def test_host_reservations_deliver_through_real_prop_admission(case):
    case.w.subjects[case.sid]["props"]["context"] = ""
    capture, args = native_producer(case)
    a, b = capture.Pending(args), capture.Pending(args)
    a.mark()
    b.mark()
    assert a.admitted and b.admitted
    assert_refused_unchanged(case, lambda: send(case), "still attaching")
    assert capture.deliver("cap-2", args, b)[0]
    assert_refused_unchanged(case, lambda: send(case), "still attaching")
    assert capture.deliver("cap-1", args, a)[0]
    case.service.sent_copy.side_effect = lambda s, actor, cid: dict(case.capture, id=cid)
    send(case)
    payload = json.loads(case.w.subjects[case.chat]["lines"][-1]["fields"]["context"])
    assert [c["id"] for c in payload["captures"]] == ["cap-2", "cap-1"]
    assert props(case)["pending"] == ""
    assert not capture.deliver("cap-1", args, a)[0]


def test_cancel_then_send_rejects_old_host_generation(case):
    case.w.subjects[case.sid]["props"]["context"] = ""
    capture, args = native_producer(case)
    reservation = capture.Pending(args)
    reservation.mark()
    assert reservation.admitted and reservation.generation == "0"
    assert reservation.drop()[0]
    send(case)
    before = store.flatten(case.w)
    assert not capture.deliver("cap-1", args, reservation)[0]
    assert store.flatten(case.w) == before
