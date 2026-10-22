"""Worker authority, recoverable commitments, queue fairness and candidate adoption."""

import threading
import time

import pytest

from agora3.gateway import Gateway
from agora3.work import FACET
from agora3.work_scheduler import WorkService
from agora3.world import Refusal


def until(test, timeout=6):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = test()
        if value:
            return value
        time.sleep(0.02)
    raise AssertionError("Expected state did not arrive")


class Worker:
    def __init__(self, candidate, run):
        self.candidate, self.run = candidate, run
        self.updates = []
        self.stopped = threading.Event()

    def send(self, prompt, observe):
        return self.run(self)

    def steer(self, message):
        self.updates.append(message)
        return True

    def stop(self):
        self.stopped.set()

    def close(self):
        pass


@pytest.fixture
def setup(tmp_path):
    gateway = Gateway(tmp_path)
    human = gateway.principal("human")
    gateway.commit(
        human,
        [
            {"id": name, "expected_revision": 0, "facets": {"core.text": {"text": text}}}
            for name, text in (("allowed", "original"), ("secret", "PRIVATE OUTSIDE SCOPE"))
        ],
    )
    services = []

    def make(run, slots=2, notify=None):
        service = WorkService(
            gateway, slots=slots, worker_factory=lambda c: Worker(c, run), notify=notify
        )
        services.append(service)
        return service

    yield gateway, human, make
    for service in services:
        service.close()


def create(g, actor, **extra):
    return g.dispatch(
        actor,
        "work.create",
        {
            "title": "Test",
            "brief": "Complete the explicit test.",
            "scope": {"read_objects": ["allowed"], "write_objects": ["allowed"]},
            "notify": False,
            **extra,
        },
    )["id"]


def status(service, task_id):
    return service.read(task_id)[1]


def change(candidate, text):
    obj = candidate.dispatch("world.get", {"id": "allowed"})
    return candidate.dispatch(
        "world.transact",
        {
            "changes": [
                {
                    "id": "allowed",
                    "expected_revision": obj["revision"],
                    "facets": {"core.text": {"text": text}},
                }
            ]
        },
    )


def test_scope_is_enforced_and_adoption_is_explicit_and_atomic(setup):
    g, actor, make = setup

    def run(worker):
        c = worker.candidate
        assert "secret" not in [o["id"] for o in c.gateway.world.query()["items"]]
        with pytest.raises(Refusal, match="scope"):
            c.dispatch("world.get", {"id": "secret"})
        with pytest.raises(Refusal, match="not granted"):
            c.dispatch("guest.execute", {"command": "anything"})
        with pytest.raises(Refusal, match="scope"):
            c.dispatch(
                "world.transact",
                {
                    "changes": [
                        {
                            "id": "allowed",
                            "expected_revision": 1,
                            "facets": {"core.text": {"text": "bad"}},
                        },
                        {
                            "id": "secret",
                            "expected_revision": 1,
                            "facets": {"core.text": {"text": "bad"}},
                        },
                    ]
                },
            )
        assert c.gateway.world.get("allowed")["revision"] == 1
        change(c, "candidate result")
        return "Candidate edited. Not installed."

    s = make(run)
    task = create(g, actor)
    s.start()
    until(lambda: status(s, task)["state"] == "ready")
    assert g.world.get("allowed")["facets"]["core.text"]["text"] == "original"
    g.dispatch(actor, "work.adopt", {"id": task, "expected_brief_revision": 1})
    assert g.world.get("allowed")["facets"]["core.text"]["text"] == "candidate result"
    assert g.world.get("secret")["revision"] == 1
    assert g.world.verify()["ok"]


def test_resource_queue_does_not_consume_a_slot_and_unrelated_work_can_run(setup):
    g, actor, make = setup
    release = threading.Event()
    started = []

    def run(worker):
        title = worker.candidate.task["title"]
        started.append(title)
        if title == "holder":
            assert release.wait(4)
        return title

    s = make(run)
    first = create(g, actor, title="holder", resources=["test-browser"])
    second = create(g, actor, title="waiter", resources=["test-browser"])
    third = create(g, actor, title="independent")
    s.start()
    until(lambda: status(s, third)["state"] == "ready")
    assert "waiter" not in started
    assert "test-browser" in status(s, second)["detail"]
    assert status(s, first)["state"] == "running"
    release.set()
    until(lambda: status(s, second)["state"] == "ready")


def test_midturn_delivery_and_explicit_peer_collaboration(setup):
    g, actor, make = setup
    release = threading.Event()
    workers = {}

    def run(worker):
        workers[worker.candidate.task["title"]] = worker
        assert release.wait(5)
        return "Done"

    s = make(run)
    left = create(g, actor, title="left")
    right = create(g, actor, title="right")
    s.start()
    until(lambda: len(workers) == 2)
    with pytest.raises(Refusal, match="linked"):
        workers["left"].candidate.dispatch("work.send", {"id": right, "text": "Not yet linked"})
    g.dispatch(actor, "work.link", {"left": left, "right": right})
    workers["left"].candidate.dispatch("work.send", {"id": right, "text": "Found the cause"})
    receipt = g.dispatch(actor, "work.message", {"id": left, "text": "Keep the old colors"})
    assert receipt["delivery"] == "runtime_accepted"
    assert receipt["sender"] == "human"
    assert any("Keep the old colors" in text for text in workers["left"].updates)
    # Peer sends queue for the scheduler so runtime steering happens outside the
    # world authority lock; the other worker's direct receipt is not that delivery.
    until(lambda: any("Found the cause" in text for text in workers["right"].updates))
    release.set()
    until(lambda: status(s, right)["state"] == "ready")


def test_cancellation_fences_candidate_writes_even_if_worker_ignores_stop(setup):
    g, actor, make = setup
    entered, release = threading.Event(), threading.Event()
    refused = []

    def run(worker):
        entered.set()
        assert release.wait(4)
        with pytest.raises(Refusal, match="no longer active"):
            change(worker.candidate, "late write")
        refused.append(True)
        return "Late result"

    s = make(run)
    task = create(g, actor)
    s.start()
    assert entered.wait(4)
    g.dispatch(actor, "work.cancel", {"id": task})
    release.set()
    until(lambda: refused)
    assert status(s, task)["state"] == "cancelled"
    assert g.world.get("allowed")["revision"] == 1


def test_stale_inputs_and_changed_briefs_cannot_adopt(setup):
    g, actor, make = setup
    s = make(lambda w: (change(w.candidate, "draft"), "Done")[1])
    task = create(g, actor)
    s.start()
    until(lambda: status(s, task)["state"] == "ready")
    g.commit(
        actor,
        [
            {
                "id": "allowed",
                "expected_revision": 1,
                "facets": {"core.text": {"text": "human edit"}},
            }
        ],
    )
    with pytest.raises(Refusal, match="Stale dependency"):
        g.dispatch(actor, "work.adopt", {"id": task, "expected_brief_revision": 1})
    s.close()
    g.dispatch(
        actor, "work.revise", {"id": task, "brief": "A changed goal", "expected_brief_revision": 1}
    )
    with pytest.raises(Refusal, match="current brief"):
        g.dispatch(actor, "work.adopt", {"id": task, "expected_brief_revision": 1})
    assert g.world.get("allowed")["facets"]["core.text"]["text"] == "human edit"


def test_restart_marks_uncertain_work_interrupted_instead_of_replaying(setup):
    g, actor, make = setup
    executions = []
    s = make(lambda w: executions.append(True) or "Done")
    task = create(g, actor)
    obj, value = s.read(task)
    value.update(state="running", attempt="lost-process")
    s.save(obj, value)
    s.start()
    until(lambda: status(s, task)["state"] == "interrupted")
    assert not executions
    g.dispatch(actor, "work.retry", {"id": task})
    until(lambda: status(s, task)["state"] == "ready")
    assert len(executions) == 1


def test_model_failure_is_a_failed_task_not_a_successful_result(setup):
    g, actor, make = setup

    def run(worker):
        raise RuntimeError("Transport validation failed")

    s = make(run)
    task = create(g, actor)
    s.start()
    until(lambda: status(s, task)["state"] == "failed")
    assert "Transport validation failed" in status(s, task)["detail"]
    assert status(s, task)["result"] is None
    with pytest.raises(Refusal):
        g.commit(
            actor,
            [
                {
                    "id": task,
                    "expected_revision": g.world.get(task)["revision"],
                    "facets": {FACET: {"state": "ready"}},
                }
            ],
        )


def test_evidence_is_retained_without_premature_executive_wakeup(setup):
    g, actor, make = setup
    release = threading.Event()
    notices = []

    def run(worker):
        worker.candidate.dispatch("work.report", {"kind": "evidence", "text": "Check passed"})
        assert release.wait(4)
        return "Finished"

    s = make(run, notify=lambda text: notices.append(text) or True)
    task = create(g, actor, notify=True)
    s.start()
    until(lambda: status(s, task)["updates"])
    s._notifications()
    assert not notices
    release.set()
    until(lambda: notices)
    assert '"kind":"ready"' in notices[0]


def test_blocker_does_not_poison_explicit_retry_and_cleanup_releases_slot(setup):
    g, actor, make = setup
    runs = []

    def run(worker):
        runs.append(True)
        if len(runs) == 1:
            worker.candidate.dispatch("work.report", {"kind": "blocked", "text": "Need input"})
        return "Done"

    s = make(run, slots=1)
    task = create(g, actor)
    s.start()
    until(lambda: status(s, task)["state"] == "blocked")
    g.dispatch(actor, "work.retry", {"id": task})
    until(lambda: status(s, task)["state"] == "ready")
    until(lambda: not s.runners)
    assert "blocker" not in status(s, task)


def test_cancel_fences_waiting_messages_and_late_reports(setup):
    g, actor, make = setup
    entered, finished = threading.Event(), threading.Event()

    def run(worker):
        entered.set()
        with pytest.raises(Refusal, match="no longer active"):
            worker.candidate.dispatch("work.wait_messages", {"timeout_seconds": 30})
        with pytest.raises(Refusal, match="no longer active"):
            worker.candidate.dispatch("work.report", {"text": "Too late"})
        finished.set()
        return "Late"

    s = make(run)
    task = create(g, actor)
    s.start()
    assert entered.wait(4)
    g.dispatch(actor, "work.cancel", {"id": task})
    assert finished.wait(2)
    assert status(s, task)["progress"] != "Too late"


def test_cleanup_failure_still_releases_exclusive_resources(setup):
    g, actor, make = setup
    s = make(lambda w: "Done", slots=1)
    base = s.factory

    def factory(candidate):
        worker = base(candidate)
        worker.close = lambda: (_ for _ in ()).throw(RuntimeError("Cleanup failed"))
        return worker

    s.factory = factory
    task = create(g, actor, resources=["yard"])
    s.start()
    until(lambda: status(s, task)["state"] == "failed")
    until(lambda: not s.runners)
    assert not s.holders


def test_peer_delivery_never_holds_world_authority_during_runtime_steering(setup):
    g, actor, make = setup
    release = threading.Event()
    workers = {}

    def run(worker):
        workers[worker.candidate.task["id"]] = worker
        assert release.wait(5)
        return "Done"

    s = make(run)
    left = create(g, actor)
    right = create(g, actor, collaborators=[left])
    s.start()
    until(lambda: len(workers) == 2)
    checked = threading.Event()

    def steer(message):
        reader = threading.Thread(target=lambda: (g.principal("human"), checked.set()))
        reader.start()
        assert checked.wait(1), "Peer steering held the world authority lock"
        reader.join()
        return True

    workers[right].steer = steer
    workers[left].candidate.dispatch("work.send", {"id": right, "text": "Case found"})
    assert checked.wait(2)
    release.set()


def test_runtime_budget_exhaustion_cannot_be_a_ready_candidate(setup):
    g, actor, make = setup

    def run(worker):
        worker.last_outcome = "budget"
        return "Tool-call limit reached"

    s = make(run)
    task = create(g, actor)
    s.start()
    until(lambda: status(s, task)["state"] == "failed")
    assert status(s, task)["result"] is None


def test_host_revocation_and_resume_restore_supervisor_without_replaying_attempt(
    tmp_path, monkeypatch
):
    from agora3.server import Application

    monkeypatch.setenv("AGORA_WORKERS", "1")
    app = Application(tmp_path)
    app.connect_guest = lambda: {"test_double": True}
    executions = []

    def run(worker):
        executions.append(True)
        assert worker.stopped.wait(5)
        return "Stopped"

    app.work.factory = lambda c: Worker(c, run)
    actor = app.gateway.principal("human")
    task = create(app.gateway, actor)
    try:
        until(lambda: executions)
        app.dispatch("operator", "host.revoke", {}, actor)
        assert app.work.closed.is_set()
        assert status(app.work, task)["state"] == "interrupted"
        app.dispatch("operator", "host.resume", {}, actor)
        assert not app.work.closed.is_set()
        assert app.work.actor.generation == app.gateway.keep["generation"]
        assert status(app.work, task)["state"] == "interrupted"
        assert len(executions) == 1
    finally:
        app.work.close()


def test_revised_brief_archives_old_messages_and_can_edit_adopted_owned_output(setup):
    g, actor, make = setup
    seen = []

    def run(worker):
        c = worker.candidate
        own = c.dispatch("work.self", {})
        seen.append(own["messages"])
        obj_id = own["output_prefix"] + "note"
        try:
            revision = c.dispatch("world.get", {"id": obj_id})["revision"]
        except Refusal:
            revision = 0
        c.dispatch(
            "world.transact",
            {
                "changes": [
                    {
                        "id": obj_id,
                        "expected_revision": revision,
                        "facets": {"core.text": {"text": own["brief"]}},
                    }
                ]
            },
        )
        return "Done"

    s = make(run)
    task = create(g, actor)
    g.dispatch(actor, "work.message", {"id": task, "text": "Old brief instruction"})
    s.start()
    until(lambda: status(s, task)["state"] == "ready")
    g.dispatch(actor, "work.adopt", {"id": task, "expected_brief_revision": 1})
    g.dispatch(
        actor,
        "work.revise",
        {
            "id": task,
            "expected_brief_revision": 1,
            "brief": "New intent",
        },
    )
    until(lambda: status(s, task)["state"] == "ready")
    g.dispatch(actor, "work.adopt", {"id": task, "expected_brief_revision": 2})
    obj_id = status(s, task)["output_prefix"] + "note"
    assert g.world.get(obj_id)["facets"]["core.text"]["text"] == "New intent"
    assert seen[0][0]["text"] == "Old brief instruction"
    assert seen[1] == []
    assert len(status(s, task)["messages"]) == 1


def test_changed_prerequisite_invalidates_downstream_adoption(setup):
    g, actor, make = setup
    s = make(lambda w: "Done")
    prerequisite = create(g, actor)
    downstream = create(g, actor, depends_on=[prerequisite])
    s.start()
    until(lambda: status(s, downstream)["state"] == "ready")
    s.close()
    g.dispatch(
        actor,
        "work.revise",
        {
            "id": prerequisite,
            "expected_brief_revision": 1,
            "brief": "Changed premise",
        },
    )
    with pytest.raises(Refusal, match="prerequisite"):
        g.dispatch(actor, "work.adopt", {"id": downstream, "expected_brief_revision": 1})
