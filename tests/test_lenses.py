"""Personal views preserve subjects, activate exact revisions, and remain reversible."""

import copy
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient as RawClient

from jeff.agent import Agent
from kernel import events, project, store, verbs
from shell.server import create_app
from tests.fakes import FakeClient, _last_result, text, tool_use
from tests.http_client import TestClient


def definition():
    return {
        "version": 1,
        "title": "Notes",
        "source": {"scene": "ent_desk", "facet": "core.text"},
        "list": {"component": "list", "field": "core.name.name"},
        "detail": {"component": "text", "field": "core.text.text"},
        "density": "compact",
    }


def notes(world):
    refs = []
    for name, body in (("Garden", "Plant rosemary."), ("Reading", "Return to chapter three.")):
        ref = verbs.mint(world, "alex", {"core.name": {"name": name}, "core.text": {"text": body}})
        verbs.place(world, "alex", ref)
        refs.append(ref)
    return refs


def test_active_current_lens_does_not_rescan_old_events(world):
    notes(world)
    ref = verbs.mint(world, "jeff", {"core.lens": definition()})
    verbs.activate_lens(world, "jeff", ref)
    world.sync()
    with patch.object(events, "_decode", side_effect=AssertionError("rescanned history")):
        assert project.lens(world)["active"]


def test_draft_activation_restore_and_reopen_preserve_subjects(world):
    refs = notes(world)
    before = [verbs.read(world, "alex", ref) for ref in refs]
    entity = verbs.mint(world, "jeff", {"core.lens": definition()})
    initial = verbs.preview_lens(world, "jeff", entity, selected=refs[1])
    assert initial["detail"] == "Return to chapter three."
    assert not project.lens(world)["active"]
    verbs.activate_lens(world, "jeff", entity, revision=initial["revision"], expected_revision=0)
    updated = definition() | {"density": "comfortable"}
    updated["list"]["secondary"] = ["written_by"]
    verbs.attach(world, "jeff", entity, "core.lens", updated, expected_revision=1)
    assert project.lens(world)["definition"]["density"] == "compact"
    draft = verbs.preview_lens(world, "jeff", entity)
    assert draft["rows"][0]["secondary"] == ["alex"]
    verbs.activate_lens(world, "jeff", entity, revision=draft["revision"], expected_revision=1)
    previous = verbs.read(world, "alex", "ent_desk", "core.display", 1)["facets"]["core.display"][
        "body"
    ]
    verbs.activate_lens(world, "alex", previous["lens"], previous["revision"], expected_revision=2)
    again = verbs.open_world(world.world.path)
    try:
        assert project.lens(again)["definition"]["density"] == "compact"
        assert [verbs.read(again, "alex", ref) for ref in refs] == before
        rebuilt = store.rebuild(world.world)
        assert rebuilt.snapshot() == world.snapshot()
        rebuilt.close()
    finally:
        again.close()
    verbs.activate_lens(world, "alex")
    assert not project.lens(world)["active"]


def test_invalid_or_stale_views_leave_the_display_unchanged(world):
    notes(world)
    entity = verbs.mint(world, "jeff", {"core.lens": definition()})
    verbs.activate_lens(world, "jeff", entity)
    before = world.world.log.read_bytes()
    hostile = definition()
    hostile["detail"] = {"component": "script", "field": "core.text.text"}
    with pytest.raises(verbs.VerbError):
        verbs.attach(world, "jeff", entity, "core.lens", hostile)
    with pytest.raises(verbs.VerbError, match="stale"):
        verbs.activate_lens(world, "jeff", entity, expected_revision=0)
    assert world.world.log.read_bytes() == before


def test_selection_cannot_escape_declared_source(world):
    a, b = notes(world)
    body = definition() | {"source": {"entities": [a]}}
    entity = verbs.mint(world, "alex", {"core.lens": body})
    with pytest.raises(verbs.VerbError, match="outside"):
        verbs.preview_lens(world, "alex", entity, selected=b)
    assert [r["entity"] for r in verbs.preview_lens(world, "alex", entity)["rows"]] == [a]


def test_jeff_authors_and_revises_the_same_lens(world):
    notes(world)
    state = {}

    def place(request):
        state["entity"] = _last_result(request)["entity"]
        return [tool_use("place", {"entity": state["entity"]})]

    def preview(_):
        return [tool_use("preview_lens", {"entity": state["entity"]})]

    def activate(request):
        result = _last_result(request)
        return [
            tool_use(
                "activate_lens",
                {
                    "entity": result["entity"],
                    "revision": result["revision"],
                    "expected_revision": result["display_revision"],
                },
            )
        ]

    client = FakeClient(
        [
            [
                tool_use(
                    "mint",
                    {"facets": {"core.name": {"name": "Notes lens"}, "core.lens": definition()}},
                )
            ],
            place,
            preview,
            activate,
            [text("Your notes view is ready.")],
        ]
    )
    agent = Agent(world, client=client)
    result = agent.turn("Make my notes a compact list with a selection preview.")
    assert all("error" not in c for c in result.calls)
    body = copy.deepcopy(definition())
    body["list"]["secondary"] = ["written_by"]
    client.script.extend(
        [
            [
                tool_use(
                    "attach",
                    {
                        "entity": state["entity"],
                        "facet_type": "core.lens",
                        "body": body,
                        "expected_revision": 1,
                    },
                )
            ],
            preview,
            activate,
            [text("Updated.")],
        ]
    )
    result = agent.turn("Show who last edited each note.")
    assert all("error" not in c for c in result.calls)
    assert project.lens(world)["entity"] == state["entity"]
    assert project.lens(world)["revision"] == 2
    assert world.facet(state["entity"], "core.lens").written_by == "jeff"


def test_local_session_authors_and_content_are_protected(world_path):
    app = create_app(world_path, viewer="alex")
    with RawClient(app, base_url="http://localhost") as raw:
        assert raw.get("/tree").status_code == 401
        assert raw.post("/verb", json={"verb": "mint"}).status_code in (401, 403)
    with TestClient(create_app(world_path, viewer="alex")) as client:
        before = client.app.state.world.world.log.read_bytes()
        request = {"verb": "mint", "args": {}}
        assert (
            client.post(
                "/verb", json=request, headers={"Origin": "https://foreign.invalid"}
            ).status_code
            == 403
        )
        assert (
            client.post("/verb", content="{}", headers={"Content-Type": "text/plain"}).status_code
            == 415
        )
        assert client.post("/verb", json=request | {"actor": "jeff"}).status_code == 400
        assert client.post("/verb", json=request | {"args": []}).status_code == 400
        assert client.get("/session", headers={"Host": "evil.invalid"}).status_code == 400
        assert client.app.state.world.world.log.read_bytes() == before
        entity = client.post("/verb", json=request).json()["result"]["entity"]
        assert client.app.state.world.entity(entity).minted_by == "alex"


def test_stop_prevents_dispatch_after_a_provider_returns(world):
    entered, release = Event(), Event()

    def provider(_):
        entered.set()
        assert release.wait(5)
        return [tool_use("mint", {"facets": {"core.name": {"name": "must not be created"}}})]

    agent = Agent(world, client=FakeClient([provider]))
    before = world.world.log.read_bytes()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(agent.turn, "start")
        assert entered.wait(5)
        with pytest.raises(ValueError, match="already working"):
            agent.turn("another simultaneous message")
        agent.cancel()
        release.set()
        result = future.result(timeout=5)
    assert "Stopped" in result.reply
    assert world.world.log.read_bytes() == before


def test_refused_activation_does_not_initialize_the_desk(world):
    before = world.world.log.read_bytes()
    with pytest.raises(verbs.VerbError, match="stale"):
        verbs.activate_lens(world, "alex", expected_revision=99)
    assert world.world.log.read_bytes() == before
