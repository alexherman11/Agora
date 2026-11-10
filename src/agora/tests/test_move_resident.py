"""Private in-process worlds and scripted replies only; retain fixtures under .resident-fixtures."""
import importlib.util
import json
import sys
import threading
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

LAB = Path(__file__).resolve().parents[1]
ROOT = LAB.parents[1]
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(LAB.parent / "desktop" / "kernel-desktop"))
from kernel.kernel import Kernel
from agents.move_resident import digest, install, load_manifest, validate
from kdesk import LocalEntry, moving_in


def load_house():
    spec = importlib.util.spec_from_file_location("resident_house", LAB / "modules/house/house.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def manifest(name="Sable", sable_reply=None):
    data = {"resident": name, "reviewed_by": "Fixture owner"}
    if name == "Pike":
        data["sable_reply"] = sable_reply
    for kind, approval, text in (
        ("soul", "T3", "Alex's exact words.\n\nSable's own lessons — Before the move.\n"),
        ("charter", "T2", "Ask before changing settings. End programs only when necessary or requested.\n"),
    ):
        text = text.replace("Sable", name)
        data[kind] = {"source": "fixture soul" if kind == "soul" else "fixture MOVING-IN T2",
                      "author": f"Alex and {name}" if kind == "soul" else "Alex",
                      "approval": approval, "text": text, "sha256": digest(text)}
    return data


@pytest.fixture
def world():
    directory = ROOT / ".resident-fixtures" / uuid.uuid4().hex
    directory.mkdir(parents=True)
    k = Kernel(directory, {"tag": "rs", "name": "Private move fixture",
                           "steward": {"account": "desktop:alex", "name": "Alex"}})
    entry = LocalEntry(k.keep_dir)
    moving_in(k)
    alex = k.actor_for(k.accounts["desktop:alex"])
    jeff_agent = k.run(alex, "rows house-agent name=JEFF", mode="see")["rows"][0]["id"]
    assert k.run(alex, f"look {jeff_agent}")["ok"]
    assert k.run(alex, f"set {jeff_agent} next_steps=on")["ok"]
    return k, entry, alex


def scripted(world, data=None):
    k, entry, alex = world
    data = data or manifest()
    agent_id = install(k, entry, data)
    person = k.state.get(agent_id, "person")
    actor = k.actor_for(person)
    mod = load_house()
    h = mod.House.__new__(mod.House)
    h.publish = Mock()
    h.m = SimpleNamespace(see=lambda line, **kwargs: k.run(alex, line, mode="see"))
    h.ready = threading.Event()
    h.ready.set()
    h.builders = SimpleNamespace(hear=Mock(), states={})
    h.chat_names = {}
    a = mod.Agent.__new__(mod.Agent)
    a.cfg = dict(k.state.things[agent_id], id=agent_id, want="awake")
    a.house, a.name, a.lock = h, data["resident"], threading.RLock()
    a.state, a.inbox, a.turn, a.busy = {"welcome_due": "fresh"}, [], {}, False
    a.dir = k.log.dir.parent
    a.save, a.log = Mock(), Mock()
    a.child = Mock()
    a.child.alive.return_value = True
    a.child.send.return_value = True
    a.door = SimpleNamespace(post=lambda route, line: k.run(actor, line, mode="see" if route == "/see" else "do"))
    h.agents = {person: a}
    return k, alex, actor, mod, h, a


def make(k, actor, **facts):
    out = k.run(actor, "make " + " ".join(f"{key}={json.dumps(value)}" for key, value in facts.items()))
    assert out["ok"], out["text"]
    return out["made"][0]


def pike_manifest(world):
    k, entry, alex = world
    sable = install(k, entry, manifest())
    person = k.state.get(sable, "person")
    shop = make(k, alex, kind="chat", name="Shop talk")
    reply = k.run(k.actor_for(person), f'say {shop} "Settled, soul edited."')
    assert reply["ok"], reply["text"]
    return manifest("Pike", reply["rows"][0]["id"])


def test_pike_waits_for_sable_reply_before_any_effect(world):
    k, entry, alex = world
    data = manifest("Pike", "missing-reply")
    before = len(k.log.records), dict(entry.sessions)
    with pytest.raises(ValueError, match="Sable's reviewed"):
        install(k, entry, data)
    assert before == (len(k.log.records), entry.sessions)
    data = pike_manifest(world)
    # A visible line by Alex is not evidence that Sable has answered.
    chat = k.state.get(data["sable_reply"], "chat")
    fake = k.run(alex, f'say {chat} "Sable is here"')["rows"][0]["id"]
    real = data["sable_reply"]
    data["sable_reply"] = fake
    before = len(k.log.records), dict(entry.sessions)
    with pytest.raises(ValueError, match="Sable's reviewed"):
        install(k, entry, data)
    assert before == (len(k.log.records), entry.sessions)
    assert "desktop:pike" not in k.accounts
    data["sable_reply"] = real
    sable_person = k.accounts["desktop:sable"]
    sable = next(a for a in k.things("house-agent") if k.state.get(a, "person") == sable_person)
    sable_state = dict(k.state.things[sable])
    agent = install(k, entry, data)
    assert k.state.things[sable] == sable_state
    assert k.state.get(agent, "name") == "Pike"
    assert k.state.get(agent, "move_after_reply") == real
    assert k.state.get(agent, "want") == "asleep"
    assert not k.state.get(agent, "fallback_provider")
    assert not k.things("taskboard-task")
    assert entry.check(entry.token("pike"))["account"] == "desktop:pike"
    before = len(k.log.records), dict(entry.sessions)
    assert install(k, entry, data) == agent
    assert before == (len(k.log.records), entry.sessions)


def test_pike_rejects_private_reply_and_disabled_continuity(world):
    k, entry, alex = world
    data = pike_manifest(world)
    sable_person = k.accounts["desktop:sable"]
    sable_actor = k.actor_for(sable_person)
    private = make(k, sable_actor, kind="chat", name="Sable's private note", sees="me")
    hidden = k.run(sable_actor, f'say {private} "Private reply"')["rows"][0]["id"]
    # A steward sees this line; use an actual visibility fence for the reader.
    original = k.shown
    k.shown = lambda viewer, target: None if target == hidden else original(viewer, target)
    data["sable_reply"] = hidden
    before = len(k.log.records), dict(entry.sessions)
    try:
        with pytest.raises(ValueError, match="Sable's reviewed"):
            install(k, entry, data)
    finally:
        k.shown = original
    assert before == (len(k.log.records), entry.sessions)
    data = pike_manifest(world)
    jeff = k.accounts["desktop:jeff"]
    agent = next(a for a in k.things("house-agent") if k.state.get(a, "person") == jeff)
    assert k.run(alex, f"look {agent}")["ok"]
    assert k.run(alex, f"set {agent} next_steps=off")["ok"]
    before = len(k.log.records), dict(entry.sessions)
    with pytest.raises(ValueError, match="JEFF continuity"):
        install(k, entry, data)
    assert before == (len(k.log.records), entry.sessions)


def test_rules_attribution_repair_preserves_resident_writing(world):
    k, entry, alex = world
    data = manifest()
    agent = install(k, entry, data)
    person = k.state.get(agent, "person")
    charter = k.state.get(agent, "charter")
    soul = k.state.get(agent, "soul")
    # Reproduce the old installer's attribution, retaining new resident writing.
    from kernel.kernel import Tx
    tx = Tx(k)
    tx.part("fixture", None, "fixture")
    tx.set(charter, "made_by", person)
    tx.set(charter, "text", "Resident's current annotations")
    tx.set(soul, "text", "Before the move\nSable's edited soul")
    k._commit(tx, by=alex.person, words="fixture: old mover with later writing")
    install(k, entry, data)
    assert k.state.get(charter, "made_by") == alex.person
    assert k.state.get(charter, "text") == "Resident's current annotations"
    assert k.state.get(soul, "text") == "Before the move\nSable's edited soul"
    assert k.state.get(soul, "made_by") == person
    before = len(k.log.records), dict(entry.sessions)
    install(k, entry, data)
    assert before == (len(k.log.records), entry.sessions)
    data["charter"]["author"] = "Sable"
    with pytest.raises(ValueError, match="credit Alex"):
        install(k, entry, data)
    assert before == (len(k.log.records), entry.sessions)


def test_install_is_asleep_attributed_private_and_idempotent(world):
    k, entry, alex = world
    data = manifest()
    agent = install(k, entry, data)
    person = k.state.get(agent, "person")
    assert not k.is_steward(person)
    assert k.state.get(agent, "want") == "asleep"
    assert k.state.get(agent, "wake_policy") == "addressed"
    assert k.state.get(agent, "next_steps") == "on"
    assert not k.state.get(agent, "fallback_provider")
    assert not k.things("taskboard-task")
    for kind in ("soul", "charter"):
        target = k.state.get(agent, kind)
        assert k.state.get(target, "text") == data[kind]["text"]
        assert k.state.get(target, "made_by") == (person if kind == "soul" else alex.person)
        assert k.state.get(target, "source_author") == data[kind]["author"]
        assert k.shown(k.accounts["desktop:jeff"], target) is not None
    other = k.join("fixture:other", "Other", invite={"channel": "fixture"})["person"]
    assert k.shown(other, k.state.get(agent, "soul")) is None
    assert k.shown(other, k.state.get(agent, "chat")) is None
    assert k.shown(k.accounts["desktop:jeff"], k.state.get(agent, "chat")) is None
    assert entry.check(entry.token("sable"))["account"] == "desktop:sable"
    assert not entry.check(entry.token("sable"))["agent"]
    before = len(k.log.records), dict(entry.sessions)
    assert install(k, entry, data) == agent
    assert before == (len(k.log.records), entry.sessions)
    # Resident writing after installation is preserved by a rerun.
    soul = k.state.get(agent, "soul")
    resident = k.actor_for(person)
    assert k.run(resident, f"look {soul}")["ok"]
    assert k.run(resident, f'set {soul} text="New resident writing"')["ok"]
    install(k, entry, data)
    assert k.state.get(soul, "text") == "New resident writing"
    jeff = k.actor_for(k.accounts["desktop:jeff"])
    assert k.run(jeff, f"look {soul}")["ok"]
    assert k.run(jeff, f'set {soul} lesson="Reviewed together"')["ok"]
    assert not k.run(k.actor_for(other), f"set {soul} text=Intrusion")["ok"]


def test_manifest_conflicts_stop_before_changes(world):
    k, entry, alex = world
    data = manifest()
    data["resident"] = "Other"
    before = len(k.log.records), dict(entry.sessions)
    with pytest.raises(ValueError, match="only Sable and Pike"):
        install(k, entry, data)
    assert before == (len(k.log.records), entry.sessions)
    data = manifest()
    data["soul"]["text"] += "unreviewed change"
    with pytest.raises(ValueError, match="hash"):
        install(k, entry, data)
    assert "desktop:sable" not in k.accounts
    data = manifest()
    agent = install(k, entry, data)
    data["soul"]["text"] = "Different source"
    data["soul"]["sha256"] = digest(data["soul"]["text"])
    before = len(k.log.records), dict(entry.sessions)
    with pytest.raises(ValueError, match="existing import differs"):
        install(k, entry, data)
    assert before == (len(k.log.records), entry.sessions)
    assert k.state.get(k.state.get(agent, "soul"), "text") == manifest()["soul"]["text"]


def test_session_conflict_is_not_replaced(world):
    k, entry, alex = world
    entry.sessions["fixture-token"] = {"signer": "sable", "account": "someone-else", "method": "desktop"}
    before = len(k.log.records), dict(entry.sessions)
    with pytest.raises(ValueError, match="conflicts"):
        install(k, entry, manifest())
    assert before == (len(k.log.records), entry.sessions)
    assert "desktop:sable" not in k.accounts


@pytest.mark.parametrize("name", ["Sable", "Pike"])
def test_addressed_wake_receives_own_tasks_and_answers_private_chat(world, name):
    data = manifest() if name == "Sable" else pike_manifest(world)
    k, alex, actor, mod, h, a = scripted(world, data)
    task = make(k, alex, kind="taskboard-task", title=f"{name}'s fresh task", who=name,
                lane="Now", next_action="Inspect the current window behavior")
    unrelated = make(k, alex, kind="taskboard-task", title="JEFF only", who="JEFF", lane="Now")
    hidden = make(k, alex, kind="taskboard-task", title="Private Alex task", who=name, sees="me")
    h.task_changes()
    h.happen({"word": "make", "target": task, "text": "make who=Sable"})
    assert not a.child.send.called
    assert not a.inbox
    chat = a.cfg["chat"]
    # Real kernel address routing -> House -> resident.
    start = len(k.happenings)
    out = k.run(alex, f'say {chat} "{name}, are you here?"')
    assert out["ok"]
    happening = [x for x in k.happenings[start:] if x["word"] == "say"][-1]
    h.happen(k.happening_for(None, happening))
    delivered = a.child.send.call_args.args[0]
    assert task in delivered and "Inspect the current window behavior" in delivered
    assert unrelated not in delivered and hidden not in delivered
    assert data["soul"]["text"].strip() in delivered
    a._event({"e": "text", "text": "I'm here, Alex."})
    replies = k.run(alex, f"chat {chat}", mode="see")["rows"]
    assert replies[-1]["by"] == name and replies[-1]["text"] == "I'm here, Alex."
    # Public unaddressed chat and self replies do not cause a turn.
    a._event({"e": "result", "ok": True, "detail": ""})
    calls = a.child.send.call_count
    shop = next(t for t in k.things("chat") if k.state.get(t, "name") == "Shop talk")
    start = len(k.happenings)
    assert k.run(alex, f'say {shop} "General notice"')["ok"]
    h.happen(k.happening_for(None, [x for x in k.happenings[start:] if x["word"] == "say"][-1]))
    assert a.child.send.call_count == calls
    # Compaction in an addressed turn gets current task context, after this turn.
    a.wake("Continue", chat=chat)
    a._event({"e": "compacted"})
    assert a.inbox and a.busy
    a._event({"e": "result", "ok": True, "detail": ""})
    assert task in a.child.send.call_args.args[0]
    assert "compacted" in a.child.send.call_args.args[0]
    # Config-only updates must not warm/start this resident.
    a.busy, a.inbox = False, []
    a.child.alive.return_value = False
    a.start = Mock()
    h.load = Mock()
    h.happen({"word": "set", "target": a.cfg["id"]})
    a.start.assert_not_called()


def test_compaction_hook_and_manifest_plan(world, monkeypatch):
    k, alex, actor, mod, h, a = scripted(world)
    import charter_hook
    task = make(k, alex, kind="taskboard-task", title="Task after compact", who="Sable", lane="Now")
    monkeypatch.setattr(charter_hook, "reading", lambda url, token, line: k.run(actor, line, mode="see"))
    assert task in charter_hook.task_context("fixture", "fixture", a.cfg["id"])
    charter = a.cfg["charter"]
    assert charter_hook.read("fixture", "fixture", charter) == manifest()["charter"]["text"].strip()
    data = manifest()
    path = k.log.dir.parent / "manifest.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert load_manifest(path) == data
    data["charter"]["source"] = "unreviewed old charter"
    with pytest.raises(ValueError, match="MOVING-IN T2"):
        validate(data)


def test_default_continuity_still_wakes_but_sleep_gates_addressed_resident(world):
    k, alex, actor, mod, h, a = scripted(world)
    task = make(k, alex, kind="taskboard-task", title="Changed task", who="Sable", lane="Now")
    a.cfg.pop("wake_policy")
    h.task_changes()
    assert task in a.child.send.call_args.args[0]  # JEFF's default policy is retained.
    a._event({"e": "result", "ok": True, "detail": ""})
    a.cfg.update(wake_policy="addressed", want="asleep")
    count = a.child.send.call_count
    a.wake("Addressed while asleep", chat=a.cfg["chat"])
    assert a.child.send.call_count == count and a.inbox
    a.cfg["want"] = "awake"
    a._begin()
    assert "Addressed while asleep" in a.child.send.call_args.args[0]


@pytest.mark.parametrize("name", ["Sable", "Pike"])
def test_kdesk_startup_opt_in_is_idempotent_and_starts_no_model(world, name):
    k, entry, alex = world
    import kdesk
    path = k.log.dir.parent / "manifest.json"
    data = manifest() if name == "Sable" else pike_manifest(world)
    path.write_text(json.dumps(data), encoding="utf-8")
    assert f"desktop:{name.lower()}" not in k.accounts
    # No modules, windows, model transports or real user world.
    for _ in range(2):
        opened, server, host, fresh_entry = kdesk.start(k.log.dir.parent, port=0, modules=False,
                                                     headless=True, resident_manifest=path)
        try:
            assert opened.accounts[f"desktop:{name.lower()}"]
            rows = opened.run(opened.actor_for(alex.person), f"rows house-agent name={name}", mode="see")["rows"]
            assert len(rows) == 1 and rows[0]["want"] == "asleep"
            assert fresh_entry.check(fresh_entry.token(name.lower()))["account"] == f"desktop:{name.lower()}"
        finally:
            server.shutdown()
            server.server_close()
