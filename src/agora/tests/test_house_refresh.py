"""Fresh conversations in private worlds, with both transport commands and fake children.

No live resident, model, provider settings, credential or window is touched.
"""
import copy
import json
import queue
import shlex
import threading
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from test_next_steps import load_house, say, world  # noqa: F401


class Child:
    def __init__(self, cmd, cwd, env, events, log):
        self.cmd, self.events, self.log = cmd, events, log
        self.proc = SimpleNamespace(pid=123)
        self.running, self.sent = True, []

    def alive(self):
        return self.running

    def stop(self):
        self.running = False

    def send(self, text):
        self.sent.append(text)
        self.log("fixture-input", text)
        return True


@pytest.fixture
def resident(world, tmp_path, monkeypatch):
    k, owner, person, outsider = world
    mod = load_house()
    monkeypatch.setattr(mod.T, "Child", Child)
    monkeypatch.setattr(mod.T, "find_claude", lambda: "fixture-claude")
    h = mod.House.__new__(mod.House)
    h.home = tmp_path
    h.m = SimpleNamespace(see=lambda line, **kw: k.run(owner, line, mode="see"))
    h.publish, h.mark_turn, h.refresh_card_signals = Mock(), Mock(), Mock()
    h.token_for = lambda signer: "private-fixture-token"
    h.next_steps = lambda agent: "Current task context"
    h.builders = SimpleNamespace(states={}, steward=lambda p: p == owner.person,
                                 alex=lambda p: p == owner.person, owner_turn_ended=Mock())
    h.ready = threading.Event()
    h.ready.set()
    cfg = dict(name="Fixture resident", person=person.person, id="fixture-agent",
               signer="fixture", provider="codex", model="fixture-model", reasoning="medium",
               speaks="text", want="awake", wake_policy="addressed", next_steps="on",
               fallback_provider="claude", fallback_model="fixture-fallback")
    for field in ("prompt", "charter", "guide", "soul"):
        cfg[field] = say(k, owner, f'make kind=document name="{field}" text="old {field}"')["made"][0]
    a = mod.Agent.__new__(mod.Agent)
    a.house, a.cfg, a.name = h, cfg, cfg["name"]
    a.dir = tmp_path / "agent"
    a.dir.mkdir()
    a.state_path = a.dir / "state.json"
    a.lock, a.events = threading.RLock(), queue.Queue()
    a.state = dict(cursor=12, turns=3, card_signals_seen=["seen-note"])
    a.child, a.busy, a.inbox, a.turn = None, False, [], {}
    h.agents = {person.person: a}
    return mod, h, a, k, owner, outsider


def refresh_call(h, a, owner):
    return h.call(dict(word="house.refresh", args={"target": a.person},
                       caller={"person": owner.person, "name": "Fixture owner"}))


def change_context(k, owner, a):
    for field in ("prompt", "charter", "guide", "soul"):
        say(k, owner, f"look {a.cfg[field]}")
        say(k, owner, f'set {a.cfg[field]} text="current {field}"')
    book = say(k, owner, 'look "Agent Book"')["rows"][0]
    say(k, owner, f'set {book["id"]} text='
        + shlex.quote(book["text"].replace("You are $.name", "Current welcome: you are $.name")))


@pytest.mark.parametrize("provider", ["codex", "claude"])
def test_next_wake_has_current_context_without_resume_and_keeps_history(resident, provider):
    mod, h, a, k, owner, _ = resident
    a.cfg["provider"] = provider
    a.start()
    old = a.child
    a._event({"e": "init", "session": "old-conversation", "child": old})
    a.wake("old request")
    a._event({"e": "result", "ok": True, "detail": "", "child": old})
    assert "old soul" in old.sent[0]
    previous = (a.dir / "transcript.jsonl").read_bytes()
    previous_state, config = copy.deepcopy(a.state), copy.deepcopy(a.cfg)
    change_context(k, owner, a)

    a.refresh()
    new = a.child
    assert not old.alive() and new is not old
    assert "--resume" not in new.cmd and "old-conversation" not in new.cmd
    assert not new.sent                             # an idle refresh spends no model turn
    assert a.cfg == config
    assert (a.dir / "transcript.jsonl").read_bytes().startswith(previous)
    archive = list((a.dir / "conversations").glob("*.json"))
    assert len(archive) == 1
    assert json.loads(archive[0].read_text(encoding="utf-8")) == previous_state
    saved = json.loads(a.state_path.read_text(encoding="utf-8"))
    assert "session" not in saved
    for key in ("cursor", "turns", "card_signals_seen"):
        assert a.state[key] == previous_state[key]
    a._event({"e": "init", "session": "new-conversation", "child": new})
    a.wake("new request")
    sent = new.sent[0]
    assert all(text in sent for text in ("current soul", "current guide", "Current welcome",
                                         "Current task context", "new request"))
    assert all(text not in sent for text in ("old soul", "old guide", "old request"))
    system = (a.dir / "charter.txt").read_text(encoding="utf-8")
    assert "current prompt" in system and "current charter" in system
    assert "old prompt" not in system and "old charter" not in system
    assert a.state["session"] == "new-conversation"
    assert a.cfg == config


def test_busy_refresh_replays_only_pending_messages_with_chat_boundaries(resident):
    mod, h, a, k, owner, _ = resident
    a.start()
    old = a.child
    a.wake("unfinished private question", chat="private", record=20)
    a.wake("public question waiting", chat="public", record=21)
    change_context(k, owner, a)
    a.refresh()
    new = a.child
    assert not old.alive()
    assert a.turn["chat"] == "private"
    assert "unfinished private question" in new.sent[0]
    assert "current soul" in new.sent[0] and "old soul" not in new.sent[0]
    assert "public question" not in new.sent[0]
    assert a.state["cursor"] == 20
    assert a.state["paused"][0]["text"] == "public question waiting"
    a._event({"e": "result", "ok": True, "detail": "", "child": new})
    assert a.turn["chat"] == "public" and len(new.sent) == 2
    assert "public question waiting" in new.sent[1]
    assert "unfinished private question" not in new.sent[1]
    assert a.state["cursor"] == 21 and "paused" not in a.state


@pytest.mark.parametrize("event", [
    {"e": "init", "session": "stale"},
    {"e": "text", "text": "old soul's answer"},
    {"e": "tool", "name": "do", "input": {"line": "stale receipt"}},
    {"e": "toolresult", "refused": 1},
    {"e": "compacted"},
    {"e": "result", "ok": False, "detail": "plan limit resets tomorrow"},
    {"e": "exit", "code": 1},
])
def test_every_late_event_from_old_process_is_ignored(resident, event):
    mod, h, a, _, _, _ = resident
    a.start()
    old = a.child
    a.refresh()
    new = a.child
    a.wake("current question", chat="private")
    state, turn = copy.deepcopy(a.state), copy.deepcopy(a.turn)
    a._spoke = Mock()
    a._event(dict(event, child=old))
    assert a.child is new and a.busy
    assert a.state == state and a.turn == turn and len(new.sent) == 1
    a._spoke.assert_not_called()


def test_sleeping_refresh_retains_queue_and_fallback_without_starting(resident):
    mod, h, a, _, _, _ = resident
    a.cfg["want"] = "asleep"
    a.state.update(session="old-thread", session_provider="codex", on_fallback="retained",
                   fallback_from=["codex", "fixture-model"], quota="retained")
    config = copy.deepcopy(a.cfg)
    a.wake("pending while asleep")
    a.refresh()
    assert a.child is None and a.doing() == "asleep"
    assert "session" not in a.state and a.state["on_fallback"] == "retained"
    assert a.state["paused"][0]["text"] == "pending while asleep"
    assert a.cfg == config
    a.cfg["want"] = "awake"
    a.wake("awake now")
    assert "--resume" not in a.child.cmd
    assert all(text in a.child.sent[0] for text in ("pending while asleep", "awake now", "old soul"))


def test_failed_start_keeps_fresh_state_and_pending_work_for_recovery(resident, monkeypatch):
    mod, h, a, _, _, _ = resident
    a.start()
    a.wake("unfinished request")
    a.wake("queued request")
    monkeypatch.setattr(mod.T, "Child", Mock(side_effect=OSError("fixture startup failure")))
    a.refresh()
    assert a.child is None and a.doing() == "error"
    saved = json.loads(a.state_path.read_text(encoding="utf-8"))
    assert "session" not in saved and saved["welcome_due"]
    assert len(saved["paused"]) == 2
    assert "unfinished request" in saved["paused"][0]["text"]
    monkeypatch.setattr(mod.T, "Child", Child)
    a._begin()
    assert "--resume" not in a.child.cmd
    assert "unfinished request" in a.child.sent[0] and "queued request" in a.child.sent[0]
    assert "paused" not in a.state


def test_house_restart_recovers_the_refresh_queue_without_resuming_old_thread(resident):
    mod, h, a, _, _, _ = resident
    a.start()
    a._event({"e": "init", "session": "old-thread", "child": a.child})
    a.wake("unfinished request", record=20)
    a.wake("queued wake without record")
    a.cfg["want"] = "asleep"
    a.refresh()
    assert a.child is None
    restored = copy.copy(a)
    restored.state = json.loads(a.state_path.read_text(encoding="utf-8"))
    restored.lock, restored.events, restored.inbox = threading.RLock(), queue.Queue(), []
    restored.cfg = dict(a.cfg, want="awake")
    h.card_signals = Mock()
    h.catch_up(restored)
    assert "--resume" not in restored.child.cmd
    sent = restored.child.sent[0]
    assert sent.count("unfinished request") == 1 and sent.count("queued wake without record") == 1
    assert "paused" not in restored.state


def test_house_off_keeps_refreshed_cut_turn_and_queued_wake_exactly_once(resident, monkeypatch):
    mod, h, a, _, _, _ = resident
    a.start()
    a.wake("cut recorded turn", record=20)
    a.wake("pending report without a record")
    a.cfg["want"] = "asleep"
    a.refresh()
    h.builders = None
    monkeypatch.setattr(mod.os, "_exit", lambda code: None)
    h.off()
    saved = json.loads(a.state_path.read_text(encoding="utf-8"))
    assert saved["cursor"] == 20 and "in_flight" not in saved
    assert len(saved["paused"]) == 2
    assert saved["paused"][0]["record"] == 20
    assert "cut recorded turn" in saved["paused"][0]["text"]
    assert saved["paused"][1]["text"] == "pending report without a record"


def test_archive_failure_leaves_existing_conversation_running(resident):
    mod, h, a, _, _, _ = resident
    a.start()
    old = a.child
    a.state["session"] = "old-thread"
    # A file at the archive directory's path prevents preservation.
    (a.dir / "conversations").write_text("fixture obstruction", encoding="utf-8")
    a.refresh()
    assert a.child is old and old.alive()
    assert a.state["session"] == "old-thread"
    assert "could not refresh" in a.state["error"]


def test_a_process_that_did_not_stop_is_not_replaced(resident):
    mod, h, a, _, _, _ = resident
    a.start()
    old = a.child
    a.state["session"] = "old-thread"
    old.stop = lambda: None
    a.refresh()
    assert a.child is old and a.state["session"] == "old-thread"
    assert "old process has not ended" in a.state["error"]


def test_command_is_steward_only_and_returns_before_slow_shutdown(resident):
    mod, h, a, _, owner, outsider = resident
    a.start()
    old = a.child
    started, release, finished = threading.Event(), threading.Event(), threading.Event()
    real_refresh = a.refresh

    def stop():
        started.set()
        assert release.wait(5)
        old.running = False

    def refresh():
        try:
            real_refresh()
        finally:
            finished.set()

    old.stop, a.refresh = stop, refresh
    assert "refused" in refresh_call(h, a, outsider)
    assert old.alive() and not started.is_set()
    try:
        result = refresh_call(h, a, owner)
        assert result["external"] and "requested" in result["text"]
        assert started.wait(2) and not finished.is_set()
        assert a.doing() == "refreshing"
        assert "already underway" in refresh_call(h, a, owner)["text"]
    finally:
        release.set()
        assert finished.wait(5)
    assert a.child is not old and not old.alive() and "--resume" not in a.child.cmd


def test_word_is_offered_as_external_person_operation(resident):
    mod, h, a, k, owner, outsider = resident
    mid = say(k, owner, 'module house run=' + shlex.quote('["unused-fixture-only"]')
              + ' grants="look rows"')["made"][0]
    offer = next(word for word in mod.OFFER if word["word"] == "house.refresh")
    assert k.on_offer(mid, [offer])[0].startswith("published")
    entry = k.find_entry("house.refresh")
    assert k.state.get(entry, "undo") == "external"
    assert k.state.get(entry, "needs") == "kind=person"
    assert k.state.get(entry, "may") == "stewards"
    assert "fresh context" in say(k, owner, "help house.refresh")["text"]
    denied = say(k, outsider, f"house.refresh {a.person}", ok=False)
    assert "steward" in denied["text"]
    unknown = h.call(dict(word="house.refresh", args={"target": "not-an-agent"},
                          caller={"person": owner.person}))
    assert "refused" in unknown
    a.start()
    old = a.child
    finished = threading.Event()
    real_refresh = a.refresh

    def refresh():
        try:
            real_refresh()
        finally:
            finished.set()

    a.refresh = refresh
    k.modules = SimpleNamespace(
        running=lambda mid: True, deliver=lambda event: None, reconcile=lambda: None,
        call=lambda mid, word, args, caller: h.call(
            dict(word=word, args=args, caller={"person": caller.person})))
    out = say(k, owner, "house.refresh " + shlex.quote(k.name(a.person)))
    assert "requested" in out["text"] and finished.wait(5)
    assert a.child is not old and not old.alive()
    assert "--resume" not in a.child.cmd
    assert k.log.records[-1]["external"] is True
    say(k, owner, "undo " + out["records"][0], ok=False)
