"""Narrow resident provider handover with fake transports and disposable worlds."""

import copy
import io
import json
from pathlib import Path
from unittest.mock import Mock

import house
import image_comments
import pytest
import roomworld
import workshop


@pytest.fixture
def portable(tmp_path, monkeypatch):
    desk, refs = roomworld.build()
    w = desk.world
    rid = refs.corner["pike"]
    props = w.nodes[rid]["props"]
    props.update(provider="claude", model="claude-opus-5-5", handover="portable")
    h = house.House.__new__(house.House)
    h.dir, h.world, h.fake, h.claude = tmp_path, "portable-fixture", False, "claude.exe"
    h.load = lambda: w
    h.act = Mock(return_value="Full current soul and wake notes")
    h.welcome_for = lambda resident: "Pike's unchanged identity and memory notes"
    h.settings = lambda world: dict(house.DEFAULTS, timers="off")
    h.corners = lambda world: {rid: w.nodes[rid]}
    h.record_knocks = lambda world, corners: world
    h.toasts, h.beat, h.set_status = Mock(), Mock(), Mock()
    h.workshop = Mock(restart_wanted=False)
    h.feeds, h.usage, h.plans, h.scripts = Mock(), Mock(), Mock(), Mock()
    h.plans.wait_until.return_value = 0
    r = house.Resident(h, rid)
    h.residents = {rid: r}
    r.state = {"session": "old-codex-token", "session_provider": "codex",
               "session_model": "gpt-6.1-sol", "cursor": len(w.events),
               "charter_text": "old charter", "wake_read": {"soul": 123}}
    r.save()
    monkeypatch.setattr(house.charter, "collect", lambda *args: "Current start charter")
    monkeypatch.setattr(house.charter, "drain_channel", lambda *args: None)
    monkeypatch.setattr(house.Resident, "_charter_channel", lambda self: setattr(
        self, "charter_channel", self.dir / "test-channel"))
    monkeypatch.setattr(house.charter, "claude_hook", lambda *args: {})
    monkeypatch.setattr(house.threading, "Thread", Mock())
    monkeypatch.setattr(house, "clean_env", lambda fake: {})
    monkeypatch.setattr(image_comments, "content", lambda world, refs: [])
    spawned = []

    def popen(args, **kwargs):
        kwargs["stderr"].close()
        proc = Mock(pid=100 + len(spawned), stdin=io.StringIO())
        proc.poll.return_value = None
        spawned.append((args, proc))
        return proc

    monkeypatch.setattr(house.subprocess, "Popen", popen)
    return h, r, props, spawned


def test_opt_in_is_checked_before_pending_or_handoff_consumption(portable):
    _, r, props, spawned = portable
    props.pop("handover")
    r.state.update(pending={"carry": "pending input", "delivered": True},
                   handoff={"carry": "drained inbox"})
    before = copy.deepcopy(r.state)
    with pytest.raises(ValueError, match="handover=portable"):
        r.start(props["model"])
    assert r.state == before and not spawned
    assert not (r.dir / "provider-history").exists()


def test_archive_and_portable_packet_keep_full_unresolved_text_and_references(portable):
    _, r, props, spawned = portable
    long_request = "x" * 31000 + "PENDING END"
    staged = "y" * 28000 + "HANDOFF END"
    r.state.update(pending={"carry": long_request, "delivered": True,
                            "image_comments": ["c1"], "message_contexts": ["m1"]},
                   handoff={"carry": staged, "image_comments": ["c2"]},
                   undelivered="Never delivered receipt", inbox=["still queued"],
                   retry_at=9999999999, retry_kind="limit")
    before = copy.deepcopy(r.state)
    r.start(props["model"])
    assert json.loads(Path(r.state["previous_provider_state"]).read_text()) == before
    assert long_request in r.state["handover_due"] and staged in r.state["handover_due"]
    assert "Never delivered receipt" in r.state["handover_due"]
    assert r.state["image_comments"] == ["c1", "c2"]
    assert r.state["message_contexts"] == ["m1"]
    assert r.state["inbox"] == ["still queued"]
    assert not any(k in r.state for k in ("session", "wake_read", "retry_at", "pending"))
    assert "--resume" not in spawned[0][0]
    assert spawned[0][0][0] == "claude.exe"


def test_same_provider_resume_retains_its_token(portable):
    _, r, props, spawned = portable
    props.update(provider="codex", model="gpt-6.1-sol")
    r.start(props["model"])
    assert spawned[0][0][-2:] == ["--resume", "old-codex-token"]
    assert not (r.dir / "provider-history").exists()


def test_configuration_change_parks_receipt_instead_of_another_old_turn(portable):
    _, r, _, spawned = portable
    r.proc = Mock()
    r.send("Done once; inspect result before more work", "receipt")
    r.proc.stdin.write.assert_not_called()
    assert "Done once" in r.state["undelivered"]
    assert not r.busy and not spawned


def test_worker_send_without_resident_corner_is_not_a_provider_switch(portable):
    h, _, _, _ = portable
    worker = workshop.Worker(h, "test-card", h.dir, "test-branch", "pike")
    worker.state.update(session="worker-thread", session_provider="codex")
    worker.proc = Mock(stdin=io.StringIO())
    worker.send("Continue the assigned task", "news")
    assert "Continue the assigned task" in worker.proc.stdin.getvalue()
    assert worker.busy and "undelivered" not in worker.state


def test_packet_survives_error_and_clears_only_successful_sent_generation(portable):
    h, r, props, _ = portable
    r.start(props["model"])
    r.send("You are Pike. Full soul follows.", "wake")
    sent = json.loads(r.proc.stdin.getvalue())["message"]["content"][0]["text"]
    assert "Provider handover" in sent and "Full soul follows" in sent
    assert "unchanged identity" in sent
    r.events.put({"type": "result", "is_error": True, "subtype": "timeout"})
    assert r.turns_ended()[0]["error"] == "timeout"
    assert r.state["handover_due"]
    # A subsequent successfully completed turn is the acknowledgement boundary.
    r.events.put({"type": "result", "is_error": False})
    r.turns_ended()
    assert "handover_due" not in r.state
    assert "handover_unanswered" not in r.state
    assert not h.act.called


def test_delivered_failed_input_survives_later_switch_in_full(portable):
    _, r, props, _ = portable
    unresolved = "z" * 32000 + "END OF FAILED INPUT"
    r.hold_unanswered({"carry": unresolved, "delivered": True,
                       "image_comments": ["c1"], "message_contexts": ["m1"]}, "timeout")
    r.start(props["model"])
    assert unresolved in r.state["handover_due"]
    assert r.state["image_comments"] == ["c1"] and r.state["message_contexts"] == ["m1"]


def test_scheduler_switches_idle_transport_without_old_quota_delay(portable):
    h, r, _, spawned = portable
    r.state.update(retry_at=9999999999, retry_kind="limit", at_rest=True)
    old = Mock()
    old.poll.return_value = None
    r.proc = old
    h.wake = Mock()
    h.step()
    old.stdin.close.assert_called_once()
    assert len(spawned) == 1 and "--resume" not in spawned[0][0]
    h.wake.assert_called_once()
    assert r.state["session_provider"] == "claude"
    assert "retry_at" not in r.state


def test_scheduler_waits_for_busy_turn_and_refuses_nonportable_switch(portable):
    h, r, props, spawned = portable
    r.busy = True
    r.proc = Mock()
    r.proc.poll.return_value = None
    h.step()
    assert not spawned
    r.proc.stdin.close.assert_not_called()
    r.busy = False
    props.pop("handover")
    h.step()
    assert not spawned and r.state["session"] == "old-codex-token"
    assert "handover=portable" in r.state["provider_error"]
    r.proc.stdin.close.assert_not_called()


def test_scheduler_first_new_turn_includes_full_wake_and_portable_context(portable):
    h, r, _, spawned = portable
    r.state["pending"] = {"carry": "Finish the person's request", "delivered": True}
    h.step()
    assert len(spawned) == 1
    content = json.loads(r.proc.stdin.getvalue())["message"]["content"][0]["text"]
    assert "Full current soul and wake notes" in content
    assert "You are pike" in content
    assert "Provider handover: codex -> claude" in content
    assert "Finish the person's request" in content
    assert "Current start charter" in spawned[0][0]
    assert r.state["handover_due"]
