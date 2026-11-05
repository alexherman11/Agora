"""Live document edits in hidden kernel fixtures; no workers, models or windows."""
import re
import shlex
import threading
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from test_next_steps import LAB, load_house, resident, world  # noqa: F401
from kernel.kernel import Kernel
from kernel.text_templates import render, section


BOOK = (LAB / "modules/house/fixtures/agent-book.md").read_text(encoding="utf-8")
HEADINGS = re.findall(r"^### (.+)$", BOOK, re.M)
ADDITIONS = (LAB.parents[1] / "BOOK-ADDITIONS.md").read_text(encoding="utf-8")
NEW_HEADINGS = re.findall(r"^### (.+)$", ADDITIONS, re.M)


def edit_book(k, actor, text):
    book = k.run(actor, 'look "Agent Book"', mode="see")["rows"][0]["id"]
    out = k.run(actor, f"set {book} text=" + shlex.quote(text))
    assert out["ok"], out


@pytest.mark.parametrize("heading", HEADINGS)
def test_every_book_heading_rereads_and_names_missing_gap(world, heading):
    k, a, j, _ = world
    h, agent = resident(k, j, load_house())
    edit_book(k, a, f"### {heading}\nFirst $.name, $now.\n")
    assert k.run(j, 'look "Agent Book"', mode="see")["rows"][0]["text"] == f"### {heading}\nFirst $.name, $now.\n"
    assert h.message(heading, name="Sable").startswith("First Sable, ")
    edit_book(k, a, f"### {heading}\nEdited $.name.\n")
    assert h.message(heading, name="Sable") == "Edited Sable."
    edit_book(k, a, f"### Renamed {heading}\nDo something else.\n")
    gap = h.message(heading, name="Sable")
    assert "Message unavailable: Agent Book / " + heading in gap
    assert "No instruction supplied." in gap and "Do something else" not in gap


def test_actual_brief_welcome_wake_and_header_change_without_recreation(world):
    k, a, j, _ = world
    mod = load_house()
    h, agent = resident(k, j, mod)
    import builders
    b = builders.Builders.__new__(builders.Builders)
    b.h = h
    state = dict(name="Worker", requester_name="Sable", task="card", title="Repair")
    task = dict(text="the task", acceptance="checked")
    cfg = SimpleNamespace(cfg={}, name="Sable", person=j.person)
    for version in ("Before", "After"):
        edit_book(k, a, f"""### Worker brief
{version} $.name / $.owner / $.title / $.card / $.text / $.acceptance
### Welcome
{version} hello $.name
### Task list header
{version} tasks
### The time
{version} $now
### A line said to them
{version} $.by / $.chat / $.chat_id / $.line / $.text
### A card note addressed to them
{version} $.text / $.card / $.note
""")
        assert b.prompt(state, task) == f"{version} Worker / Sable / Repair / card / the task / checked"
        assert mod.House.welcome(h, cfg) == version + " hello Sable"
        assert h.next_steps(agent).startswith(version + " tasks\n")
        h.chat_names = {"chat": "Shop"}
        assert h.line_text("line", dict(by_name="Alex", text="hello"), "chat") == \
            f"{version} Alex / Shop / chat / line / hello"
        assert h.card_signal_text([dict(text="note", about="card", id="note-id")]) == \
            f"{version} note / card / note-id"
        agent.busy = False
        agent.wake("an event")
        assert version + " tasks" in agent.child.send.call_args.args[0]
        assert re.search(version + r" \d{4}-\d\d-\d\dT", agent.child.send.call_args.args[0])


def test_fill_ins_are_single_pass_prose_and_references_keep_visibility(world):
    k, a, j, _ = world
    public = k.run(a, 'make kind=note name="Settings fixture" model=small')["made"][0]
    private = k.run(a, 'make kind=note name="Private fixture" sees=me secret=hidden')["made"][0]
    see = lambda line: k.run(j, line, mode="see")
    edit_book(k, a, '### Words\n"$.name" $[[Settings fixture]].model $[[' + public + '|label]].model $today')
    result = render(see, "Agent Book", "Words", dict(name="$now"))
    assert result.startswith('"$now" small small ')  # inserted dollars are never evaluated
    k.run(a, "look " + public, mode="see")
    assert k.run(a, f"set {public} model=edited")["ok"]
    assert render(see, "Agent Book", "Words", dict(name="$now")).startswith('"$now" edited edited ')
    edit_book(k, a, '### Words\n$[[' + private + ']].secret')
    result = render(see, "Agent Book", "Words")
    assert "Message unavailable" in result and "hidden" not in result
    edit_book(k, a, '### Words\n$.missing')
    assert "unfilled $.missing" in render(see, "Agent Book", "Words")
    assert Kernel.fill_names('say "$today" $card', {"today": "today", "card": "dk1"}) == 'say "$today" dk1'


def test_heading_boundaries_and_transport_failure():
    assert "Proposed additions" not in section(BOOK, "Worker brief")
    assert section("### One\n```\n### Code\n```\ntext\n### Two\nother", "One") == "```\n### Code\n```\ntext"
    assert section("  ### C# ###\nbody", "C#") == "body"
    assert section("### One\n```text\n## Literal heading\n```\n### Two\nother", "One") == "## Literal heading"
    assert section("### One\n~~~text\n# Literal heading\n~~~", "One") == "# Literal heading"
    assert section("### One\nIntro\n```text\n# Literal heading\n```", "One") == "Intro\n```text\n# Literal heading\n```"
    with pytest.raises(ValueError, match="missing or empty heading"):
        section("### One\n```text\n\n```", "One")
    def broken(_):
        raise RuntimeError("private transport body")
    assert render(broken, "Book", "Heading") == \
        "Message unavailable: Book / Heading (RuntimeError). No instruction supplied."
    assert "unreadable reference Book" in render(lambda _: {"ok": False}, "Book", "Heading")
    assert "missing or empty heading" in render(lambda _: {"rows": [{"text": "### Heading\n"}]}, "Book", "Heading")


def test_old_message_bodies_are_not_runtime_fallbacks():
    house = LAB / "modules/house"
    for filename, fragments in {
        house / "house.py": ["a person in Alex's desktop world", "~ your task projection changed",
                            "~ Your picture of", "~ The picture of", "## Alex's standing rules",
                            "charter: none named", "charter: not read:", "# How work flows here",
                            "# Your soul", "Next steps unavailable;", "[about:", "asked at ",
                            "~ around this:", "~ nearby:", "def context(", "def in_chat("],
        house / "builders.py": ["a coding worker in Alex's Agora desktop", "Follow-up on this same task.",
                               "Your card changed since you started.", "~ Reminder: these workers",
                               "~ Your worker", "~ The worker", "~ Nobody can pick this up:",
                               "asked for it and is not a resident", "in charge of it, can't act now",
                               "stays in charge):", "(the worker ended its turn without words)",
                               "): {state['phase']} since"],
        LAB / "kernel/next_steps.py": ["Receipt is not review;", "Next steps (canonical tasks;"],
        house / "manager.py": ["~ Your builder has a receipt for"],
    }.items():
        source = filename.read_text(encoding="utf-8")
        for fragment in fragments:
            assert fragment not in source, (filename.name, fragment)


def test_follow_up_and_outcome_render_at_use(world):
    k, a, j, _ = world
    h, agent = resident(k, j, load_house())
    import builders
    b = builders.Builders.__new__(builders.Builders)
    b.h, b.lock, b.stopping = h, threading.RLock(), False
    b.notification_lock = threading.RLock()
    b.save = b.assert_owned = b.event = b.stopped = Mock()
    b.run_worker, b.wake_owner = Mock(), Mock()
    state = dict(task="card", name="Worker", requester_name="Sable", session="thread", phase="blocked")
    for version in ("Before", "After"):
        edit_book(k, a, f"### Follow-up\n{version} $.owner_words\n### It stopped\n{version} $.name: $.detail")
        state["pending"] = ["a correction"]
        b.resume(state)
        assert b.run_worker.call_args.args[1] == version + " a correction"
        state.update(detail=version, last_outcome=None)
        b.outcome(state)
        assert b.wake_owner.call_args.args[1] == f"{version} Worker: {version}"


def test_reminder_and_queued_worker_note_use_current_sections(world):
    k, a, j, _ = world
    h, agent = resident(k, j, load_house())
    import builders
    b = builders.Builders.__new__(builders.Builders)
    b.h, b.lock, b.children = h, threading.RLock(), {}
    b.save = b.assert_owned = b.event = Mock()
    b.run_worker = Mock()
    state = dict(task="card", name="Worker", requester=j.person, session="thread", phase="blocked",
                 resume_note={"heading": "When its card changed", "facts": {"text": "revised task"}})
    b.states = {"card": state}
    for version in ("Before", "After"):
        edit_book(k, a, f"### One reminder\n{version} $.list\n### Follow-up\n{version} $.owner_words\n"
                       f"### When its card changed\n{version} $.text\n"
                       "### Waiting worker row\n- $.name ($.card): $.phase")
        agent.wake = Mock()
        state.update(awaiting="then", reminded=None)
        b.remind(j.person)
        assert agent.wake.call_args.args[0].startswith(version + " - Worker (card): blocked")
    state["pending"] = ["owner correction"]
    b.resume(state)
    assert b.run_worker.call_args.args[1] == "After After revised task\nowner correction"


def test_compaction_reads_current_book_and_charter(world, tmp_path, monkeypatch):
    k, a, j, _ = world
    load_house()
    import charter_hook
    charter = k.run(a, 'make kind=note text="Live rules"')["made"][0]
    token_file = tmp_path / "fixture-token"
    token_file.write_text("fixture", encoding="utf-8")
    monkeypatch.setattr(charter_hook, "reading", lambda url, token, line: k.run(j, line, mode="see"))
    for version in ("Before", "After"):
        edit_book(k, a, f"### After a compaction\n{version} rules $.charter")
        assert charter_hook.context("unused", token_file, charter) == f"{version} rules {charter}\n\nLive rules"


def test_book_additions_match_fixture_and_preserve_literal_headers():
    assert len(NEW_HEADINGS) == len(set(NEW_HEADINGS)) == 17
    for heading in NEW_HEADINGS:
        assert section(BOOK, heading) == section(ADDITIONS, heading)
    assert section(ADDITIONS, "Standing rules header") == "## Alex's standing rules (look $.charter is the live one)"
    assert section(ADDITIONS, "Work guide header") == "# How work flows here ($.guide)"
    assert section(ADDITIONS, "Soul header") == "# Your soul ($.soul, yours to keep)"


def test_remaining_house_fragments_read_edits_at_each_use(world):
    k, a, j, _ = world
    mod = load_house()
    h, agent = resident(k, j, mod)
    charter = k.run(a, 'make kind=note text="Rules"')["made"][0]
    empty = k.run(a, 'make kind=note name="Empty charter"')["made"][0]
    guide = k.run(a, 'make kind=note text="Workflow"')["made"][0]
    soul = k.run(a, 'make kind=note text="Identity"')["made"][0]
    made = k.run(a, f"make kind=note where={k.place} about={charter}")
    assert made["ok"], made
    about = made["made"][0]
    cfg = SimpleNamespace(cfg=dict(guide=guide, soul=soul), name="Sable", person=j.person)
    h.chat_names = {"chat": "Shop"}
    agent.door = SimpleNamespace(post=lambda *args: {"ok": False})
    for version in ("Before", "After"):
        text = "\n".join(f"### {heading}\n{version} {section(ADDITIONS, heading)}"
                         for heading in NEW_HEADINGS)
        edit_book(k, a, text + "\n### Welcome\nHello\n### A line said to them\n$.text")
        assert h.charter_text(charter) == f"{version} ## Alex's standing rules (look {charter} is the live one)\n\nRules"
        assert h.charter_text(None) == f"{version} charter: none named on your house-agent thing; tell Alex."
        assert h.charter_text(empty) == f"{version} charter: not read: {empty} is empty or gone; tell Alex."
        assert mod.House.welcome(h, cfg) == (f"Hello\n\n{version} # How work flows here ({guide})\n\nWorkflow"
                                            f"\n\n{version} # Your soul ({soul}, yours to keep)\n\nIdentity")
        assert h.next_steps(agent) == f"{version} Next steps unavailable; read rows nextsteps:{j.person} before continuing task work."
        assert h.line_text("line", dict(text="Words", about=about), "chat") == (
            f"Words {version} [about: {version} note {about}, {version} asked at {k.place}, {version} on {charter}]")
    edit_book(k, a, "### Renamed\nOther")
    assert "Agent Book / Standing rules header (missing or empty heading)" in h.charter_text(charter)
    assert "Agent Book / Task list unavailable (missing or empty heading)" in h.next_steps(agent)


def test_remaining_builder_fragments_read_edits_at_each_use(world):
    k, a, j, _ = world
    h, agent = resident(k, j, load_house())
    import builders
    b = builders.Builders.__new__(builders.Builders)
    b.h = h
    jeff = SimpleNamespace(name="JEFF")
    b.general_manager = lambda: jeff
    state = dict(name="Worker", task="card", phase="blocked", awaiting="2026-11-04T09:00:00",
                 detail="Needs attention", requester_name="Alex")
    for version in ("Before", "After"):
        text = "\n".join(f"### {heading}\n{version} {section(ADDITIONS, heading)}"
                         for heading in NEW_HEADINGS)
        edit_book(k, a, text + "\n### Nobody can pick this up (JEFF)\n$.why")
        assert b.waiting_line(state) == f"{version} - Worker (card): blocked since 2026-11-04 09:00. Needs attention"
        b.owner = lambda _: None
        assert b.route(state) == [(jeff, f"{version} Alex asked for it and is not a resident the House can wake\n")]
        down = SimpleNamespace(name="Sable", state=dict(error="Unavailable"), cfg={})
        b.owner = lambda _: down
        assert b.route(state)[-1] == (jeff, f"{version} Sable, in charge of it, can't act now (Unavailable)\n")
