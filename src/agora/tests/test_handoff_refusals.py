"""Hidden worlds and the real rule queue/House inbox, with no worker processes."""
import importlib.util
import json
import os
import shlex
import sys
import threading
import time
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB))
from kernel.kernel import Kernel
from apps.taskboard.handoff_rules import policy_line, rule_lines


def run(k, actor, text):
    result = k.run(actor, text)
    assert result["ok"], result
    return result


def settle(k):
    deadline = time.monotonic() + 5
    stable = None
    while time.monotonic() < deadline:
        with k.lock:
            now = len(k.log.records)
            empty = k._rules_q is None or k._rules_q.empty()
        if empty and now == stable:
            return
        stable = now if empty else None
        time.sleep(.04)
    pytest.fail("rule queue did not settle")


@pytest.fixture
def world():
    root = Path(os.environ["TEMP"]) / "handoff-refusals" / uuid.uuid4().hex
    root.mkdir(parents=True)
    k = Kernel(root, {"tag": "hr", "name": "Hidden handoff checks",
                     "steward": {"account": "jeff", "name": "JEFF"},
                     "invites_counted_by": "kernel", "invites": [{"code": "x", "uses": 5}]})
    owner = k.actor_for(k.accounts["jeff"])
    recipient = k.actor_for(k.join("worker", "Worker", invite="x")["person"])
    other = k.actor_for(k.join("other", "Other", invite="x")["person"])
    book = (LAB / "modules/house/fixtures/agent-book.md").read_text(encoding="utf-8")
    run(k, owner, 'make kind=document title="Agent Book" text=' + shlex.quote(book))
    chat = run(k, owner, 'make kind=chat name="Hidden Shop talk"')["made"][0]
    run(k, owner, 'verb house.hand steps="set $target who=Worker" help="hidden transfer receipt only"')
    run(k, owner, 'verb house.tell steps="make kind=note text=accepted" help="hidden acceptance only"')
    policy = run(k, owner, policy_line(chat))["made"][0]
    rules = [run(k, owner, text)["made"][0] for text in rule_lines(policy, cc=None)]
    yield SimpleNamespace(k=k, owner=owner, recipient=recipient, other=other, chat=chat,
                          policy=policy, rules=rules, root=root)


def enable(w):
    for rule in w.rules:
        run(w.k, w.owner, f"look {rule}")
        run(w.k, w.owner, f"set {rule} off=no")
    settle(w.k)


def hand(w, title="Repair the hidden example"):
    target = run(w.k, w.owner, "make kind=taskboard-task who=JEFF title=" + json.dumps(title))["made"][0]
    run(w.k, w.owner, f"look {target}")
    run(w.k, w.owner, f"house.hand {target} Worker")
    settle(w.k)
    return target


def reply(w, text, actor=None, **facts):
    result = run(w.k, actor or w.recipient, f"say {w.chat} text={shlex.quote(text)} " +
                 " ".join(f"{key}={json.dumps(value)}" for key, value in facts.items()))
    settle(w.k)
    return result["made"][0]


def notices(w):
    return list(w.k.things("notification"))


def house(w):
    spec = importlib.util.spec_from_file_location("handoff_fixture_house", LAB / "modules/house/house.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    h = mod.House.__new__(mod.House)
    h.m = SimpleNamespace(see=lambda line: w.k.run(w.owner, line, mode="see"))
    h.ready = threading.Event()
    h.ready.set()
    h.builders = SimpleNamespace(hear=Mock())
    h.task_changes = Mock()
    h.chat_names = {}
    a = SimpleNamespace(person=w.owner.person, state={}, inbox=[], lock=threading.RLock())
    a.wake = Mock(side_effect=lambda text, record=None, card_notes=None:
                  a.inbox.append(dict(text=text, record=record, card_signal_notes=card_notes or [])))
    h.agents = {w.owner.person: a}
    h.line_for = lambda agent, sid: w.k.shown(agent.person, sid)
    return h, a


def test_disabled_then_enabled_one_refusal_one_wake_and_no_loops(world):
    w = world
    hand(w)
    reply(w, "This session's governing scope excludes that work. I cannot take it.")
    assert not list(w.k.things("handoff")) and notices(w) == []
    enable(w)
    target = hand(w)
    source = reply(w, f"I can’t brief [{target}]({target}) while this session’s governing scope excludes it.")
    assert "@" not in w.k.state.get(source, "text")
    assert len(notices(w)) == 1
    notice = notices(w)[0]
    row = w.k.state.things[notice]
    assert row["to"] == w.owner.person and row["source"] == source and row["about"] == target
    assert w.k.state.get(source, "text") in row["text"] and f"({source})" in row["text"]
    h, a = house(w)
    msg = next(w.k.happening_for(None, msg) for msg in w.k.happenings if notice in msg.get("made", []))
    h.happen(msg)
    h.happen(msg)  # duplicate transport delivery
    h.card_signals(a)  # catch-up overlap
    assert a.wake.call_count == 1
    assert row["text"] in a.inbox[0]["text"]
    run(w.k, w.owner, f"handoff.observe {source} policy={w.policy}")
    run(w.k, w.owner, f"handoff.observe {notice} policy={w.policy}")
    reply(w, "Thanks; I will resolve the scope restriction.", actor=w.owner)
    reply(w, "The garden looks good today.")
    reply(w, w.k.state.get(source, "text"))  # duplicate content in another said record
    settle(w.k)
    assert len(notices(w)) == 1 and a.wake.call_count == 1
    assert all(w.k.state.get(t, "build") is None for t in w.k.things("taskboard-task"))
    # Delivered IDs survive a House restart; its ordinary cursor is not a retry.
    a.state["card_signals_seen"] = [notice]
    a.inbox.clear()
    h.card_signals(a)
    assert a.wake.call_count == 1
    (w.root / "activation-evidence.json").write_text(json.dumps({
        "rules": w.rules, "enabled": all(w.k.state.get(r, "off") == "no" for r in w.rules),
        "handoff": list(w.k.things("handoff"))[-1], "source": source, "notice": notice,
        "addressed_to": row["to"], "wakes": a.wake.call_count, "workers_started": 0,
        "notification_kind": row["kind"], "notification_state": row["state"],
    }, indent=2), encoding="utf-8")
    print("hidden activation evidence:", w.root / "activation-evidence.json")


@pytest.mark.parametrize("text", [
    "You've hit your session limit · resets 6:30pm (America/Los_Angeles)",
    "My provider quota is exhausted; I cannot accept this task.",
    "I am unable to accept the handoff under my current restrictions.",
])
def test_provider_and_cannot_accept(world, text):
    w = world
    enable(w)
    target = hand(w)
    reply(w, text, about=target)
    assert len(notices(w)) == 1


def test_unthreaded_session_failure_covers_pending_handoffs_only(world):
    w = world
    old = reply(w, "You've hit your session limit")
    enable(w)
    one, two = hand(w, "First pending work"), hand(w, "Second pending work")
    run(w.k, w.owner, f"handoff.observe {old} policy={w.policy}")
    assert not notices(w)
    reply(w, "You've hit your session limit")
    assert {w.k.state.get(n, "about") for n in notices(w)} == {one, two}


def test_unrelated_speaker_chat_quotes_and_task_do_not_match(world):
    w = world
    enable(w)
    target = hand(w)
    reply(w, f"I cannot accept {target}", actor=w.other)
    reply(w, "I cannot accept the lunch invitation.")
    reply(w, f'Example text: "I cannot accept {target}"')
    reply(w, "Provider limit is a useful dashboard label.", about=target)
    reply(w, "I can accept this work; no scope restriction prevents it.", about=target)
    reply(w, "My governing scope does not exclude this work.", about=target)
    reply(w, "The provider limit was reached yesterday; today is fine.", about=target)
    other_chat = run(w.k, w.owner, "make kind=chat name=Elsewhere")["made"][0]
    run(w.k, w.recipient, f'say {other_chat} text="I cannot accept" about={target}')
    settle(w.k)
    assert not notices(w)


def test_reply_chain_and_acceptance(world):
    w = world
    enable(w)
    target = hand(w)
    request = reply(w, "Please handle this work.", actor=w.owner, about=target)
    reply(w, "I cannot take this.", reply_to=request)
    assert len(notices(w)) == 1
    target = hand(w, "Already accepted task")
    run(w.k, w.recipient, f"handoff.close {target}")
    reply(w, "I cannot take this.", about=target)
    assert len(notices(w)) == 1


def test_reassignment_and_disabled_notification(world):
    w = world
    enable(w)
    target = hand(w)
    run(w.k, w.owner, f"look {target}")
    run(w.k, w.owner, f"set {target} who=Other")
    reply(w, "I cannot take this.", about=target)
    assert not notices(w)
    target = hand(w, "Another task")
    run(w.k, w.owner, f"look {w.rules[2]}")
    run(w.k, w.owner, f"set {w.rules[2]} off=yes")
    reply(w, "I cannot take this.", about=target)
    assert len(list(w.k.things("handoff-refusal"))) == 1 and not notices(w)


def test_receipts_cannot_be_forged_or_rewritten(world):
    w = world
    enable(w)
    hand(w)
    h = list(w.k.things("handoff"))[0]
    assert not w.k.run(w.recipient, "make kind=handoff-refusal")["ok"]
    run(w.k, w.owner, f"look {h}")
    assert not w.k.run(w.owner, f"set {h} status=pending recipient={w.other.person}")["ok"]


def test_explicit_refusal_requires_recipient_but_no_keywords(world):
    w = world
    enable(w)
    target = hand(w)
    h = list(w.k.things("handoff"))[0]
    source = reply(w, "This assignment falls beyond my remit.", about=target)
    assert not notices(w)
    assert not w.k.run(w.other, f"handoff.refuse {h} source={source} category=scope")["ok"]
    run(w.k, w.recipient, f"handoff.refuse {h} source={source} category=scope")
    settle(w.k)
    assert len(notices(w)) == 1
    assert w.k.shown(w.other.person, notices(w)[0]) is None


def test_undo_source_retracts_undelivered_notice(world):
    w = world
    enable(w)
    target = hand(w)
    source = reply(w, "I cannot accept this.", about=target)
    h, a = house(w)
    h.card_signals(notice=notices(w)[0])
    assert len(a.inbox) == 1
    seq = w.k.state.history[(source, "kind")][0][0]
    run(w.k, w.owner, f"undo r{seq}")
    settle(w.k)
    h.retract_card_signals()
    assert a.inbox == [] and not notices(w)


def test_module_envelope_and_actual_agent_inbox_deliver_once(world):
    w = world
    steward = w.k.actor_for(w.k.join("alex", "Alex", invite="x")["person"])
    rule = w.rules[2]
    run(w.k, w.owner, f"look {rule}")
    action = 'handoff.notify $target cc=Alex text="Handoff blocked: {task}; {recipient}; {reason}; {source}"'
    run(w.k, w.owner, f"set {rule} do={shlex.quote(action)}")
    enable(w)
    target = hand(w)
    helper = w.k.actor_for(w.recipient.person, agent="Recipient session")
    source = reply(w, "My provider quota is exhausted.", actor=helper)
    assert len(notices(w)) == 1
    notice = notices(w)[0]
    assert "text" not in w.k.shown(steward.person, notice)
    assert w.k.shown(w.other.person, notice) is None
    h, _ = house(w)
    h.m = SimpleNamespace(see=lambda line: w.k.run(steward, line, mode="see"))
    # The loaded class's globals retain the real Agent even without registration.
    Agent = h.__class__.happen.__globals__["Agent"]
    a = Agent.__new__(Agent)
    a.house, a.cfg = h, dict(person=w.owner.person, name="JEFF", next_steps="off")
    a.name, a.lock = "JEFF", threading.RLock()
    a.state, a.inbox, a.turn, a.busy = {}, [], {}, True
    a.save, a.log = Mock(), Mock()
    a.child = Mock()
    a.child.alive.return_value = True
    a.child.send.return_value = True
    h.agents = {w.owner.person: a}
    h.publish, h.mark_turn = Mock(), Mock()
    h.system_text = Mock(return_value="unchanged fixture charter")
    h.happen({"word": "make", "target": notice})
    h.happen({"word": "make", "target": notice})
    assert len(a.inbox) == 1
    a.busy = False
    a._begin()
    assert a.child.send.call_count == 1
    delivered = a.child.send.call_args.args[0]
    assert source in delivered and target in delivered and "My provider quota is exhausted." in delivered
    assert a.state["card_signals_seen"] == [notice]
    h.card_signals(a)
    assert a.inbox == [] and a.child.send.call_count == 1


def test_successful_recipient_instruction_closes_pending_handoff(world):
    w = world
    enable(w)
    target = hand(w)
    h = list(w.k.things("handoff"))[0]
    run(w.k, w.other, f"house.tell {target} unrelated")
    settle(w.k)
    assert w.k.state.get(h, "status") == "pending"
    run(w.k, w.recipient, f"house.tell {target} accepted")
    settle(w.k)
    assert w.k.state.get(h, "status") == "accepted"
    reply(w, "I cannot accept this.", about=target)
    assert not notices(w)


def test_notification_is_durable_readable_dismissible_and_reuses_identity(world):
    w = world
    enable(w)
    target = hand(w)
    reply(w, "I cannot accept this.", about=target)
    notice = notices(w)[0]
    row = run(w.k, w.owner, f"look {notice}")["rows"][0]
    assert row["kind"] == "notification" and row["recipient"] == w.owner.person and row["state"] == "unread"
    assert any(r["id"] == notice for r in run(w.k, w.owner, "rows notification")["rows"])
    assert "notification.read" in run(w.k, w.owner, f"actions {notice}")["text"]
    assert not w.k.run(w.recipient, f"notification.read {notice}")["ok"]
    run(w.k, w.owner, f"notification.read {notice}")
    assert w.k.state.get(notice, "state") == "read"
    run(w.k, w.owner, f"notification.dismiss {notice}")
    assert w.k.state.get(notice, "state") == "dismissed"
    run(w.k, w.owner, f"notification.read {notice}")  # cannot silently resurrect dismissal
    assert w.k.state.get(notice, "state") == "dismissed"
    h, a = house(w)
    h.card_signals(a)
    assert a.wake.call_count == 0
    event = list(w.k.things("handoff-refusal"))[0]
    run(w.k, w.owner, f'handoff.notify {event} text="{{reason}}"')
    assert notices(w) == [notice]
    settle(w.k)
    restarted = Kernel(w.root)
    assert restarted.shown(w.owner.person, notice)["state"] == "dismissed"
    assert restarted.shown(w.owner.person, notice)["source"] == row["source"]
    assert restarted.shown(w.other.person, notice) is None


def test_generic_notifications_without_a_handoff_and_dismissed_queue(world):
    w = world
    source = reply(w, "A standalone event.", actor=w.owner)
    command = f'notification.send {source} to=Worker text="A durable event notification" key=standalone cc=JEFF'
    first = run(w.k, w.owner, command)["rows"][0]["id"]
    assert run(w.k, w.owner, command)["rows"][0]["id"] == first
    assert list(w.k.things("handoff")) == []
    assert not w.k.run(w.owner, f"notification.dismiss {first}")["ok"]
    assert not w.k.run(w.owner, f"set {first} state=dismissed")["ok"]
    h, a = house(w)
    a.person = w.recipient.person
    h.agents = {a.person: a}
    h.card_signals(a)
    assert a.wake.call_count == 1 and first in a.inbox[0]["text"]
    run(w.k, w.recipient, f"notification.dismiss {first}")
    h.happen({"word": "set", "target": first})
    assert a.inbox == []
    h.card_signals(a)
    assert a.wake.call_count == 1
    assert run(w.k, w.owner, command)["rows"][0]["id"] == first
    assert w.k.state.get(first, "state") == "dismissed"


def test_notification_does_not_expose_hidden_source(world):
    w = world
    source = run(w.k, w.owner, 'make kind=note text=private sees=me')["made"][0]
    assert not w.k.run(w.owner, f'notification.send {source} to=Worker text="Private event"')["ok"]
    assert not notices(w)
