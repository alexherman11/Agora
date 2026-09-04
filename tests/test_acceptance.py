"""The acceptance script from BUILD_PROMPT.md, as one automated run. Every step, in order."""

from __future__ import annotations

import io
from pathlib import Path

from fastapi.testclient import TestClient

import cli
from jeff.agent import Agent
from kernel import store, verbs
from shell.server import create_app
from tests.fakes import FakeClient, import_notes_script


def agora(world: Path, *args: str) -> str:
    out = io.StringIO()
    assert cli.run(["--world", str(world), "--actor", "alex", *args], out, io.StringIO()) == 0
    return out.getvalue()


def test_the_acceptance_script(world_path: Path, notes_file: Path) -> None:
    # 1. Start the shell. An empty desk renders: a scene entity with zero appearances.
    world = verbs.open_world(world_path)
    jeff = Agent(world, client=FakeClient(import_notes_script(str(notes_file))))
    with TestClient(create_app(world_path, jeff=jeff)) as shell:
        tree = shell.get("/tree").json()
        assert tree["exists"] is True and tree["nodes"] == []
        revision_before = tree["revision"]

        # 2. "Put my notes file into the world." JEFF mints name + text + file-backing, places it.
        chat = shell.post("/chat", json={"message": "Put my notes file into the world."}).json()
        assert [c["verb"] for c in chat["calls"]] == ["mint", "place"]
        entity = chat["calls"][0]["result"]["entity"]
        tree = shell.get("/tree").json()
        [node] = tree["nodes"]
        assert node["entity"] == entity and node["label"].startswith("notes")
        assert tree["revision"] > revision_before  # what the change stream pushes to the page
        facets = verbs.read(world, "alex", entity)["facets"]
        assert set(facets) == {"core.name", "core.text", "core.file-backing"}
        assert facets["core.text"]["body"]["text"].startswith("Buy oat milk")

    # 3. `agora log` shows every event of step 2, each carrying actor jeff.
    log = agora(world_path, "log").strip().splitlines()
    step2 = [line for line in log if entity in line]
    assert len(step2) == 2 and all(" jeff " in line for line in step2)

    # 4. Edit the text via the CLI; `agora project <ref> --budget 60` reflects the change.
    agora(world_path, "attach", entity, "core.text", '{"text": "Buy oat milk. Also bread."}')
    projected = agora(world_path, "project", entity, "--budget", "60")
    assert projected.startswith("notes (by jeff); file notes.txt")
    assert projected.rstrip().endswith("Buy oat milk. Also bread.")  # alex's own edit, unattributed

    # 5. Kill every process. Restart. The desk is exactly as it was; rebuild matches the store.
    world.close()
    desk_before = agora(world_path, "tree")
    again = verbs.open_world(world_path)
    with TestClient(create_app(world_path)) as shell:
        assert shell.get("/tree").json()["nodes"][0]["entity"] == entity
    assert agora(world_path, "tree") == desk_before
    assert store.rebuild(again.world).snapshot() == again.snapshot()
    assert agora(world_path, "rebuild").strip() == "identical"
    again.close()

    # 6. Delete the SQLite file entirely. Restart. The world comes back from the log alone.
    (world_path / "store.db").unlink()
    with TestClient(create_app(world_path)) as shell:
        [node] = shell.get("/tree").json()["nodes"]
        assert node["entity"] == entity and node["label"].startswith("notes")
    assert agora(world_path, "tree") == desk_before
