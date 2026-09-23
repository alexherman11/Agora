"""Native package lifecycle. Fake guest isolates gateway checks from Linux execution."""

import pytest

from agora3.gateway import Gateway
from agora3.guest import GuestError
from agora3.world import Refusal


class FakeGuest:
    output = {"result": {"answer": 42}}
    after_run = None
    failure = False

    def status(self):
        return {"state": "test-double", "not_live_evidence": True}

    def run(self, files, entry, args, context, timeout=30):
        if self.failure:
            raise GuestError("script failed in guest")
        if self.after_run:
            self.after_run()
        return {"compiled": True} if entry.startswith("__agora_check") else self.output


@pytest.fixture
def setup(tmp_path):
    guest = FakeGuest()
    gateway = Gateway(tmp_path, guest, yard=guest)
    actor = gateway.principal("jeff")
    return gateway, actor, guest


FILES = {"action.py": "def main(arguments, context):\n    return {'result': 42}\n"}
MANIFEST = {
    "runtime": "python-1",
    "actions": {"answer": {"entry": "action.py:main", "input_schema": {"type": "object"}}},
}


def build(gateway, actor):
    gateway.packages.save(
        actor, id="alex.test", expected_revision=0, files=FILES, manifest=MANIFEST
    )
    return gateway.packages.build(actor, id="alex.test", expected_revision=1)["build"]


def install(gateway, actor, receipt):
    gateway.packages.install(actor, id="alex.test", build=receipt, expected_revision=0)


def test_actions_exist_without_any_view_and_pin_installation(setup):
    gateway, actor, _ = setup
    receipt = build(gateway, actor)
    assert gateway.packages.tools() == []
    install(gateway, actor, receipt)
    assert gateway.packages.tools()[0]["action"] == "answer"
    assert gateway.packages.invoke(
        actor, package="alex.test", revision=1, action="answer", args={}
    )["result"] == {"answer": 42}
    gateway.packages.install(
        actor, id="alex.test", build=receipt, expected_revision=1, restore=True
    )
    with pytest.raises(Refusal, match="changed"):
        gateway.packages.invoke(actor, package="alex.test", revision=1, action="answer", args={})


def test_stale_source_cannot_promote(setup):
    gateway, actor, _ = setup
    receipt = build(gateway, actor)
    gateway.packages.save(
        actor, id="alex.test", expected_revision=1, files=FILES, manifest=MANIFEST
    )
    with pytest.raises(Refusal, match="Stale dependency"):
        install(gateway, actor, receipt)
    assert gateway.packages.tools() == []


def test_candidate_leaves_live_data_and_log_unchanged(setup):
    gateway, actor, guest = setup
    receipt = build(gateway, actor)
    guest.output = {
        "result": "would write",
        "changes": [
            {"id": "note", "expected_revision": 0, "facets": {"core.text": {"text": "candidate"}}}
        ],
    }
    before = gateway.world.query()
    result = gateway.packages.invoke(
        actor, package="alex.test", revision=0, candidate=receipt, action="answer", args={}
    )
    assert result["native_writes"] == 0
    assert gateway.world.query() == before
    install(gateway, actor, receipt)
    gateway.packages.invoke(actor, package="alex.test", revision=1, action="answer", args={})
    assert gateway.world.get("note")["facets"]["core.text"]["text"] == "candidate"
    assert gateway.world.verify()["ok"]


def test_candidate_rejects_privileged_writes(setup):
    gateway, actor, guest = setup
    receipt = build(gateway, actor)
    guest.output = {
        "changes": [
            {
                "id": "forgery",
                "expected_revision": 0,
                "facets": {"agora.installation": {"build": receipt}},
            }
        ]
    }
    with pytest.raises(Refusal, match="protected"):
        gateway.packages.invoke(
            actor, package="alex.test", revision=0, candidate=receipt, action="answer", args={}
        )


def test_revocation_while_action_runs_blocks_proposed_commit(setup):
    gateway, actor, guest = setup
    receipt = build(gateway, actor)
    install(gateway, actor, receipt)
    guest.output = {
        "changes": [
            {"id": "note", "expected_revision": 0, "facets": {"core.text": {"text": "too late"}}}
        ]
    }
    guest.after_run = gateway.revoke
    before = gateway.world.query()
    with pytest.raises(Refusal, match="stopped"):
        gateway.packages.invoke(actor, package="alex.test", revision=1, action="answer", args={})
    assert gateway.world.query() == before


def test_action_never_overwrites_intervening_human_edit(setup):
    gateway, actor, guest = setup
    receipt = build(gateway, actor)
    install(gateway, actor, receipt)
    guest.output = {
        "changes": [
            {"id": "note", "expected_revision": 0, "facets": {"core.text": {"text": "agent"}}}
        ]
    }
    guest.after_run = lambda: gateway.commit(
        gateway.principal("human"),
        [{"id": "note", "expected_revision": 0, "facets": {"core.text": {"text": "human"}}}],
    )
    with pytest.raises(Refusal, match="stale"):
        gateway.packages.invoke(actor, package="alex.test", revision=1, action="answer", args={})
    assert gateway.world.get("note")["facets"]["core.text"]["text"] == "human"


def test_failed_build_leaves_previous_installation(setup):
    gateway, actor, guest = setup
    receipt = build(gateway, actor)
    install(gateway, actor, receipt)
    before = gateway.world.query()
    guest.failure = True
    with pytest.raises(GuestError):
        gateway.packages.build(actor, id="alex.test", expected_revision=1)
    assert gateway.world.query() == before


@pytest.mark.parametrize(
    "path", ["../escape.py", "/root/file.py", "C:/host.py", "a/../file.py", "a\\b.py"]
)
def test_package_paths_cannot_target_host_or_escape_materialization(setup, path):
    gateway, actor, _ = setup
    with pytest.raises(Refusal):
        gateway.packages.save(
            actor, id="alex.bad", expected_revision=0, files={path: "pass"}, manifest=MANIFEST
        )
    assert gateway.world.query()["watermark"] == 0
