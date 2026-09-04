"""The CLI: the object layer without JEFF, exercised end to end."""

from __future__ import annotations

import io
import json
from pathlib import Path

import cli


def agora(world: Path, *args: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    code = cli.run(["--world", str(world), "--actor", "alex", *args], out, err)
    return code, out.getvalue(), err.getvalue()


def test_the_cli_round_trip(world_path: Path, notes_file: Path) -> None:
    code, out, _ = agora(world_path, "init")
    assert code == 0 and "ent_desk" in out
    code, out, _ = agora(world_path, "mint", "--facet", "core.name", '{"name": "notes"}')
    entity = out.strip()
    assert code == 0 and entity.startswith("ent_")
    code, out, _ = agora(
        world_path, "attach", entity, "core.text", json.dumps({"path": str(notes_file)})
    )
    assert code == 0 and out.strip().endswith("r1")
    code, out, _ = agora(world_path, "place", entity, "--mode", "summary", "--x", "12")
    assert code == 0 and "as summary" in out
    code, out, _ = agora(world_path, "read", entity, "core.name")
    assert json.loads(out)["facets"]["core.name"]["body"] == {"name": "notes"}
    code, out, _ = agora(world_path, "project", entity, "--budget", "60")
    assert out.startswith("notes; Buy oat milk.")
    code, out, _ = agora(world_path, "desk")
    assert "desk with 1 item: notes" in out
    code, out, _ = agora(world_path, "log")
    lines = out.strip().splitlines()
    assert len(lines) == 4 and all("alex" in line for line in lines)
    code, out, _ = agora(world_path, "rebuild")
    assert code == 0 and out.strip() == "identical"


def test_refusals_exit_2_with_the_reason(world_path: Path) -> None:
    code, _, err = agora(world_path, "attach", "ent_nope", "core.name", '{"name": "x"}')
    assert code == 2 and err.startswith("refused: no entity")
    code, _, err = agora(world_path, "mint", "--facet", "core.name", "not json")
    assert code == 2 and "not JSON" in err


def test_edit_goes_through_the_crdt_as_one_event(world_path: Path) -> None:
    _, out, _ = agora(world_path, "mint", "--facet", "core.text", '{"text": "hello"}')
    entity = out.strip()
    code, out, _ = agora(world_path, "edit", entity, "--insert", "5", " world")
    assert code == 0 and "r2: 'hello world'" in out
    _, out, _ = agora(world_path, "edit", entity, "--anchor", "6", "11")
    locator = out.strip()
    _, out, _ = agora(world_path, "edit", entity, "--insert", "0", "oh ", "--resolve", locator)
    found = json.loads(out.splitlines()[0])
    assert (found["start"], found["end"], found["exact"]) == (9, 14, True)
    _, out, _ = agora(world_path, "log", "--json")
    kinds = [json.loads(line)["kind"] for line in out.strip().splitlines()]
    assert kinds == ["entity-minted", "text-edited", "text-edited"]
    _, out, _ = agora(world_path, "project", entity, "--budget", "12")
    assert out.strip() == "oh hello world"
