"""Current-card scenarios; no models, desktop windows or live world."""
import re
from types import SimpleNamespace
import pytest
import work_overview as W


def project(cards, workers=(), people=()):
    calls = []
    def see(line, use):
        calls.append((line, use))
        return {"rows": cards if line == "rows taskboard-task" else list(people)}
    builders = SimpleNamespace(rows=lambda msg: list(workers))
    agents = {"jeff": SimpleNamespace(person="dk2", name="JEFF")}
    result = W.rows(SimpleNamespace(see=see), agents, builders, "reader")
    assert all(use == "reader" for _, use in calls)
    return result


def card(**facts):
    return dict(id="dk10", title="Repair the dock", lane="Now", who="JEFF", **facts)


@pytest.mark.parametrize("field", ["lane", "status"])
@pytest.mark.parametrize("state", sorted(W.HIDDEN))
def test_finished_and_queued_card_overrides_stale_running_builder(field, state):
    task = card(build="building", build_run="old")
    task[field] = state.title()
    assert project([task], [{"task": "dk10", "doing": "working", "name": "Codex", "build_run": "old"}]) == []


def test_one_resident_card_without_builder_and_no_duplicates():
    assert len(project([card()])) == 1
    task = card(build="building", build_run="current")
    rows = project([task], [{"task": "dk10", "doing": "working", "name": "Codex", "build_run": "current"}])
    assert len(rows) == 1 and rows[0]["owner"] == "Codex"


@pytest.mark.parametrize("phase", ["asked", "landed", "released", "idle"])
def test_old_builder_phase_is_not_active(phase):
    assert not project([card(build="building", build_run="old")],
                       [{"task": "dk10", "doing": phase, "name": "Codex", "build_run": "old"}])


@pytest.mark.parametrize("phase,why", [("received", "Finished, waiting on its review since 2026-10-29"),
                                       ("reviewed", "Checks passed, waiting to land since 2026-10-29")])
def test_a_stopped_result_waits_on_its_owner_by_name(phase, why):
    """Alex, 3 Nov: finished results sat for days unattended because the panel hid them. A stopped worker's result
    waits on the one in charge of it, so it shows, after the blocked cards, with how long it has waited."""
    got = project([card(build="landing", build_run="old")],
                  [{"task": "dk10", "doing": phase, "name": "Codex", "build_run": "old",
                    "awaiting": "2026-10-29T05:00:00Z", "owner_name": "Sable"}])
    assert len(got) == 1 and got[0]["state"] == "Waiting"
    assert got[0]["blocker"] == why and got[0]["resolver"] == "Sable"


def test_unclaimed_now_card_is_not_work_in_progress():
    task = card()
    task["who"] = ""
    assert not project([task])


def test_blocked_reason_resolver_names_and_missing_information():
    task = card(blocked_on="Need approval from dk3", blocker_owner="dk3")
    row = project([task], people=[dict(id="dk3", name="Alex")])[0]
    assert row["blocker"] == "Need approval from Alex" and row["resolver"] == "Alex"
    assert row["state"] == "Blocked"
    task = card()
    task["lane"] = "Blocked"
    row = project([task])[0]
    assert row["resolver"] == "Resolver not recorded" and row["blocker"] == "Blocker not recorded"


def test_finishing_disappears_on_the_next_read_without_clearing():
    task = card()
    assert project([task])
    task["lane"] = "Done"
    assert not project([task])


def test_reassigned_worker_cannot_claim_current_card():
    task = card(build="building", build_run="new")
    worker = dict(task="dk10", doing="working", name="Old worker", build_run="old")
    assert not project([task], [worker])
    worker["build_run"] = "new"
    task["builder"] = "New worker"
    assert not project([task], [worker])


def test_current_blocker_survives_an_old_finished_build():
    task = card(build="landed", build_run="current", blocked_on="Needs the owner", blocker_owner="JEFF")
    worker = dict(task="dk10", doing="landed", name="Codex", build_run="current")
    assert project([task], [worker])[0]["state"] == "Blocked"


def test_released_builder_does_not_hide_a_new_resident_claim():
    worker = dict(task="dk10", doing="released", name="Codex", build_run="old")
    assert project([card()], [worker])[0]["owner"] == "JEFF"


@pytest.mark.parametrize("field", ["released", "cancelled", "paused"])
def test_explicit_released_and_held_cards_hide(field):
    assert not project([card(**{field: "yes"})])


def test_reference_blocker_uses_visible_card_title():
    other = dict(id="dk11", title="Owner approval", lane="Later")
    result = project([card(blocked_on="dk11", blocker_owner="dk2"), other],
                     people=[dict(id="dk2", name="JEFF")])
    assert result[0]["blocker"] == "Owner approval" and result[0]["resolver"] == "JEFF"


def test_read_failure_is_not_presented_as_all_clear():
    module = SimpleNamespace(see=lambda *a, **kw: {"refused": "Current work is unavailable"})
    with pytest.raises(RuntimeError, match="Current work is unavailable"):
        W.rows(module, {}, SimpleNamespace(rows=lambda msg: []), "reader")


# Today's world (28 Oct, dk1461): house.who and taskboard rows as the House gave them, trimmed to the facts read here.
# The panel showed nothing; this is the shape it must show.
def worker(task, name, doing, run, now=""):
    return dict(id=task, person=task, name=name, role="builder", task=task, build_run=run, chat="dk1", doing=doing,
                now=now, error=now if doing == "blocked" else "", colour="sage", provider="claude")


TODAY_WORKERS = [
    worker("dk1451", "Claude — Card dk1368 (Bring over the old desk's $ fill-in words…", "working",
           "kernel-dk1451-f48d03edfd", "authenticated Claude turn running"),
    worker("dk1452", "Claude — Card dk1344 (Right-click anything in Agora). Read the…", "working",
           "kernel-dk1452-9383675f0a", "authenticated Claude turn running"),
    worker("dk1453", "Claude — Card dk1136 (Big white blocks appear on the screen). Read…", "landed",
           "kernel-dk1453-25eeabe13d", "source landed; activation and owner outcome verification remain"),
    worker("dk1382", "Codex — Card dk1332 (Rework the work panel: only active or blocked…", "blocked",
           "kernel-dk1382-6a28dddf2c", "House shutting down; preserve work and reconcile before retry"),
    worker("dk1381", "Claude — Read-only research for Alex, card dk1326 (Find Alex's…", "recovery-needed",
           "kernel-dk1381-6033f76410", "House restarted during an operation; inspect retained process"),
    worker("dk1470", "Codex — Card dk1215 (Builders can't make scratch folders in…", "recovery-needed",
           "kernel-dk1470-0a1b2c3d4e", "House restarted during an operation; inspect retained process"),
]
TODAY_CARDS = [
    dict(id="dk1368", title="Bring over the old desk's $ fill-in words, and fix where they snag", lane="Now"),
    dict(id="dk1344", title="Right-click anything in Agora", lane="Now"),
    dict(id="dk1136", title="Big white blocks appear on the screen", lane="Now"),
    dict(id="dk1215", title="Builders can't make scratch folders in Windows Temp", lane="Now"),
    dict(id="dk1332", title="Rework the work panel: only active or blocked work, and nicer", lane="Now"),
    dict(id="dk90", title="The kernel's first shape", lane="Now", who="claude"),
    dict(id="dk1451", title="Card dk1368 (Bring over the old desk's $ fill-in words, and fix where they…", lane="Now",
         who="JEFF", lead="JEFF", builder=TODAY_WORKERS[0]["name"], build="building",
         build_run="kernel-dk1451-f48d03edfd", build_phase="working"),
    dict(id="dk1452", title="Card dk1344 (Right-click anything in Agora). Read the card, then the o", lane="Now",
         who="JEFF", lead="JEFF", builder=TODAY_WORKERS[1]["name"], build="building",
         build_run="kernel-dk1452-9383675f0a", build_phase="working"),
    dict(id="dk1453", title="Card dk1136 (Big white blocks appear on the screen). Read the card. Fi", lane="Now",
         who="JEFF", lead="JEFF", builder=TODAY_WORKERS[2]["name"], build="landed",
         build_run="kernel-dk1453-25eeabe13d", build_phase="landed"),
    dict(id="dk1382", title="Card dk1332 (Rework the work panel: only active or blocked work, and nicer)…", lane="Done",
         who="JEFF", lead="JEFF", builder=TODAY_WORKERS[3]["name"], build="blocked",
         build_run="kernel-dk1382-6a28dddf2c", next_action="Superseded by dk1399. Nothing to do."),
    dict(id="dk1381", title="Read-only research for Alex, card dk1326 (Find Alex's Seabright…", lane="Done",
         who="JEFF", lead="JEFF", builder=TODAY_WORKERS[4]["name"], build="building",
         build_run="kernel-dk1381-6033f76410"),
    dict(id="dk1470", title="Card dk1215 (Builders can't make scratch folders in Windows Temp)", lane="Now",
         who="JEFF", lead="dk827", builder=TODAY_WORKERS[5]["name"], build="building",
         build_run="kernel-dk1470-0a1b2c3d4e"),
    dict(id="dk954", title="Bring Agora docs and Alex's writing from the old world", lane="Now", status="blocked",
         builder="Codex — Bring Agora docs and Alex's writing from the old world", build="landing",
         build_run="kernel-dk954-d521ff68e0", blocker="Worker result received but uncommitted. WinError 5 creating "
         "C:/Users/Alex/AppData/Local/Temp/writing-import/log; cleanup also denied", resolver="Alex"),
    dict(id="dk1144", title="Unpin things from the bottom dock", lane="Now", who="Rowan", lead="dk1190",
         status="Blocked: missing trusted host-action capability", build="landing", build_run="kernel-dk1144-30394317b4",
         blocker="Missing host-action capability: a sandboxed widget can't act as the pressing person", resolver="JEFF"),
    dict(id="dk1017", title="Paste a screenshot into the JEFF chat", lane="Now", who="Rowan", lead="dk1190",
         status="Closed-chat fix reported live, coordinator review requested", build="landing",
         build_run="kernel-dk1017-ecb96f9ad0", resolver="Claude"),
]


def test_todays_world_shows_working_builders_and_blockers_by_name():
    agents = {k: SimpleNamespace(person=p, name=n) for k, p, n in
              [("jeff", "dk827", "JEFF"), ("sable", "dk1148", "Sable"), ("rowan", "dk1190", "Rowan")]}
    module = SimpleNamespace(see=lambda line, use: {"rows": TODAY_CARDS if line == "rows taskboard-task" else
                                                     [dict(id="dk2", name="Alex")]})
    got = W.rows(module, agents, SimpleNamespace(rows=lambda msg: TODAY_WORKERS), "dk2")
    lines = {r["id"]: r for r in got}
    # working builders, under the name of the card they serve, by the kind of worker
    assert lines["dk1451"]["state"] == "Working" and lines["dk1451"]["owner"] == "Claude"
    assert lines["dk1451"]["title"] == "Bring over the old desk's $ fill-in words, and fix where they snag"
    assert lines["dk1452"]["title"] == "Right-click anything in Agora"
    # a stuck builder on an open card: why, and who resolves it (whoever started it)
    stuck = lines["dk1470"]
    assert stuck["state"] == "Blocked" and stuck["resolver"] == "JEFF"
    assert stuck["blocker"] == "House restarted during an operation; inspect retained process"
    # blocked cards with their own blocker and resolver facts, one sentence each
    assert lines["dk954"]["blocker"] == "Worker result received but uncommitted" and lines["dk954"]["resolver"] == "Alex"
    assert lines["dk1144"]["state"] == "Blocked" and lines["dk1144"]["resolver"] == "JEFF"
    # landed, superseded (Done) and unclaimed cards stay hidden; no line carries an id
    assert set(lines) == {"dk1451", "dk1452", "dk1470", "dk954", "dk1144"}
    assert [r["state"] for r in got] == ["Blocked"] * 3 + ["Working"] * 2
    for r in got:
        for field in ("title", "owner", "blocker", "resolver"):
            assert not re.search(r"\bdk\d+\b", r[field]), (field, r[field])
