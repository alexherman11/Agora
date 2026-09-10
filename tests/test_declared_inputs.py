"""Dependency validation through the real native package and gateway lifecycle."""

import pytest

from agora3.gateway import Gateway
from agora3.world import Refusal


class Runner:
    output = {"result": True}
    after_run = None
    context = None

    def status(self):
        return {"state": "test-double"}

    def run(self, files, entry, args, context, timeout=30):
        self.context = context
        if entry.startswith("__agora_check"):
            return {"compiled": True}
        if self.after_run:
            self.after_run()
        return self.output


@pytest.fixture
def lab(tmp_path):
    runner = Runner()
    g = Gateway(tmp_path, runner, yard=runner)
    a = g.principal("jeff")
    return g, a, runner


def write(g, a, id, text="original", revision=0):
    return g.commit(
        a, [{"id": id, "expected_revision": revision, "facets": {"core.text": {"text": text}}}]
    )


def install(g, a, reads):
    action = {"entry": "main.py:main", "reads": reads, "input_schema": {"type": "object"}}
    g.packages.save(
        a,
        id="test.inputs",
        expected_revision=0,
        files={"main.py": "def main(a,c): return {}"},
        manifest={"runtime": "python-1", "actions": {"apply": action}},
    )
    receipt = g.packages.build(a, id="test.inputs", expected_revision=1)["build"]
    g.packages.install(a, id="test.inputs", build=receipt, expected_revision=0)
    return receipt


def invoke(g, a, **kwargs):
    return g.packages.invoke(
        a, package="test.inputs", revision=1, action="apply", args=kwargs.pop("args", {}), **kwargs
    )


def proposed(id="result", revision=0):
    return {
        "result": "ok",
        "changes": [
            {"id": id, "expected_revision": revision, "facets": {"core.text": {"text": "applied"}}}
        ],
    }


def test_large_world_only_declared_objects_enter_context(lab):
    g, a, r = lab
    for start in range(0, 1400, 100):
        g.commit(
            a,
            [
                {
                    "id": f"noise-{i:04}",
                    "expected_revision": 0,
                    "facets": {"core.title": {"text": "unrelated"}},
                }
                for i in range(start, start + 100)
            ],
        )
    write(g, a, "document")
    install(g, a, {"ids": ["document"]})
    r.output = proposed()
    r.after_run = lambda: write(g, a, "other")
    invoke(g, a)
    assert [o["id"] for o in r.context["objects"]] == ["document"]
    assert g.world.get("result")["facets"]["core.text"]["text"] == "applied"
    assert g.world.verify()["ok"]


@pytest.mark.parametrize("change", ["edit", "add", "remove"])
def test_query_revision_and_membership_changes_reject_whole_batch(lab, change):
    g, a, r = lab
    write(g, a, "document")
    install(g, a, {"queries": [["core.text"]]})
    r.output = proposed()
    if change == "edit":
        r.after_run = lambda: write(g, a, "document", "human", 1)
    elif change == "add":
        r.after_run = lambda: write(g, a, "newly-matching")
    else:
        r.after_run = lambda: g.commit(
            a, [{"id": "document", "expected_revision": 1, "facets": {"core.text": None}}]
        )
    with pytest.raises(Refusal, match="Declared action inputs changed"):
        invoke(g, a)
    with pytest.raises(Refusal):
        g.world.get("result")


def test_absence_argument_and_target_guards(lab):
    g, a, r = lab
    install(g, a, {"arg_ids": ["document_id"]})
    r.output = proposed()
    r.after_run = lambda: write(g, a, "missing")
    with pytest.raises(Refusal, match="missing"):
        invoke(g, a, args={"document_id": "missing"})
    assert r.context["missing_ids"] == ["missing"]
    r.after_run = None
    r.output = proposed("missing", 0)
    with pytest.raises(Refusal, match="Stale"):
        invoke(g, a, args={"document_id": "unrelated"})
    assert g.world.get("missing")["revision"] == 1


def test_candidate_uses_same_guards_and_never_applies_live_batch(lab):
    g, a, r = lab
    write(g, a, "document")
    receipt = install(g, a, {"ids": ["document"]})
    r.output = proposed()
    before = g.world.query()
    out = invoke(g, a, candidate=receipt)
    assert out["native_writes"] == 0 and g.world.query() == before
    r.after_run = lambda: write(g, a, "document", "human", 1)
    with pytest.raises(Refusal, match="Declared action inputs changed"):
        invoke(g, a, candidate=receipt)
    with pytest.raises(Refusal):
        g.world.get("result")


def test_revocation_still_blocks_declared_commit(lab):
    g, a, r = lab
    install(g, a, {})
    r.output = proposed()
    r.after_run = g.revoke
    with pytest.raises(Refusal, match="stopped"):
        invoke(g, a)
    with pytest.raises(Refusal):
        g.world.get("result")


def test_installation_change_still_blocks_declared_commit(lab):
    g, a, r = lab
    receipt = install(g, a, {})
    r.output = proposed()
    r.after_run = lambda: g.packages.install(
        a, id="test.inputs", build=receipt, expected_revision=1, restore=True
    )
    with pytest.raises(Refusal, match="Stale dependency"):
        invoke(g, a)


def test_declared_query_limit_refuses_before_guest_execution(lab):
    g, a, r = lab
    install(g, a, {"queries": [["core.title"]]})
    for start in range(0, 1100, 100):
        g.commit(
            a,
            [
                {
                    "id": f"noise-{i:04}",
                    "expected_revision": 0,
                    "facets": {"core.title": {"text": "unrelated"}},
                }
                for i in range(start, start + 100)
            ],
        )
    r.context = None
    with pytest.raises(Refusal, match="exceeds 1000"):
        invoke(g, a)
    assert r.context is None
