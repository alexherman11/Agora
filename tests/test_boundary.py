"""Axioms 2 and 3, mechanically: clients touch only verbs, project, and scene; secrets stay home."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLIENT_ALLOWED = {"kernel.verbs", "kernel.project", "kernel.scene"}

# Who may import whom inside the kernel: the dependency chain, as a table.
KERNEL_IMPORTS = {
    "schema": set(),
    "events": {"schema", "locking"},
    "store": {"events", "schema", "locking"},
    "facets": {"schema", "lens_schema", "component_schema", "component_metadata"},
    "verbs": {
        "events",
        "facets",
        "schema",
        "store",
        "imports",
        "lenses",
        "locking",
        "vocabulary",
        "component_api",
        "component_data",
    },
    "project": {"facets", "schema", "store", "lenses", "locking"},
    "scene": {"project", "schema", "store", "locking"},
    "text": {"schema", "store", "verbs"},
    "locking": set(),
    "imports": {"facets"},
    "lens_schema": set(),
    "lenses": {"lens_schema", "locking", "schema", "store"},
    "vocabulary": {"schema"},
    "component_api": {
        "component_candidates",
        "component_commands",
        "component_data",
        "component_testing",
        "facets",
        "locking",
        "store",
    },
    "component_candidates": {"component_commands", "component_data", "events", "store"},
    "component_commands": {
        "component_data",
        "component_effects",
        "component_runtime",
        "component_schema",
        "component_tree",
        "schema",
    },
    "component_data": {"component_schema", "schema"},
    "component_effects": {"component_schema", "facets", "schema"},
    "component_runtime": {"component_schema", "component_tree"},
    "component_schema": set(),
    "component_metadata": set(),
    "component_testing": {
        "component_commands",
        "component_data",
        "component_schema",
        "component_tree",
        "events",
        "store",
    },
    "component_tree": set(),
}


def kernel_imports(path: Path) -> set[str]:
    found = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "kernel":
                found.update(f"kernel.{alias.name}" for alias in node.names)
            elif node.module.startswith("kernel."):
                found.add(node.module)
        elif isinstance(node, ast.Import):
            found.update(a.name for a in node.names if a.name.startswith("kernel"))
    return found


def all_imports(path: Path) -> set[str]:
    found = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module.split(".")[0])
        elif isinstance(node, ast.Import):
            found.update(a.name.split(".")[0] for a in node.names)
    return found


def test_clients_import_only_verbs_project_and_scene() -> None:
    for package in ("shell", "jeff"):
        for path in (ROOT / package).glob("*.py"):
            illegal = kernel_imports(path) - CLIENT_ALLOWED
            assert not illegal, f"{path.relative_to(ROOT)} reaches past the choke point: {illegal}"


def test_kernel_follows_the_dependency_chain() -> None:
    assert {p.stem for p in (ROOT / "kernel").glob("*.py")} - {"__init__"} == set(KERNEL_IMPORTS)
    for name, allowed in KERNEL_IMPORTS.items():
        found = {m.removeprefix("kernel.") for m in kernel_imports(ROOT / "kernel" / f"{name}.py")}
        assert found <= allowed, f"kernel/{name}.py imports {found - allowed} against the chain"


def test_only_text_knows_loro_and_only_store_knows_sqlite() -> None:
    for path in list(ROOT.glob("*.py")) + [
        p for d in ("kernel", "shell", "jeff") for p in (ROOT / d).glob("*.py")
    ]:
        mods = all_imports(path)
        if path.name != "text.py":
            assert "loro" not in mods, f"{path.relative_to(ROOT)} knows Loro"
        if path.name != "store.py":
            assert "sqlite3" not in mods, f"{path.relative_to(ROOT)} knows SQLite"


def test_every_kernel_file_opens_with_a_two_line_header() -> None:
    for path in (ROOT / "kernel").glob("*.py"):
        doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8")), clean=False) or ""
        lines = doc.strip().splitlines()
        assert len(lines) >= 2 and lines[1].startswith("Never:"), (
            f"{path.name} lacks its never-clause"
        )


def test_kernel_files_stay_small() -> None:
    for path in (ROOT / "kernel").glob("*.py"):
        count = len(path.read_text(encoding="utf-8").splitlines())
        limit = {"store.py": 300, "verbs.py": 320, "events.py": 260}.get(path.name, 230)
        assert count <= limit, f"{path.name} has {count} lines; split it and update AGENTS.md"
