"""Private in-process fixtures only; no models, sockets, sessions from live keep, or cleanup."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import uuid

import pytest

LAB = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(LAB), str(LAB.parent / "desktop/kernel-desktop")]
from agents.new_manager import APPROVAL, digest, install, validate
from kernel.kernel import Kernel
from kdesk import LocalEntry


@pytest.fixture
def fixture():
    root = Path(os.environ.get("AGORA_ROWAN_TEST_ROOT", tempfile.gettempdir())) / ("rowan-" + uuid.uuid4().hex)
    k = Kernel(root, {"tag": "rw", "name": "Private Rowan fixture",
                      "steward": {"account": "desktop:alex", "name": "Alex"},
                      "modules": [{"name": "house", "run": ["fixture-not-started"],
                                   "publishes": "house.*", "grants": "look rows", "for": "steward"}]})
    entry = LocalEntry(k.keep_dir)
    alex = k.actor_for(k.accounts["desktop:alex"])
    tasks = []
    for n in range(3):
        r = k.run(alex, f'make kind=taskboard-task title="Task {n}" text="Preserve exact draft {n}" lane=Now')
        assert r["ok"], r
        tasks.append(r["made"][0])
    data = {"resident": "Rowan", "approval": APPROVAL, "tasks": tasks}
    for kind in ("soul", "charter"):
        text = f"Fresh Rowan {kind}. Coordinate only the three approved tasks; preserve others."
        data[kind] = {"source": "fresh:Rowan Oct28", "author": "Codex for Alex",
                      "text": text, "sha256": digest(text)}
    return k, entry, alex, data


def test_install_member_two_sessions_and_three_tasks(fixture):
    k, entry, alex, data = fixture
    before = copy.deepcopy(entry.sessions)
    texts = {t: k.state.get(t, "text") for t in data["tasks"]}
    result = install(k, entry, data)
    person, agent = result["person"], result["agent"]
    assert not k.is_steward(person)
    assert all(entry.sessions[t] == s for t, s in before.items())
    assert len(entry.sessions) == len(before) + 2
    own = [v for v in entry.sessions.values() if v["account"] == "desktop:rowan"]
    assert {v["signer"] for v in own} == {"rowan", "rowan-builder"}
    assert len([v for v in own if v.get("agent")]) == 1
    for key, expected in {"want": "asleep", "provider": "codex", "model": "gpt-6.1-sol",
                          "reasoning": "medium", "wake_policy": "addressed"}.items():
        assert k.state.get(agent, key) == expected
    assert not k.state.get(agent, "fallback_provider")
    assert all(k.state.get(t, "who") == "Rowan" and k.state.get(t, "lead") == person for t in data["tasks"])
    assert texts == {t: k.state.get(t, "text") for t in data["tasks"]}
    assert json.loads((k.keep_dir / "house-managers.json").read_text()) == {
        person: {"tasks": data["tasks"], "enabled": True, "approval": APPROVAL}}
    assert k.run(k.actor_for(person), "who", mode="see")["ok"]
    assert not any(token in json.dumps(result) for token in entry.sessions)


def test_rerun_preserves_sessions_capacity_and_unrelated_authority(fixture):
    k, entry, alex, data = fixture
    setting = k.run(alex, 'make kind=house-settings name=House compact_at=400k builder_capacity=4')["made"][0]
    result = install(k, entry, data)
    assert result["previous_builder_capacity"] == "4"
    assert k.state.get(setting, "compact_at") == "400k"
    assert k.state.get(setting, "builder_capacity") == "3"
    assert k.run(alex, "look " + setting)["ok"]
    assert k.run(alex, "set " + setting + " builder_capacity=2")["ok"]
    before = len(k.log.records), copy.deepcopy(entry.sessions)
    again = install(k, entry, data)
    assert not again["created"]
    assert before == (len(k.log.records), entry.sessions)
    assert k.state.get(setting, "builder_capacity") == "2"


@pytest.mark.parametrize("change", ["duplicate", "foreign", "claim", "missing", "settings", "session"])
def test_preflight_conflicts_write_nothing(fixture, change):
    k, entry, alex, data = fixture
    if change == "duplicate":
        data["tasks"][2] = data["tasks"][0]
    elif change in ("foreign", "claim"):
        assert k.run(alex, "look " + data["tasks"][0])["ok"]
        field = 'who=JEFF' if change == "foreign" else 'build_run=other'
        assert k.run(alex, "set " + data["tasks"][0] + " " + field)["ok"]
    elif change == "missing":
        data["tasks"][0] = "rw999999"
    elif change == "settings":
        for _ in range(2):
            assert k.run(alex, "make kind=house-settings")["ok"]
    else:
        entry.sessions["fixture-conflicting-token"] = {"account": "someone-else", "method": "desktop", "signer": "rowan"}
    before = len(k.log.records), copy.deepcopy(entry.sessions), dict(k.accounts)
    with pytest.raises(ValueError):
        install(k, entry, data)
    assert before == (len(k.log.records), entry.sessions, k.accounts)
    assert not (k.keep_dir / "house-managers.json").exists()


def test_rerun_refuses_revoked_authority_without_restoring_it(fixture):
    k, entry, alex, data = fixture
    result = install(k, entry, data)
    path = k.keep_dir / "house-managers.json"
    authority = json.loads(path.read_text())
    authority[result["person"]]["enabled"] = False
    path.write_text(json.dumps(authority))
    before = len(k.log.records), copy.deepcopy(entry.sessions)
    with pytest.raises(ValueError, match="disabled"):
        install(k, entry, data)
    assert before == (len(k.log.records), entry.sessions)
    assert json.loads(path.read_text()) == authority


def test_manifest_requires_fresh_attribution_and_exact_approval(fixture):
    _, _, _, data = fixture
    for field, value in (("resident", "Sable"), ("approval", "different"), ("tasks", data["tasks"][:2])):
        bad = copy.deepcopy(data)
        bad[field] = value
        with pytest.raises(ValueError):
            validate(bad)
    bad = copy.deepcopy(data)
    bad["soul"]["source"] = "archived migration"
    with pytest.raises(ValueError, match="fresh"):
        validate(bad)


def test_settings_owned_by_alex_agent_are_preserved(fixture):
    k, entry, alex, data = fixture
    actor = k.actor_for(alex.person, "fixture-author")
    setting = k.run(actor, "make kind=house-settings compact_at=450k builder_capacity=4")["made"][0]
    install(k, entry, data)
    assert k.state.get(setting, "compact_at") == "450k"
    assert k.state.get(setting, "builder_capacity") == "3"


def test_existing_unrelated_rowan_is_not_adopted(fixture):
    k, entry, alex, data = fixture
    k.join("desktop:rowan", "Rowan", invite={"channel": "other"})
    before = len(k.log.records), copy.deepcopy(entry.sessions)
    with pytest.raises(ValueError, match="origin"):
        install(k, entry, data)
    assert before == (len(k.log.records), entry.sessions)


def test_held_status_refuses_before_identity_creation(fixture):
    k, entry, alex, data = fixture
    assert k.run(alex, "look " + data["tasks"][0])["ok"]
    assert k.run(alex, "set " + data["tasks"][0] + " status=blocked")["ok"]
    before = len(k.log.records), copy.deepcopy(entry.sessions)
    with pytest.raises(ValueError, match="held"):
        install(k, entry, data)
    assert before == (len(k.log.records), entry.sessions)
    assert "desktop:rowan" not in k.accounts


def test_house_task_grants_are_exact_and_rowan_has_no_raw_set(fixture):
    k, entry, alex, data = fixture
    other = k.run(alex, 'make kind=taskboard-task title="Outside scope"')["made"][0]
    result = install(k, entry, data)
    house = k.module_named("house")
    assert len(result["grants"]) == 3
    for task, grant in zip(data["tasks"], result["grants"]):
        assert k.state.get(grant, "words") == "set"
        assert k.state.get(grant, "only") == "thing:" + task
        assert k.state.get(grant, "to") == house
    task = data["tasks"][0]
    good = k.module_own(house, "set " + task + " build=asked", saw={task: k.state.rev[task]})
    assert good["ok"], good
    bad = k.module_own(house, "set " + other + " build=asked", saw={other: k.state.rev[other]})
    assert not bad["ok"]
    rowan = k.actor_for(result["person"])
    assert k.run(rowan, "look " + task)["ok"]
    assert not k.run(rowan, "set " + task + " title=changed")["ok"]


def test_rerun_does_not_restore_undone_task_grant(fixture):
    k, entry, alex, data = fixture
    result = install(k, entry, data)
    grant = result["grants"][0]
    seq = k.state.last_seq(grant, "kind")
    undone = k.run(alex, "undo r" + str(seq))
    assert undone["ok"], undone
    before = len(k.log.records), copy.deepcopy(entry.sessions)
    with pytest.raises(ValueError, match="removed or revoked"):
        install(k, entry, data)
    assert before == (len(k.log.records), entry.sessions)


def test_grant_refusal_never_enables_manager_authority(fixture, monkeypatch):
    k, entry, alex, data = fixture
    actual = k.run
    def refused(actor, line, **kwargs):
        if line.startswith("grant "):
            return {"ok": False, "text": "fixture grant refused"}
        return actual(actor, line, **kwargs)
    monkeypatch.setattr(k, "run", refused)
    before = len(k.log.records), copy.deepcopy(entry.sessions)
    with pytest.raises(ValueError, match="grant refused"):
        install(k, entry, data)
    assert before == (len(k.log.records), entry.sessions)
    assert "desktop:rowan" not in k.accounts
    assert not (k.keep_dir / "house-managers.json").exists()


def test_launcher_keeps_resident_and_manager_options_separate(fixture, monkeypatch):
    import kdesk_on
    from types import SimpleNamespace
    k, _, _, _ = fixture
    seen = []
    monkeypatch.setattr(kdesk_on, "HERE", k.dir)
    monkeypatch.setattr(kdesk_on, "answering", lambda: None)
    monkeypatch.setattr(kdesk_on.sys, "argv", ["kdesk_on.py", "--resident-manifest", str(k.dir / "resident.json"),
                                             "--manager-manifest", str(k.dir / "manager.json")])
    monkeypatch.setattr(kdesk_on.subprocess, "run", lambda args, **kwargs:
                        (seen.append(args) or SimpleNamespace(stdout="0\n123")))
    kdesk_on.start()
    command = seen[0][-1]
    assert "--resident-manifest" in command and "resident.json" in command
    assert "--manager-manifest" in command and "manager.json" in command
