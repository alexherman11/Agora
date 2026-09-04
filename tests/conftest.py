"""Shared fixtures: a throwaway world per test, never `worlds/`."""

from __future__ import annotations

from pathlib import Path

import pytest

from kernel import verbs
from kernel.store import Store


@pytest.fixture
def world_path(tmp_path: Path) -> Path:
    return tmp_path / "world"


@pytest.fixture
def world(world_path: Path) -> Store:
    return verbs.open_world(world_path)


@pytest.fixture
def notes_file(tmp_path: Path) -> Path:
    path = tmp_path / "notes.txt"
    path.write_text("Buy oat milk.\nCall Dana about the itinerary.\n", encoding="utf-8")
    return path
