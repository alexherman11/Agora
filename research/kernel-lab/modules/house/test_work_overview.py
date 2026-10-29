"""Current-card scenarios; no models, desktop windows or live world."""
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


@pytest.mark.parametrize("phase", ["asked", "received", "reviewed", "landed", "released", "idle"])
def test_old_builder_phase_is_not_active(phase):
    assert not project([card(build="building", build_run="old")],
                       [{"task": "dk10", "doing": phase, "name": "Codex", "build_run": "old"}])


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
