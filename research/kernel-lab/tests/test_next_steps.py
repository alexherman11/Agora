"""Hidden in-process worlds; no model, desktop, credentials, or archived cards."""
import importlib.util
import json
import shutil
import sys
import tempfile
import threading
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB))
from kernel.kernel import Kernel
from kernel.next_steps import basis, packet, rows


@pytest.fixture
def world():
    genesis = {"tag": "ns", "name": "Continuity",
        "steward": {"account": "alex", "name": "Alex"},
        "invites_counted_by": "kernel", "invites": [{"code": "x", "uses": 5}]}
    try:
        fixture = Path(tempfile.mkdtemp(prefix="jeff-continuity-"))
        cleanup_parent = fixture.resolve().parent
        k = Kernel(fixture, genesis)
    except PermissionError:
        # Some managed Windows workers can create a temp directory but cannot
        # use it. Leave that denied path alone; use only the authorized fallback.
        cleanup_parent = Path(__file__).resolve().parents[3] / ".continuity-fixtures"
        cleanup_parent.mkdir(exist_ok=True)
        fixture = cleanup_parent / ("world-" + uuid.uuid4().hex)
        fixture.mkdir()
        k = Kernel(fixture, genesis)
    try:
        a = k.actor_for(k.accounts["alex"])
        j = k.actor_for(k.join("jeff", "JEFF", invite="x")["person"])
        w = k.actor_for(k.join("worker", "Worker", invite="x")["person"])
        yield k, a, j, w
    finally:
        # Delete only this fixture's exact directory within its verified parent.
        resolved = fixture.resolve()
        if resolved.parent != cleanup_parent.resolve():
            raise RuntimeError("continuity fixture escaped its cleanup directory")
        shutil.rmtree(resolved)


def say(k, a, line, ok=True):
    out = k.run(a, line)
    assert out["ok"] == ok, out
    return out


def card(k, a, **fields):
    values = dict(kind="taskboard-task", title="A task never mentioned in chat",
                  lane="Now", who="Worker", lead="JEFF", goal="Keep the promise",
                  acceptance="A visible useful result", next_action="Inspect the task")
    values.update(fields)
    return say(k, a, "make " + " ".join(f"{key}={json.dumps(val)}" for key, val in values.items()))["made"][0]


def projection(k, a):
    return say(k, a, f"rows nextsteps:{a.person}")["rows"]


def test_review_is_distinct_from_worker_claim_and_invalidates(world):
    k, a, j, w = world
    t = card(k, w, build="landing", build_phase="received")
    token = projection(k, j)[0]["basis"]
    assert projection(k, j)[0]["state"] == "result awaiting owner review"
    evidence = say(k, a, 'make kind=note text="Proof"')["made"][0]
    say(k, w, f"look {t}")
    say(k, w, f"task.review {t} basis={token} next_action=Accept", False)
    say(k, w, f"set {t} reviewed_basis={token}")
    assert projection(k, j)[0]["reviewed"] == "no"
    say(k, j, f"task.review {t} basis={token} next_action=Verify")
    assert projection(k, j)[0]["reviewed"] == "yes"
    say(k, j, f"task.verify {t} basis={token} evidence={evidence}")
    assert projection(k, j)[0]["verified"] == "yes"
    say(k, a, f"look {evidence}")
    say(k, a, f'set {evidence} text="Corrected proof"')
    assert projection(k, j)[0]["verified"] == "no"
    # Same token and evidence must be explicitly re-authored together.
    say(k, j, f"task.verify {t} basis={token} evidence={evidence}")
    assert projection(k, j)[0]["verified"] == "yes"
    say(k, a, f"look {t}")
    say(k, a, f'set {t} goal="Corrected request"')
    assert projection(k, j)[0]["reviewed"] == "no"
    say(k, j, f"task.review {t} basis={token} next_action=Accept", False)


def test_child_result_and_undo_and_completion(world):
    k, a, j, w = world
    t = card(k, a)
    child = card(k, a, parent_task=t)
    token = basis(k, j.person, t)
    say(k, a, f"look {child}")
    out = say(k, a, f"set {child} worker_summary=Result")
    assert basis(k, j.person, t) != token
    say(k, a, f"undo {out['records'][0]}")
    assert basis(k, j.person, t) == token
    say(k, a, f"look {t}")
    say(k, a, f"set {t} lane=Done")
    assert next(r for r in projection(k, j) if r["target"] == t)["verified"] == "no"


def test_fields_deadlines_privacy_and_packet_bound(world):
    k, a, j, w = world
    t = card(k, a, who="JEFF")
    say(k, j, f"look {t}")
    say(k, j, f'task.next {t} next_action="Build it" acceptance="Works"')
    say(k, j, f'task.revise {t} goal="New goal" acceptance="New acceptance" request_ref=request next_action="Inspect correction"')
    say(k, j, f"task.followup {t} review_at=2026-01-01", False)
    say(k, j, f"task.followup {t} review_at=2026-01-01T00:00:00Z")
    assert projection(k, j)[0]["state"] == "review due"
    hidden = card(k, a, sees="me", title="Private")
    assert hidden not in [r["target"] for r in projection(k, j)]
    for i in range(15):
        card(k, a, title="Long title " * 100, next_action="x" * 10000, priority=str(i % 4))
    items = projection(k, j)
    text = packet(items, j.person)
    assert len(items) == 16
    assert len(text) < 6000 and text.count("\n- ") <= 8 and "more. Inspect rows" in text
    assert "Private" not in text


def load_house():
    path = LAB / "modules" / "house" / "house.py"
    spec = importlib.util.spec_from_file_location("continuity_house", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def resident(k, j, mod):
    h = mod.House.__new__(mod.House)
    h.publish = Mock()
    h.welcome = Mock(return_value="Soul and welcome")
    a = mod.Agent.__new__(mod.Agent)
    a.house, a.cfg = h, {"person": j.person, "name": "JEFF", "next_steps": "on"}
    a.name, a.lock = "JEFF", threading.RLock()
    a.state, a.inbox, a.turn = {"welcome_due": "fresh"}, [], {}
    a.busy = False
    a.save = Mock()
    a.log = Mock()
    a.child = Mock()
    a.child.alive.return_value = True
    a.child.send.return_value = True
    a.door = SimpleNamespace(post=lambda route, line: k.run(j, line, mode="see"))
    h.agents = {j.person: a}
    return h, a


def test_fresh_wake_compaction_change_and_off(world):
    k, a, j, w = world
    mod = load_house()
    h, agent = resident(k, j, mod)
    t = card(k, a)
    agent.wake("Hello", chat="private-chat")
    delivered = agent.child.send.call_args.args[0]
    assert t in delivered and "Inspect the task" in delivered and "Hello" in delivered
    # A hidden task cannot wake JEFF or affect his projection.
    agent.busy = False
    count = agent.child.send.call_count
    card(k, a, sees="me")
    h.task_changes()
    assert agent.child.send.call_count == count
    # A task created without any chat is picked up via its happening.
    new = card(k, a, next_action="Pick up this new task")
    h.task_changes()
    assert new in agent.child.send.call_args.args[0]
    assert "Pick up this new task" in agent.state["last_sent"]
    count = agent.child.send.call_count
    h.task_changes()
    assert agent.child.send.call_count == count
    agent._event({"e": "compacted"})
    assert agent.inbox  # retained while current turn runs
    agent._event({"e": "result", "ok": True, "detail": ""})
    assert "Next steps" in agent.child.send.call_args.args[0]
    agent.busy = False
    agent.cfg["next_steps"] = "off"
    agent.wake("Next ordinary message")
    assert "Next steps" not in agent.child.send.call_args.args[0]


def test_compaction_hook_uses_live_opt_in(world, monkeypatch):
    k, a, j, w = world
    mod = load_house()
    import charter_hook
    t = card(k, a)
    cfg = {"person": j.person, "next_steps": "on"}
    def reading(url, token, line):
        return {"rows": [cfg]} if line == "look agent" else k.run(j, line, mode="see")
    monkeypatch.setattr(charter_hook, "reading", reading)
    assert t in charter_hook.task_context("unused", "unused", "agent")
    cfg["next_steps"] = "off"
    assert charter_hook.task_context("unused", "unused", "agent") == ""
    hook = mod.T.compact_hook("http://127.0.0.1:1", Path("token"), "charter", "agent")
    assert "--agent agent" in hook["hooks"]["SessionStart"][0]["hooks"][0]["command"]


def test_undo_review_and_evidence_swap_cannot_borrow_claim(world):
    k, a, j, w = world
    t = card(k, w)
    token = projection(k, j)[0]["basis"]
    evidence = say(k, a, 'make kind=note text=Proof')["made"][0]
    other = say(k, a, 'make kind=note text=Other')["made"][0]
    out = say(k, j, f'task-review {t} {token} "Inspect evidence"')
    assert projection(k, j)[0]["reviewed"] == "yes"
    say(k, j, f"undo {out['records'][0]}")
    assert projection(k, j)[0]["reviewed"] == "no"
    say(k, j, f"task-verify {t} {token} {evidence}")
    assert projection(k, j)[0]["verified"] == "yes"
    say(k, w, f"look {t}")
    say(k, w, f"set {t} verified_evidence={other}")
    assert projection(k, j)[0]["verified"] == "no"
    say(k, w, f"look {t}")
    say(k, w, f"set {t} lead=Worker")
    assert projection(k, w)[0]["verified"] == "no"


def test_real_house_happening_discovers_task_and_activity_is_inspectable(world):
    k, a, j, w = world
    mod = load_house()
    h, agent = resident(k, j, mod)
    h.ready = threading.Event()
    h.ready.set()
    h.builders = SimpleNamespace(hear=Mock(), states={})
    h.m = SimpleNamespace(see=lambda line: k.run(a, line, mode="see"))
    agent.dir = k.log.dir.parent
    new = card(k, a, next_action="Take the newly assigned task")
    h.happen({"word": "make", "target": new, "text": "make kind=taskboard-task"})
    assert new in agent.child.send.call_args.args[0]
    # A scripted response exercises the existing public activity path.
    agent._event({"e": "text", "text": "Picked up the newly assigned task."})
    log = h.call({"word": "house.activity", "args": {"target": j.person}})
    assert "Picked up the newly assigned task." in log["text"]
    assert "your task projection changed" in agent.recent_activity()[0]["woken_by"]
    # Successful transport did not author any review/verification.
    agent._event({"e": "result", "ok": True, "detail": ""})
    assert projection(k, j)[0]["reviewed"] == "no"


def test_codex_compaction_injects_same_kernel_context(monkeypatch):
    load_house()
    import charter_hook
    path = LAB.parent / "codex-residents" / "codex_resident.py"
    spec = importlib.util.spec_from_file_location("continuity_codex", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(charter_hook, "context", lambda **kw: "Live charter\nNext steps: inspect new task")
    client = Mock()
    emit = Mock()
    args = SimpleNamespace(kernel_context=json.dumps({"url": "fixture", "token_file": "fixture",
                                                      "charter": "rules", "agent": "JEFF"}))
    mod.refresh_charter(client, "same-thread", args, emit)
    call = client.request.call_args
    assert call.args[0] == "thread/inject_items"
    assert call.args[1]["threadId"] == "same-thread"
    assert "inspect new task" in call.args[1]["items"][0]["content"][0]["text"]
    assert emit.call_args.args[0] == {"type": "kernel_context", "ok": True}


def test_failed_send_preserves_instruction_and_retry_reads_current_tasks(world):
    k, a, j, w = world
    mod = load_house()
    h, agent = resident(k, j, mod)
    t = card(k, a)
    agent.child.send.return_value = False
    agent.wake("The user's complete instruction " * 1000)
    assert len(agent.inbox) == 1 and not agent.busy
    assert "next_steps_context" not in agent.state
    say(k, a, f"look {t}")
    say(k, a, f'set {t} next_action="Use the correction" paused=yes')
    agent.child.send.return_value = True
    agent._begin()
    text = agent.child.send.call_args.args[0]
    assert "Use the correction" in text and "held:" in text
    assert text.count("The user's complete instruction ") == 1000


def test_priority_does_not_follow_error_volume_and_parent_result_does_not_close(world):
    k, a, j, w = world
    parent = card(k, a, priority="urgent")
    card(k, a, parent_task=parent, priority="low", worker_milestone="failed")
    attention = projection(k, j)
    assert attention[0]["target"] == parent
    assert attention[0]["verified"] == "no"
    assert k.state.get(parent, "lane") == "Now"


def test_an_agent_cannot_attest_for_its_person(world):
    """Values review V3 (ran): an agent for Alex attested "verified by Alex" through task.verify and a plain set."""
    k, a, j, w = world
    agent = k.actor_for(a.person, agent="Helper")
    t = say(k, a, f'make kind=taskboard-task title="Ship it" lane=Done acceptance="it runs" lead={a.person} '
                  f'next_action=check')["made"][0]
    evidence = say(k, a, 'make kind=note title="it runs"')["made"][0]
    token = basis(k, a.person, t)
    say(k, agent, f"look {t}")
    out = say(k, agent, f"task.verify {t} basis={token} evidence={evidence}", False)
    assert "can't attest for them" in out["text"]
    say(k, agent, f"set {t} verified_basis={token} verified_evidence={evidence}")     # a raw set is not attestation
    assert rows(k, a, a.person)[0]["verified"] == "no"
    say(k, a, f"look {t}")
    say(k, a, f"task.verify {t} basis={basis(k, a.person, t)} evidence={evidence}")
    assert not [r for r in rows(k, a, a.person) if r["target"] == t]                   # verified done: off the list
