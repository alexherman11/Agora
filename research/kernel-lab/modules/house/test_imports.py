"""Private in-process kernels and read-only Git. No sessions, subprocess hosts or windows."""
import hashlib
import json
from pathlib import Path
import sys
import threading
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
REPO = LAB.parents[1]
sys.path[:0] = [str(HERE), str(LAB), str(LAB.parent / "window-lab/kernel-desktop")]
from kernel.kernel import Actor, Kernel
import house as H
import imports as I
import gaming_gate

BASE, LAND, MAIN = "1" * 40, "2" * 40, "3" * 40
PATH = "app/code.js"
CONTENT = '// é; "quoted" and $literal\r\nconst path = "a\\\\b";\n'


class Snapshot:
    """Read-only Git command contract; never creates test Git commits."""
    def __init__(self):
        self.touched = True
        self.mode = "100644"
        self.main_blob = self.blob = "4" * 40
        self.main = MAIN
        self.content = CONTENT.encode()
        self.calls = []
        self.ancestor = True

    def __call__(self, repo, *args):
        self.calls.append(args)
        word = args[0]
        if word == "rev-parse":
            return (self.main + "\n").encode()
        if word == "merge-base":
            if not self.ancestor:
                raise ValueError("landing is not on committed main")
            return b""
        if word == "diff":
            return (PATH + "\0").encode() if self.touched else b""
        if word == "ls-tree":
            blob = self.main_blob if args[2] == MAIN else self.blob
            return f"{self.mode} blob {blob}\t{PATH}\0".encode()
        if word == "cat-file":
            return str(len(self.content)).encode() if args[1] == "-s" else self.content
        raise AssertionError(args)


@pytest.fixture
def world(tmp_path, monkeypatch):
    k = Kernel(tmp_path / "world", {
        "tag": "im", "name": "Import fixture",
        "steward": {"account": "owner", "name": "Owner"}, "invites_counted_by": "kernel",
        "invites": [{"code": "fixture", "uses": 2}],
        "modules": [{"name": "house", "run": ["never-started"], "publishes": "house.*",
                     "grants": "house.* rows look"}]})
    owner = k.actor_for(k.accounts["owner"])

    def say(line, actor=owner):
        out = k.run(actor, line)
        assert out["ok"], out
        return out

    component = say('make kind=component name=fixture code="old"')['made'][0]
    lens = say('make kind=lens name=fixture text="old"')['made'][0]
    card = say(f'make kind=taskboard-task title=Fixture landed_commit={LAND}')['made'][0]
    grant = say('grant house words=set only="kind:component;fields:code"')['made'][0]
    say('grant house words=set only="kind:lens;fields:text"')
    mid = k.module_named("house")
    offer = next(e for e in H.OFFER if e["word"] == "house.import")
    assert k.on_offer(mid, [offer])[0].startswith("published")
    h = H.House.__new__(H.House)
    h.ready = threading.Event()
    h.ready.set()
    home = tmp_path / "builders"
    home.mkdir()
    receipt = dict(task=card, phase="landed", review_base=BASE, landed_commit=LAND)
    h.builders = SimpleNamespace(repo=tmp_path / "repo", home=home, states={card: receipt},
                                 landing_lock=threading.Lock(), steward=k.is_steward, landing_blocker=lambda: '')
    git = Snapshot()
    monkeypatch.setattr(I, "git", git)
    gate = Mock()
    monkeypatch.setattr(gaming_gate, "assert_clear", gate)
    context = {}
    h.m = SimpleNamespace(see=lambda line, use=None: k.module_see(mid, context["caller"], line))
    after = []

    def call(mid, word, args, caller):
        context["caller"] = caller
        answer = h.call(dict(word=word, args=args,
                            caller={"person": caller.person, "id": caller.id}, use="fixture"))
        for fn in after:
            fn()
        return answer

    k.modules = SimpleNamespace(running=lambda mid: True, call=call, done=Mock(),
                                deliver=lambda h: None, reconcile=lambda: None)

    def run(target=component, field="code", path=PATH, actor=owner, **extra):
        return k.run(actor, f"house.import {target} field={field} from={card} path={I.quote(path)}"
                     + "".join(f" {key}={value}" for key, value in extra.items()))

    return SimpleNamespace(k=k, owner=owner, say=say, run=run, h=h, component=component,
                           lens=lens, card=card, grant=grant, git=git, gate=gate, after=after)


def test_import_exact_bytes_receipt_and_second_use_is_noop(world):
    w = world
    before = len(w.k.log.records)
    out = w.run()
    assert out["ok"], out
    assert w.k.state.get(w.component, "code") == CONTENT
    assert len(w.k.log.records) == before + 1
    receipt = out["rows"][0]
    assert receipt["status"] == "changed"
    assert receipt["commit"] == LAND and receipt["review_base"] == BASE
    assert receipt["blob"] == w.git.blob and receipt["path"] == PATH
    assert receipt["old_sha256"] == I.digest("old")
    assert receipt["new_sha256"] == I.digest(CONTENT)
    assert receipt["review"] == "required" and receipt["grants"] == "unchanged"
    assert not w.k.state.get(w.component, "reviewed_code")
    before = len(w.k.log.records)
    out = w.run()
    assert out["ok"] and out["rows"][0]["status"] == "unchanged", out
    assert len(w.k.log.records) == before
    assert not list(w.k.things("window"))
    # The operation is the kernel's ordinary undoable set, not an external action.
    w.say("undo")
    assert w.k.state.get(w.component, "code") == "old"


def test_matching_review_is_untouched_and_reported(world):
    w = world
    assert w.run()["ok"]
    w.say("look " + w.component)
    w.say("component " + w.component)
    before = len(w.k.log.records)
    out = w.run()
    assert out["ok"] and out["rows"][0]["review"] == "unchanged"
    assert len(w.k.log.records) == before


def test_lens_uses_same_boundary(world):
    out = world.run(target=world.lens, field="text")
    assert out["ok"] and out["rows"][0]["review"] == "not-applicable"
    assert world.k.state.get(world.lens, "text") == CONTENT


def test_surviving_landing_child_refuses_import_with_reason(world):
    world.h.builders.landing_blocker = lambda: 'landing child PID 43210 may still be running'
    before = len(world.k.log.records)
    out = world.run()
    assert not out['ok'] and '43210' in out['text']
    assert len(world.k.log.records) == before
    assert world.k.state.get(world.component, 'code') == 'old'


@pytest.mark.parametrize("reason", ["untouched", "stale", "symlink", "unlanded", "missing-receipt",
                                   "unrecorded-base", "binary", "not-utf8", "oversize"])
def test_refused_sources_make_no_change(world, reason):
    w = world
    if reason == "untouched":
        w.git.touched = False
    elif reason == "stale":
        w.git.main_blob = "5" * 40
    elif reason == "symlink":
        w.git.mode = "120000"
    elif reason == "unlanded":
        w.git.ancestor = False
    elif reason == "missing-receipt":
        w.h.builders.states = {}
    elif reason == "unrecorded-base":
        w.h.builders.states[w.card].pop("review_base")
    elif reason == "binary":
        w.git.content = b"\0"
    elif reason == "not-utf8":
        w.git.content = b"\xff"
    else:
        w.git.content = b"x" * (I.MAX_BYTES + 1)
    before = len(w.k.log.records)
    out = w.run()
    assert not out["ok"], out
    assert len(w.k.log.records) == before
    assert w.k.state.get(w.component, "code") == "old"
    assert not out.get("rows")   # no successful change receipt on refusal


@pytest.mark.parametrize("path", ["../code.js", "app/../code.js", "/absolute.js", "C:/code.js",
                                  "app\\code.js", "app//code.js", "app/./code.js"])
def test_traversal_refuses_before_git(world, path):
    assert not world.run(path=path)["ok"]
    assert not world.git.calls


@pytest.mark.parametrize("target,field", [("component", "reviewed_code"), ("component", "for"),
                                         ("component", "kind"), ("grant", "words"), ("grant", "text"),
                                         ("lens", "grants"), ("component", "gestures")])
def test_grant_and_security_fields_are_not_import_destinations(world, target, field):
    w = world
    before = len(w.k.log.records)
    out = w.run(target=getattr(w, target), field=field)
    assert not out["ok"] and "no grant/security fields" in out["text"], out
    assert not w.git.calls and len(w.k.log.records) == before


def test_nonsteward_refuses_before_git_or_gate(world):
    w = world
    member = w.k.actor_for(w.k.join("member", "Member", invite="fixture")["person"])
    out = w.run(actor=member)
    assert not out["ok"], out
    assert not w.git.calls
    w.gate.assert_not_called()


def test_callers_own_narrowing_is_not_replaced_by_house_authority(world):
    w = world
    mid = w.say('module restricted run=' + I.quote('["unused"]')
                + ' grants="house.import rows look"')['made'][0]
    actor = Actor(mid, w.owner.person, "module", module=mid, caller=w.owner)
    before = len(w.k.log.records)
    out = w.run(actor=actor)
    assert not out["ok"] and "not a module caller" in out["text"], out
    assert len(w.k.log.records) == before
    assert w.k.state.get(w.component, "code") == "old"
    assert not w.git.calls


def test_direct_steward_agent_can_import(world):
    w = world
    agent = w.k.actor_for(w.owner.person, agent="fixture-steward-agent")
    out = w.run(actor=agent)
    assert out["ok"], out


def test_grant_addition_for_search_preserves_existing_widget_grants_and_owner(world):
    # JEFF's documented repair adds only the missing hearing. It does not re-run
    # `widget`, which would revoke grants and bind for= to the acting steward.
    w = world
    widget = w.say('make kind=widget name=search-fixture code="unused"')['made'][0]
    w.say(f'widget {widget} grants="window.surface window.open hear:set" surface=window')
    before = dict(w.k.state.things[widget])
    existing = list(w.k._grants_to(widget))
    w.say(f'grant {widget} words=hear:view')
    assert dict(w.k.state.things[widget]) == before
    assert all(not w.k.state.get(g, "revoked") for g in existing)
    assert set(existing) < set(w.k._grants_to(widget))
    assert not list(w.k.things("window"))


@pytest.mark.parametrize("when", ["before", "after"])
def test_gaming_gate_refuses_before_mutation(world, when):
    w = world
    w.gate.side_effect = RuntimeError("Gaming gate: fixture") if when == "before" else [
        None, RuntimeError("Gaming gate: fixture")]
    before = len(w.k.log.records)
    out = w.run()
    assert not out["ok"] and "Gaming gate" in out["text"], out
    assert len(w.k.log.records) == before
    if when == "before":
        assert not w.git.calls


def test_main_advancing_before_answer_refuses(world):
    w = world
    def gate():
        if w.git.calls:
            w.git.main = "6" * 40
    w.gate.side_effect = gate
    out = w.run()
    assert not out["ok"] and "main advanced" in out["text"]


@pytest.mark.parametrize("value", ["someone else", CONTENT])
def test_destination_edit_race_is_fenced_and_has_no_success_receipt(world, value):
    w = world
    def edit():
        w.say("look " + w.component)
        w.say(f'set {w.component} code={I.quote(value)}')
    w.after.append(edit)
    out = w.run()
    assert not out["ok"] and "stale" in out["text"], out
    assert w.k.state.get(w.component, "code") == value
    assert not out.get("rows")


def test_landing_card_changed_during_import_refuses_before_edit(world):
    w = world
    def edit():
        w.say("look " + w.card)
        w.say(f'set {w.card} landed_commit={"6" * 40}')
    w.after.append(edit)
    out = w.run()
    assert not out["ok"] and "stale" in out["text"], out
    assert w.k.state.get(w.component, "code") == "old"
    assert not out.get("rows")


@pytest.mark.parametrize("matching", [False, True])
def test_missing_module_field_grant_refuses_even_for_noop(world, matching):
    w = world
    if matching:
        assert w.run()["ok"]
    w.say("undo r" + str(w.k.state.rev[w.grant]))
    before = len(w.k.log.records)
    out = w.run()
    assert not out["ok"], out
    assert len(w.k.log.records) == before
    assert not out.get("rows")


def test_archived_landing_survives_new_worker_on_same_card(world):
    w = world
    old = w.h.builders.states.pop(w.card)
    old["superseded_by"] = "new-worker"
    folder = w.h.builders.home / "old-worker"
    folder.mkdir()
    (folder / "state.json").write_text(json.dumps(old), encoding="utf-8")
    w.h.builders.states[w.card] = dict(task=w.card, phase="released")
    assert w.run()["ok"]


def test_untrusted_revision_argument_cannot_select_a_commit(world):
    assert not world.run(commit=LAND)["ok"]
    assert not world.git.calls


def test_real_git_reads_committed_blob_without_checkout_or_git_writes():
    path = "research/kernel-lab/apps/smart-search/lexical.js"
    # First-parent is used only to select a real existing test fixture, never to
    # authorize a user's import. Production uses the saved House review_base.
    commit = I.git(REPO, "log", "--first-parent", "-1", "--format=%H",
                   "refs/heads/main", "--", path).decode().strip()
    base = I.git(REPO, "rev-parse", commit + "^").decode().strip()
    main, blob, value = I.source(REPO, base, commit, path)
    assert value.encode() == I.git(REPO, "cat-file", "blob", blob)
    assert hashlib.sha256(value.encode()).hexdigest() == I.digest(value)
    assert I.OID.fullmatch(main)
