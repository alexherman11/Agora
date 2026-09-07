"""Executable extensions earn activation; authored behavior stays inside its actual authority."""

import time

import pytest

from jeff.agent import Agent
from kernel import component_runtime, component_tree, events, store, verbs
from tests.component_fixtures import click_cases, counter, drag, drag_cases
from tests.fakes import FakeClient, text, tool_use


def activate(world, body=None):
    verbs.ensure_desk(world)
    ref = verbs.mint(world, "jeff", {"core.component": body or counter()})
    verbs.test_component(world, "jeff", ref, click_cases())
    verbs.activate_component(world, "jeff", ref, 1, 0)
    return ref


def test_two_different_authored_behaviors_and_replay(world):
    refs, body = drag(world)
    originals = [verbs.read(world, "alex", ref) for ref in refs]
    component = verbs.mint(world, "jeff", {"core.component": body})
    before = world.facet("ent_desk", "core.scene")
    result = verbs.test_component(world, "jeff", component, drag_cases(refs[0]))
    assert result["passed"]
    assert world.facet("ent_desk", "core.scene") == before
    verbs.activate_component(world, "jeff", component, 1, 0)
    frame = verbs.component_view(world, "alex")
    for index, case in enumerate(drag_cases(refs[0])):
        log = world.world.log.read_bytes()
        frame = verbs.component_event(
            world, "alex", component, 1, case["event"], frame["fingerprint"], frame["local"]
        )
        if index < 2:
            assert world.world.log.read_bytes() == log
    placed = next(a for a in world.appearances("ent_desk") if a.entity == refs[0])
    assert placed.transform == {"x": 164, "y": 215, "scale": 1}
    assert component_tree.validate(frame["tree"])[refs[0]]["style"]["left"] == "164px"
    assert [verbs.read(world, "alex", ref) for ref in refs] == originals
    last = list(events.replay(world.world))[-1]
    assert last.actor == f"component:{component}@1" and last.payload["requested_by"] == "alex"
    reopened = verbs.open_world(world.world.path)
    rebuilt = store.rebuild(world.world)
    try:
        assert reopened.snapshot() == rebuilt.snapshot() == world.snapshot()
        assert verbs.component_view(reopened, "alex")["revision"] == 1
    finally:
        reopened.close()
        rebuilt.close()


def test_state_and_actions_are_persistent_and_scoped(world):
    ref = activate(world)
    assert verbs.invoke_component(world, "jeff", ref, 1, "increment", {"amount": 3})["value"] == 3
    assert verbs.component_view(world, "alex")["tree"]["text"] == "3"
    current = world.facet(ref, "core.component-state")
    assert current.body["data"] == {"count": 3}
    assert world.historical(ref, "core.component-state", current.revision) == current
    before = world.world.log.read_bytes()
    for facet in ("core.component-state", "core.component-test", "core.component-admission"):
        with pytest.raises(verbs.VerbError, match="runtime-owned"):
            verbs.attach(world, "jeff", ref, facet, {})
    assert world.world.log.read_bytes() == before


def test_failed_or_stale_candidates_cannot_activate(world):
    verbs.ensure_desk(world)
    ref = verbs.mint(world, "jeff", {"core.component": counter()})
    before = world.world.log.read_bytes()
    with pytest.raises(verbs.VerbError, match="expectation failed"):
        verbs.test_component(world, "jeff", ref, click_cases(99))
    assert world.world.log.read_bytes() == before
    with pytest.raises(verbs.VerbError, match="test this exact"):
        verbs.activate_component(world, "jeff", ref, 1, 0)
    verbs.test_component(world, "jeff", ref, click_cases())
    changed = counter() | {"title": "Changed draft"}
    verbs.attach(world, "jeff", ref, "core.component", changed, expected_revision=1)
    with pytest.raises(verbs.VerbError, match="test this exact"):
        verbs.activate_component(world, "jeff", ref, 2, 0)
    verbs.activate_component(world, "jeff", ref, 1, 0)
    assert verbs.component_view(world, "alex")["title"] == "Counter"
    with pytest.raises(verbs.VerbError, match="stale display"):
        verbs.activate_component(world, "jeff", ref, 1, 0)


def test_stale_inputs_and_revoked_display_refuse_events(world):
    ref = activate(world)
    frame = verbs.component_view(world, "alex")
    verbs.invoke_component(world, "alex", ref, 1, "increment", {"amount": 1})
    with pytest.raises(verbs.VerbError, match="inputs changed"):
        verbs.component_event(
            world, "alex", ref, 1, {"node": "counter", "type": "click"}, frame["fingerprint"]
        )
    verbs.activate_lens(world, "alex")
    with pytest.raises(verbs.VerbError, match="no longer active"):
        verbs.invoke_component(world, "alex", ref, 1, "increment", {"amount": 1})
    display = world.facet("ent_desk", "core.display")
    verbs.activate_component(world, "alex", ref, 1, display.revision)
    assert verbs.component_view(world, "alex")["tree"]["text"] == "1"


def test_interactive_preview_cannot_write_live_or_cross_callers(world):
    verbs.ensure_desk(world)
    ref = verbs.mint(world, "jeff", {"core.component": counter()})
    original = world.world.log.read_bytes()
    frame = verbs.open_component_candidate(world, "alex", ref)
    try:
        for _ in range(2):
            frame = verbs.candidate_event(
                world,
                "alex",
                frame["candidate"],
                {"node": "counter", "type": "click"},
                frame["fingerprint"],
                frame["local"],
            )
        assert frame["tree"]["text"] == "2"
        with pytest.raises(verbs.VerbError, match="inaccessible"):
            verbs.candidate_event(
                world,
                "jeff",
                frame["candidate"],
                {"node": "counter", "type": "click"},
                frame["fingerprint"],
            )
        assert world.world.log.read_bytes() == original
    finally:
        verbs.close_component_candidate(world, "alex", frame["candidate"])


def test_component_cannot_smuggle_unauthorized_effects_in_a_valid_batch(world):
    refs, body = drag(world)
    body["source"] = body["source"].replace(
        "return {local:{},effects:[", "return {state:{},local:{},effects:["
    )
    ref = verbs.mint(world, "jeff", {"core.component": body})
    before = world.world.log.read_bytes()
    with pytest.raises(verbs.VerbError, match="persistent-state permission"):
        verbs.test_component(world, "jeff", ref, drag_cases(refs[0]))
    assert world.world.log.read_bytes() == before


@pytest.mark.parametrize(
    "source",
    [
        "({render(){while(true){}}})",
        "({render(){return {id:'x',tag:'script',text:'bad'}}})",
        "({render(){return {id:'x',tag:'div',style:{position:'fixed'}}}})",
        "({render(){return {id:'x',tag:'div',style:{backgroundColor:'url(https://example.invalid)'}}}})",
    ],
)
def test_bad_or_nonterminating_source_is_refused_and_runtime_recovers(source):
    body = counter() | {"source": source}
    ctx = {
        "state": {"count": 0},
        "local": {},
        "objects": {},
        "viewport": {"width": 900, "height": 650},
    }
    started = time.monotonic()
    with pytest.raises(ValueError):
        component_runtime.execute(body, ctx)
    assert time.monotonic() - started < 4
    assert component_runtime.execute(counter(), ctx)["tree"]["text"] == "0"


def test_no_ambient_capabilities_or_cross_request_globals(world):
    body = counter()
    body["source"] = (
        "({render(){globalThis.privateValue=1;return {id:'x',tag:'p',"
        "text:[typeof process,typeof require,typeof fetch,typeof document,typeof std].join(',')}}})"
    )
    ctx = {"state": {}, "local": {}}
    assert component_runtime.execute(body, ctx)["tree"]["text"] == ",".join(["undefined"] * 5)
    body["source"] = "({render(){return {id:'x',tag:'p',text:typeof privateValue}}})"
    assert component_runtime.execute(body, ctx)["tree"]["text"] == "undefined"


def test_new_action_appears_in_same_jeff_session(world):
    verbs.ensure_desk(world)
    ref = verbs.mint(world, "jeff", {"core.component": counter()})
    verbs.test_component(world, "jeff", ref, click_cases())
    client = FakeClient(
        [
            [
                tool_use(
                    "activate_component", {"entity": ref, "revision": 1, "expected_revision": 0}
                )
            ],
            [tool_use("extension_increment", {"amount": 5})],
            [text("Counter is five.")],
        ]
    )
    result = Agent(world, client=client).turn("Use the counter and increment it by five.")
    assert not any("error" in c for c in result.calls)
    assert "extension_increment" not in {t["name"] for t in client.requests[0]["tools"]}
    assert "extension_increment" in {t["name"] for t in client.requests[1]["tools"]}
    assert verbs.component_view(world, "alex")["tree"]["text"] == "5"


def test_changing_bound_inputs_invalidates_test_receipt(world):
    refs, body = drag(world)
    ref = verbs.mint(world, "jeff", {"core.component": body})
    verbs.test_component(world, "jeff", ref, drag_cases(refs[0]))
    verbs.attach(world, "alex", refs[0], "core.text", {"text": "A changed note"})
    with pytest.raises(verbs.VerbError, match="test this exact"):
        verbs.activate_component(world, "jeff", ref, 1, 0)


def test_motion_cannot_persist_and_node_expectations_check_nested_fields(world):
    refs, body = drag(world)
    ref = verbs.mint(world, "jeff", {"core.component": body})
    cases = drag_cases(refs[0])
    cases[1]["expect"]["node"] = {"id": refs[0], "style": {"left": "164px", "top": "215px"}}
    assert verbs.test_component(world, "jeff", ref, cases)["passed"]
    cases[1]["expect"]["node"]["style"]["left"] = "0px"
    before = world.world.log.read_bytes()
    with pytest.raises(verbs.VerbError, match="expectation failed"):
        verbs.test_component(world, "jeff", ref, cases)
    assert world.world.log.read_bytes() == before
    body["source"] = body["source"].replace(
        "return {local:{drag:{...d,x,y}}}", "return {state:{},local:{drag:{...d,x,y}}}"
    )
    body["permissions"]["state"] = True
    verbs.attach(world, "jeff", ref, "core.component", body, expected_revision=1)
    before = world.world.log.read_bytes()
    with pytest.raises(verbs.VerbError, match="pointer motion"):
        verbs.test_component(world, "jeff", ref, drag_cases(refs[0]))
    assert world.world.log.read_bytes() == before


def test_live_render_failure_leaves_state_and_log_unchanged(world):
    body = counter()
    body["source"] = body["source"].replace(
        "render(c) {", "render(c) {if(c.state.count>1) throw Error('cannot render');"
    )
    ref = activate(world, body)
    before = world.world.log.read_bytes()
    with pytest.raises(verbs.VerbError, match="cannot render"):
        verbs.invoke_component(world, "alex", ref, 1, "increment", {"amount": 2})
    assert world.world.log.read_bytes() == before
    assert verbs.component_view(world, "alex")["tree"]["text"] == "0"
