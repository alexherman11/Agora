"""Desk CLI/MCP must not replay an unacknowledged remote command locally."""

import io
import json
import sys
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "text-desk/notation"))
import desk_mcp
import explore


def test_first_request_may_commit_before_timeout_and_must_not_fall_back(monkeypatch, capsys):
    monkeypatch.setenv("DESKD", "http://fixture")
    effects = []

    def accepted_then_lost(*args, **kwargs):
        effects.append("committed once")
        raise TimeoutError("reply lost")

    call = Mock(side_effect=accepted_then_lost)
    monkeypatch.setattr(urllib.request, "urlopen", call)
    with pytest.raises(SystemExit) as stopped:
        explore.via_deskd("fixture", "alex", ["do append chat line=once"])
    assert stopped.value.code == 2
    assert effects == ["committed once"] and call.call_count == 1
    assert "outcome is uncertain" in capsys.readouterr().out


def test_later_unknown_stops_unsent_tail_without_claiming_no_effect(monkeypatch, capsys):
    monkeypatch.setenv("DESKD", "http://fixture")
    reply = io.BytesIO(json.dumps({"text": "applied"}).encode())
    call = Mock(side_effect=[reply, OSError("reply lost")])
    monkeypatch.setattr(urllib.request, "urlopen", call)
    with pytest.raises(SystemExit):
        explore.via_deskd("fixture", "alex", ["one", "two", "never sent"])
    assert call.call_count == 2
    out = capsys.readouterr().out
    assert "applied" in out and "later lines were not sent" in out
    assert "this one and the rest were not" not in out


def test_explicit_offline_path_still_uses_the_file_lock(monkeypatch):
    monkeypatch.setenv("DESKD", "off")
    call = Mock()
    monkeypatch.setattr(urllib.request, "urlopen", call)
    assert explore.via_deskd("fixture", "alex", ["look"]) is False
    call.assert_not_called()


def test_mcp_reports_unknown_process_exit_as_error_without_retry(monkeypatch):
    monkeypatch.delenv("DESK_PIN", raising=False)
    run = Mock(
        return_value=SimpleNamespace(returncode=2, stdout="ERR outcome is uncertain", stderr="")
    )
    monkeypatch.setattr(desk_mcp.subprocess, "run", run)
    text, failed = desk_mcp.run_desk({"as": "alex", "session": "fixture", "line": "look"})
    assert failed and "uncertain" in text
    assert run.call_count == 1
