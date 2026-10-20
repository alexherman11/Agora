"""Worker provider routing must preserve existing conversations."""

import hashlib
import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from prepare_worker import TARGET


def pinned_bytes(path):
    """Accept the pinned CRLF bytes or the LF checkout of the same catalog."""
    raw = path.read_bytes()
    return {
        hashlib.sha256(raw).hexdigest(),
        hashlib.sha256(raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")).hexdigest(),
    }


def test_pinned_catalog_per_model():
    """Astra uses the residents' pinned catalog; Sol keeps its own. No model substitution."""
    from codex_worker import pinned_catalog

    path, sha = pinned_catalog("gpt-6-astra")
    assert path.name == "model-catalog.json"
    assert (
        sha
        == json.loads((path.parent / "runtime-lock.json").read_text(encoding="utf-8"))[
            "catalog_sha256"
        ]
    )
    assert sha in pinned_bytes(path)
    path, sha = pinned_catalog("gpt-6.1-sol")
    assert path.name == "worker-model-catalog.json"
    assert sha in pinned_bytes(path)
    with pytest.raises(RuntimeError, match="no substitution"):
        pinned_catalog("gpt-5")


def test_provider_selection_and_resume_guard(tmp_path):
    sys.path.insert(0, str(TARGET.parent))
    module = types.ModuleType("candidate_workshop")
    module.__file__ = str(TARGET)
    source = TARGET.read_text(encoding="utf-8")
    exec(compile(source, str(TARGET), "exec"), module.__dict__)
    host = SimpleNamespace(dir=tmp_path, fake=None, claude="claude.exe", load=lambda: None)
    with (
        patch.object(module.subprocess, "Popen") as popen,
        patch.object(module.threading, "Thread"),
    ):
        popen.return_value.pid = 123
        worker = module.Worker(host, "test", tmp_path, "worker/test", "mica")
        worker.start("claude-opus-5-5", "frontier", {"props": {}})
        assert popen.call_args.args[0][0] == "claude.exe"
        worker.state["session"] = "claude-session"
        props = {"worker_provider": "codex", "worker_model": "gpt-6.1-sol"}
        with pytest.raises(ValueError, match="belongs to claude"):
            worker.start("claude-opus-5-5", "frontier", {"props": props})
        fresh = module.Worker(host, "new", tmp_path, "worker/new", "mica")
        fresh.start("claude-opus-5-5", "frontier", {"props": props})
        command = popen.call_args.args[0]
        assert Path(command[1]).name == "codex_worker.py"
        assert command[command.index("--model") + 1] == "gpt-6.1-sol"
        fresh.state["session"] = "codex-session"
        fresh.start("claude-opus-5-5", "frontier", {"props": props})
        assert popen.call_args.args[0][-2:] == ["--resume", "codex-session"]
        assert fresh.state["session_provider"] == "codex"
