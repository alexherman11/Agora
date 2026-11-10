"""Sending selected attachments detaches them in the same native command."""

import copy
import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import message_context
import moo
import roomworld
import store
import worktree
from world import Refusal, World


@pytest.fixture
def case(monkeypatch):
    desk, _ = roomworld.build()
    desk._session = "frontier"
    w = desk.world
    w.me = "alex"
    chat = w.add_subject("chat", "Human feed")
    w.subjects[chat]["lines"] = []
    w.place(chat, w.root, 0, 0, 100, 100)
    sid = w.add_subject("note", "Composer", "An unfinished draft")
    w.subjects[sid]["props"].update(actor="alex", context="cap-1")
    draft = w.place(sid, w.root, 0, 0, 100, 100)
    capture = {
        "id": "cap-1",
        "session": "frontier",
        "by": "alex",
        "at": "2026-10-14",
        "refs": [
            {
                "world": "frontier",
                "item": draft,
                "subject": sid,
                "words": "Captured selection",
                "rev": w.nodes[draft]["rev"],
            }
        ],
        "image": None,
    }

    class CaptureError(Exception):
        pass

    service = SimpleNamespace(CaptureError=CaptureError, sent_copy=Mock(return_value=capture))
    monkeypatch.setitem(sys.modules, "captures", service)
    return SimpleNamespace(
        desk=desk, w=w, chat=chat, draft=draft, sid=sid, capture=capture, service=service
    )


def send(case, **changes):
    kv = {
        "line": "Please examine this",
        "to": "pike",
        "captures": "cap-1",
        "context_from": case.draft,
        **changes,
    }
    return case.desk.cmd_do_knife("append", [case.chat], kv)


def test_send_uses_native_events_and_hooks_see_both_changes(case):
    seen = []
    case.desk.hooks.append(
        lambda _: seen.append(
            (len(case.w.subjects[case.chat]["lines"]), moo.props_of(case.w, case.draft)["context"])
        )
    )
    n0 = len(case.w.events)
    send(case)
    line = case.w.subjects[case.chat]["lines"][-1]
    assert json.loads(line["fields"]["context"])["captures"][0]["id"] == "cap-1"
    assert "context_from" not in line["fields"] and "captures" not in line["fields"]
    assert moo.props_of(case.w, case.draft)["context"] == ""
    assert case.w.subjects[case.sid]["text"] == "An unfinished draft"
    assert [e["verb"] for e in case.w.events[n0:]] == ["edit", "prop"]
    assert seen == [(1, "")]
    assert case.sid in case.w.events[-1]["changed"]
    rebuilt = World()
    facts = store.flatten(case.w)
    store.apply(rebuilt, [(a, b, v) for (a, b), v in facts.items()])
    assert store.flatten(rebuilt) == facts


def test_selected_subset_preserves_newly_attached_ids_even_during_copy(case):
    def copy_and_attach(*args):
        moo.v_prop(case.w, case.draft, {"context": "cap-1 cap-2"})
        return case.capture

    case.service.sent_copy.side_effect = copy_and_attach
    send(case)
    assert moo.props_of(case.w, case.draft)["context"] == "cap-2"
    assert [
        c["id"]
        for c in json.loads(case.w.subjects[case.chat]["lines"][-1]["fields"]["context"])[
            "captures"
        ]
    ] == ["cap-1"]


def test_empty_observed_selection_sends_text_without_consuming_new_attachment(case):
    n0 = len(case.w.events)
    send(case, captures="")
    assert moo.props_of(case.w, case.draft)["context"] == "cap-1"
    assert [e["verb"] for e in case.w.events[n0:]] == ["edit"]
    assert "context" not in case.w.subjects[case.chat]["lines"][-1].get("fields", {})
    case.service.sent_copy.assert_not_called()


@pytest.mark.parametrize("problem", ["removed", "owner", "expired", "invalid_target", "implicit"])
def test_refused_send_keeps_draft_and_feed(case, problem):
    changes = {}
    if problem == "removed":
        case.w.subjects[case.sid]["props"]["context"] = "cap-2"
    elif problem == "owner":
        case.w.subjects[case.sid]["props"]["actor"] = "juniper"
    elif problem == "expired":
        case.service.sent_copy.side_effect = case.service.CaptureError("capture expired")
    elif problem == "invalid_target":
        changes["reply_to"] = "m999999"
    before = store.flatten(case.w)
    if problem == "implicit":
        with pytest.raises(Refusal, match="explicit observed"):
            case.desk.cmd_do_knife(
                "append", [case.chat], {"line": "A message", "context_from": case.draft}
            )
    else:
        with pytest.raises(Refusal):
            send(case, **changes)
    assert store.flatten(case.w) == before
    assert not case.w.subjects[case.chat]["lines"]


def test_detach_failure_rolls_back_append_before_hooks(case, monkeypatch):
    before, n0 = store.flatten(case.w), len(case.w.events)
    hook = Mock()
    case.desk.hooks.append(hook)
    monkeypatch.setattr(moo, "v_prop", Mock(side_effect=Refusal("injected detach refusal")))
    with pytest.raises(Refusal, match="detach refusal"):
        send(case)
    assert store.flatten(case.w) == before
    assert len(case.w.events) == n0
    assert case.desk.hooks == [hook]
    hook.assert_not_called()


def test_failed_hook_rolls_back_both_native_changes(case):
    before, n0 = store.flatten(case.w), len(case.w.events)
    case.desk.hooks.append(Mock(side_effect=Refusal("injected hook refusal")))
    with pytest.raises(Refusal, match="hook refusal"):
        send(case)
    assert store.flatten(case.w) == before
    assert len(case.w.events) == n0


def test_worktree_journal_replays_without_capture_store_and_preserves_other_ids(case):
    case.w.subjects[case.sid]["props"]["context"] = "cap-1 cap-2"
    original = copy.deepcopy(case.desk)
    case.desk._wt = {"journal": []}
    line = (
        f'do append {case.chat} line="Send this" to=pike captures="cap-1" context_from={case.draft}'
    )
    n0, ids = len(case.w.events), worktree.ids_of(case.desk)
    result = case.desk.dispatch("desk", {"line": line, "whole": True})
    assert not result.get("error"), result
    worktree.record(case.desk, line, "alex", ids, n0)
    journal = case.desk._wt["journal"][-1]
    assert "captures=" not in journal["line"]
    assert f'context_from="{case.draft}"' in journal["line"]
    assert {case.sid, case.draft} <= set(journal["touched"])
    case.service.sent_copy.side_effect = case.service.CaptureError("private capture deleted")
    replayed = original.dispatch("desk", {"line": journal["line"], "whole": True})
    assert not replayed.get("error"), replayed
    assert store.flatten(original.world) == store.flatten(case.w)
    assert moo.props_of(original.world, case.draft)["context"] == "cap-2"


def test_durable_send_detaches_only_intersection_on_replay(case):
    saved = message_context.resolve("frontier", "alex", "cap-1")
    case.w.subjects[case.sid]["props"]["context"] = "cap-2"
    case.service.sent_copy.side_effect = case.service.CaptureError("private capture deleted")
    n0 = len(case.w.events)
    case.desk.cmd_do_knife(
        "append", [case.chat], {"line": "Replay", "context": saved, "context_from": case.draft}
    )
    assert moo.props_of(case.w, case.draft)["context"] == "cap-2"
    assert [e["verb"] for e in case.w.events[n0:]] == ["edit"]


@pytest.fixture
def batch_case(case, monkeypatch):
    import verbs

    # Refusal diagnostics must stay in memory in these isolated replay tests.
    monkeypatch.setattr(verbs, "record_reach", lambda *args: None)
    case.desk.batch = True
    case.desk._wt = {"journal": []}
    case.w.subjects[case.sid]["props"]["context"] = "cap-1 cap-2"
    case.original = copy.deepcopy(case.desk)
    return case


def record_batch(case, line):
    n0, ids = len(case.w.events), worktree.ids_of(case.desk)
    result = case.desk.dispatch("desk", {"line": line})
    worktree.record(case.desk, line, "alex", ids, n0)
    assert not hasattr(case.desk, "_journal_dispatch")
    journal = case.desk._wt["journal"][-1]["line"]
    assert "captures=" not in journal
    case.service.sent_copy.side_effect = case.service.CaptureError("private capture deleted")
    replayed = case.original.dispatch("desk", {"line": journal})
    assert not replayed.get("error") and not replayed.get("batch_error"), replayed
    assert store.flatten(case.original.world) == store.flatten(case.w)
    return result, journal


def test_read_then_capture_append_batch_replays_after_private_capture_removed(batch_case):
    case = batch_case
    line = (
        f'read {case.chat}; do append {case.chat} line="Words; inside the message" '
        f'captures="cap-1" context_from={case.draft}'
    )
    result, journal = record_batch(case, line)
    assert not result["batch_error"]
    assert journal.startswith(f"read {case.chat}; do append {case.chat}")
    assert case.service.sent_copy.call_count == 1
    assert moo.props_of(case.original.world, case.draft)["context"] == "cap-2"


@pytest.mark.parametrize("second_id", ["cap-1", "cap-2"])
def test_two_capture_appends_to_same_chat_use_their_own_step_events(batch_case, second_id):
    case = batch_case

    def copied(session, actor, cid):
        return dict(case.capture, id=cid)

    case.service.sent_copy.side_effect = copied
    # Reusing a private capture in two separate sends is valid without consuming
    # a draft. The matching capture IDs and chat alone cannot identify the step.
    line = (
        f'read {case.chat}; do append {case.chat} line="First" captures="cap-1"; '
        f'do append {case.chat} line="Second" captures="{second_id}"'
    )
    result, _ = record_batch(case, line)
    assert not result["batch_error"]
    lines = case.original.world.subjects[case.chat]["lines"]
    assert [row["text"] for row in lines] == ["Alex: First", "Alex: Second"]
    assert [json.loads(row["fields"]["context"])["captures"][0]["id"] for row in lines] == [
        "cap-1",
        second_id,
    ]
    assert case.service.sent_copy.call_count == 2


def test_partial_capture_batch_records_only_successful_prefix(batch_case):
    case = batch_case
    line = (
        f'read {case.chat}; do append {case.chat} line="Sent" captures="cap-1" '
        f"context_from={case.draft}; "
        f'do append {case.chat} line="Refused" captures="cap-2" context_from={case.draft} '
        "reply_to=m999999; "
        f'do append {case.chat} line="Never attempted" captures="cap-2" '
        f"context_from={case.draft}"
    )
    case.service.sent_copy.side_effect = lambda session, actor, cid: dict(case.capture, id=cid)
    result, journal = record_batch(case, line)
    assert result["batch_error"]
    assert "Refused" not in journal and "Never attempted" not in journal
    assert moo.props_of(case.original.world, case.draft)["context"] == "cap-2"
    assert len(case.original.world.subjects[case.chat]["lines"]) == 1


def test_read_limit_does_not_journal_unrun_capture_send(batch_case):
    case = batch_case
    case.desk.read_cap = case.original.read_cap = 1
    line = (
        f'do append {case.chat} line="Sent" captures="cap-1" context_from={case.draft}; '
        f"read {case.chat}; read {case.chat}; "
        f'do append {case.chat} line="Not run" captures="cap-2" context_from={case.draft}'
    )
    result, journal = record_batch(case, line)
    assert "later command(s) not run" in result["text"]
    assert "Not run" not in journal
    assert case.service.sent_copy.call_count == 1


def test_failed_capture_after_ordinary_edit_is_not_journaled(batch_case):
    case = batch_case
    case.service.sent_copy.side_effect = case.service.CaptureError("capture unavailable")
    line = (
        f"read {case.draft}; do prop {case.draft} status=ready; "
        f'do append {case.chat} line="Refused" captures="cap-1" context_from={case.draft}'
    )
    result, journal = record_batch(case, line)
    assert result["batch_error"]
    assert "Refused" not in journal
    assert moo.props_of(case.original.world, case.draft)["status"] == "ready"
    assert not case.original.world.subjects[case.chat]["lines"]


def test_capture_batch_without_exact_dispatch_receipt_refuses_to_guess(batch_case):
    case = batch_case
    line = f'read {case.chat}; do append {case.chat} line="Sent" captures="cap-1"'
    n0 = len(case.w.events)
    case.desk.dispatch("desk", {"line": line})
    with pytest.raises(Refusal, match="dispatch receipt"):
        message_context.durable_command(line, case.w, case.w.events[n0:])
    with pytest.raises(Refusal, match="dispatch receipt"):
        message_context.durable_command(
            line, case.w, case.w.events[n0:], dispatch={"line": "different", "steps": []}
        )


def test_ambiguous_context_events_within_one_step_are_not_guessed(batch_case):
    case = batch_case
    line = f'read {case.chat}; do append {case.chat} line="Sent" captures="cap-1"'
    n0 = len(case.w.events)
    case.desk.dispatch("desk", {"line": line})
    dispatch = case.desk._journal_dispatch
    saved = case.w.subjects[case.chat]["lines"][-1]["fields"]["context"]
    case.w.apply("append", case.chat, None, {"line": "Rule copy", "context": saved}, "alex")
    dispatch["steps"][-1]["events"].append(case.w.events[-1]["id"])
    with pytest.raises(Refusal, match="one durable created context"):
        message_context.durable_command(line, case.w, case.w.events[n0:], dispatch=dispatch)


def test_deskd_duplicate_gesture_after_restart_does_not_resend_or_consume(
    case, monkeypatch, tmp_path
):
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
    line = f'do append {case.chat} line="Once" to=pike captures="cap-1" context_from={case.draft}'

    def post():
        body = json.dumps(
            {"session": "frontier", "as": "alex", "line": line, "gesture": "press-1"}
        ).encode()
        handler = deskd.Handler.__new__(deskd.Handler)
        handler.path, handler.headers = "/api/do", {"Content-Length": str(len(body))}
        handler.rfile, handler._json = io.BytesIO(body), Mock()
        handler._post()
        return handler._json.call_args.args[0]

    result = post()
    assert not result.get("error"), result
    assert len(case.w.subjects[case.chat]["lines"]) == 1
    # Preserve native durable state but discard any request-local Python objects.
    case.desk = copy.deepcopy(case.desk)
    case.w = case.desk.world
    case.w.subjects[case.sid]["props"]["context"] = "cap-2"
    case.service.sent_copy.side_effect = case.service.CaptureError("capture unavailable")
    result = post()
    assert result["already"]
    assert len(case.w.subjects[case.chat]["lines"]) == 1
    assert moo.props_of(case.w, case.draft)["context"] == "cap-2"
    assert case.service.sent_copy.call_count == 1
