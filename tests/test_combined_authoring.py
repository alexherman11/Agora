"""Focused edits, catalog receipts and browser assembly must agree on activation."""

import pytest

from agora3.gateway import Gateway
from agora3.world import Refusal


def test_focused_edit_build_install_and_restore_preserve_source_binding(tmp_path):
    gateway = Gateway(tmp_path)
    actor = gateway.principal("human")
    names = [item["name"] for item in gateway.describe()]
    assert len(names) == len(set(names))
    assert {"package.catalog", "package.patch", "package.check"} <= set(names)
    gateway.dispatch(
        actor,
        "package.save",
        {
            "id": "agora.shell",
            "expected_revision": 0,
            "files": {
                "index.html": "<body><!-- agora:scripts --></body>",
                "main.js": "window.deskVersion = 1;",
            },
            "manifest": {
                "runtime": "browser-1",
                "ui": {"entry": "index.html", "scripts": ["main.js"]},
            },
        },
    )
    first = gateway.dispatch(actor, "package.build", {"id": "agora.shell", "expected_revision": 1})
    gateway.dispatch(actor, "package.install", first["install_args"])
    before = gateway.packages.shell()[0]
    with pytest.raises(Refusal):
        gateway.dispatch(
            actor,
            "package.patch",
            {
                "id": "agora.shell",
                "expected_revision": 1,
                "edits": [
                    {"path": "main.js", "old": "Version = 1", "new": "Version = 2"},
                    {"path": "main.js", "old": "missing", "new": "invalid"},
                ],
            },
        )
    assert gateway.packages.get("agora.shell")["revision"] == 1
    gateway.dispatch(
        actor,
        "package.patch",
        {
            "id": "agora.shell",
            "expected_revision": 1,
            "edits": [{"path": "main.js", "old": "Version = 1", "new": "Version = 2"}],
        },
    )
    item = gateway.dispatch(actor, "package.catalog", {})["packages"][0]
    assert (item["source_revision"], item["installed_source_revision"]) == (2, 1)
    assert gateway.packages.shell()[0] == before
    second = gateway.dispatch(actor, "package.build", {"id": "agora.shell", "expected_revision": 2})
    gateway.dispatch(actor, "package.install", second["install_args"])
    assert "Version = 2" in gateway.packages.shell()[0]
    gateway.packages.install(
        actor, id="agora.shell", build=first["build"], expected_revision=2, restore=True
    )
    assert gateway.packages.shell()[0] == before
    assert gateway.world.verify()["ok"]
