"""Isolated provider continuity and fail-closed relay tests; no live world/model."""

import copy
import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "text-desk/notation"))
import house
import resident_continuity as continuity
from codex_resident import build_config, model_catalog, require_subscription, serve


@pytest.fixture
def resident(tmp_path):
    props = {"actor": "jeff", "provider": "claude", "model": "claude-sonnet-5-5",
             "role": "resident"}
    world = SimpleNamespace(nodes={"corner": {"type": "surface", "props": props}},
                            subjects={}, events=[])
    host = SimpleNamespace(
        dir=tmp_path,
        world="fixture",
        load=lambda: world,
        fake=None,
        claude="claude.exe",
        act=Mock(return_value=""),
        welcome_for=lambda r: "Your unchanged identity and memory notes.",
    )
    r = house.Resident(host, "corner")
    r.state = {
        "session": "claude-thread",
        "session_provider": "claude",
        "session_model": props["model"],
        "cursor": 42,
        "inbox": ["keep this task"],
        "for_you": ["new request"],
        "wake_read": {"soul": ["soul", 3]},
        "charter_text": "rules",
        "retry_at": 9999999999,
        "retry_kind": "limit",
    }
    r.save()
    return r, props


def codex(props):
    props.update(provider="codex", model="gpt-6.1-sol", handover="portable")


def test_round_trip_preserves_identity_queues_and_archives_tokens(resident):
    r, props = resident
    original = copy.deepcopy(r.state)
    codex(props)
    assert continuity.prepare(r, props, props["model"])
    archive = Path(r.state["previous_provider_state"])
    assert json.loads(archive.read_text()) == original
    assert r.state["session_provider"] == "codex"
    assert r.state["cursor"] == 42 and r.state["inbox"] == original["inbox"]
    assert r.state["for_you"] == original["for_you"]
    assert not any(k in r.state for k in ("session", "wake_read", "retry_at", "charter_text"))
    assert "No provider continuation token was transferred" in r.state["handover_due"]
    assert not continuity.prepare(r, props, props["model"])
    r.state["session"] = "codex-thread"
    continuity.remember(r.state, "command receipt", "task completed once")
    props.update(provider="claude", model="claude-sonnet-5-5")
    assert continuity.prepare(r, props, props["model"])
    assert "session" not in r.state  # never resume stale Claude work automatically
    assert "task completed once" in r.state["handover_due"]
    assert len(list(archive.parent.glob("*.json"))) == 2
    assert r.house.act.call_count == 0


def test_switch_requires_opt_in_before_any_pending_state_is_consumed(resident):
    r, props = resident
    r.state["pending"] = {"carry": "unfinished request", "delivered": True}
    original = copy.deepcopy(r.state)
    props.update(provider="codex", model="gpt-6.1-sol")
    with pytest.raises(ValueError, match="handover=portable"):
        r.start(props["model"])
    assert r.state == original
    assert not (r.dir / "provider-history").exists()


@pytest.mark.parametrize(
    "provider,model", [("other", "x"), ("codex", "claude-sonnet-5-5"), ("claude", "gpt-6.1-sol")]
)
def test_invalid_selection_never_launches(resident, provider, model):
    r, props = resident
    props.update(provider=provider, model=model, handover="portable")
    with patch.object(house.subprocess, "Popen") as popen, pytest.raises(ValueError):
        r.start(model)
    popen.assert_not_called()


@pytest.mark.parametrize("condition", ["busy", "alive", "relay"])
def test_switch_waits_for_exclusive_settled_transport(resident, condition):
    r, props = resident
    codex(props)
    if condition == "busy":
        r.busy = True
    elif condition == "alive":
        r.proc = Mock()
        r.proc.poll.return_value = None
    else:
        r.state["relay_pending"] = {"phase": "applying", "text": "> do append"}
    with pytest.raises(ValueError):
        continuity.prepare(r, props, props["model"])
    assert r.state["session"] == "claude-thread"


def test_failed_atomic_switch_is_recoverable_without_losing_source(resident):
    r, props = resident
    codex(props)
    old = copy.deepcopy(r.state)
    real = continuity.atomic_json

    def fail_state(path, state):
        if path == r.state_path:
            raise OSError("simulated power loss")
        real(path, state)

    with patch.object(continuity, "atomic_json", side_effect=fail_state), pytest.raises(OSError):
        continuity.prepare(r, props, props["model"])
    assert r.state == old
    assert json.loads(r.state_path.read_text()) == old
    assert continuity.prepare(r, props, props["model"])
    assert len(list((r.dir / "provider-history").glob("*.json"))) == 1


def test_failed_turn_keeps_portable_request_and_attachment_references(resident):
    r, props = resident
    r.hold_unanswered(
        {
            "carry": "finish the open task",
            "delivered": True,
            "image_comments": ["c1"],
            "message_contexts": ["m1"],
        },
        "quota",
    )
    codex(props)
    continuity.prepare(r, props, props["model"])
    assert "finish the open task" in r.state["handover_due"]
    assert r.state["image_comments"] == ["c1"]
    assert r.state["message_contexts"] == ["m1"]
    assert "unanswered" not in r.state


def test_handover_defers_receipt_instead_of_starting_another_old_turn(resident):
    r, props = resident
    codex(props)
    r.proc = Mock()
    r.state["relay_pending"] = {"phase": "applied"}
    r.send("created once; inspect before acting again", "receipt")
    r.proc.stdin.write.assert_not_called()
    assert "created once" in r.state["undelivered"]
    assert not r.busy and "relay_pending" not in r.state


def test_same_provider_resumes_and_handover_uses_fresh_codex_thread(resident):
    r, props = resident
    with patch.object(house.subprocess, "Popen") as popen, patch.object(house.threading, "Thread"):
        popen.return_value.pid = 123
        popen.return_value.poll.return_value = 0
        r.start(props["model"])
        assert popen.call_args.args[0][-2:] == ["--resume", "claude-thread"]
        codex(props)
        with patch.object(house.charter, "collect", return_value="same live rules"):
            r.start(props["model"])
        args = popen.call_args.args[0]
        assert "codex_resident.py" in args[1] and "--resume" not in args
        assert "gpt-6.1-sol" in args
        r.send("You are jeff. Read your soul and the current tasks.", "wake")
        sent = json.loads(popen.return_value.stdin.write.call_args.args[0])
        text = sent["message"]["content"][0]["text"]
        assert "You are jeff" in text and "unchanged identity" in text
        assert "Provider handover" in text
        assert r.state["handover_due"]  # retained until a successful result


def test_context_is_bounded_and_labels_truncation():
    state = {}
    for i in range(100):
        continuity.remember(state, "receipt", str(i) + "x" * 10000)
    assert sum(len(x["text"]) for x in state["continuity"]) <= continuity.CONTEXT_CHARS
    assert "excerpt truncated" in state["continuity"][-1]["text"]


def test_completed_turn_is_saved_before_relay_and_duplicate_id_is_ignored(resident):
    r, _ = resident
    r.reply = ["> do create task"]
    r.events.put({"type": "result", "turn_id": "one"})
    assert r.turns_ended() == ["> do create task"]
    assert json.loads(r.state_path.read_text())["relay_pending"]["phase"] == "received"
    r.events.put({"type": "result", "turn_id": "one"})
    assert r.turns_ended() == []
    assert r.state["turns"] == 1


def test_uncertain_relay_is_not_retried_after_restart(resident):
    r, props = resident
    r.state["relay_pending"] = {"phase": "applying", "text": "> do append"}
    r.save()
    restarted = house.Resident(r.house, r.rid)
    with (
        patch.object(house.subprocess, "Popen") as popen,
        pytest.raises(ValueError, match="uncertain"),
    ):
        restarted.start(props["model"])
    popen.assert_not_called()
    r.house.act.assert_not_called()


def client_for(account):
    client = Mock()
    client.account_read.return_value.model_dump.return_value = {"account": account}
    client.request.return_value.config = {}
    return client


@pytest.mark.parametrize("account", [None, {"type": "apiKey"}, {"type": "amazonBedrock"}])
def test_subscription_guard_refuses_without_auth_mutation(account):
    client = client_for(account)
    with pytest.raises(RuntimeError, match="subscription"):
        require_subscription(client)
    client.account_read.assert_called_once_with({"refreshToken": False})
    client.account_login_start.assert_not_called()
    client.account_logout.assert_not_called()
    client.turn_start.assert_not_called()


def test_subscription_guard_refuses_custom_provider_auth():
    client = client_for({"type": "chatgpt"})
    client.request.return_value.config = {"model_providers": {"openai": {"env_key": "OTHER_KEY"}}}
    with pytest.raises(RuntimeError, match="Custom"):
        require_subscription(client)


def test_no_thread_or_model_turn_before_subscription_guard():
    client = client_for({"type": "apiKey"})
    client.__enter__ = Mock(return_value=client)
    client.__exit__ = Mock(return_value=False)
    with (
        patch("codex_resident.CodexClient", return_value=client),
        patch("codex_resident.runtime_config"),
        patch("codex_resident.sys.stdin", io.StringIO("")),
        pytest.raises(RuntimeError),
    ):
        serve(SimpleNamespace(model="gpt-6.1-sol"))
    client.turn_start.assert_not_called()
    assert not any(x.args[0] == "thread/start" for x in client.request.call_args_list)


def test_sol_metadata_preserves_empty_resident_tools_and_masks_api_environment(tmp_path):
    assert model_catalog("gpt-6.1-sol").name == "worker-model-catalog.json"
    assert model_catalog("gpt-6-astra").name == "model-catalog.json"
    with pytest.raises(ValueError, match="no model was substituted"):
        model_catalog("sol-guess")
    config = build_config(tmp_path, "unused.exe", tmp_path, model="gpt-6.1-sol")
    assert config.env["OPENAI_API_KEY"] == config.env["CODEX_API_KEY"] == ""
    assert "features.shell_tool=false" in config.config_overrides
    assert "features.multi_agent=false" in config.config_overrides
    client = client_for({"type": "chatgpt"})
    assert require_subscription(client) == "chatgpt"


def test_http_timeout_after_possible_commit_never_falls_back(resident):
    r, _ = resident
    host = object.__new__(house.House)
    host.world = "fixture"
    with (
        patch.dict("os.environ", {"DESKD": "http://127.0.0.1:1"}),
        patch(
            "urllib.request.urlopen", side_effect=TimeoutError("response lost after commit")
        ) as request,
        patch.object(house.desk_mcp, "run_desk") as fallback,
    ):
        with pytest.raises(RuntimeError, match="outcome uncertain"):
            host.act("jeff", "do append example line=once", whole=True)
    assert request.call_count == 1
    fallback.assert_not_called()


def test_relay_exception_persists_barrier_and_never_claims_success(resident):
    r, _ = resident
    host = object.__new__(house.House)
    host.act = Mock(side_effect=RuntimeError("uncertain outcome"))
    world = r.house.load()
    host.load = r.house.load
    with pytest.raises(RuntimeError, match="uncertain"):
        host.after_turn(world, r, {}, "jeff", "> do append example line=once")
    saved = json.loads(r.state_path.read_text())
    assert saved["relay_pending"]["phase"] == "applying"
    assert "receipt" not in saved["relay_pending"]
    assert host.act.call_count == 1


def test_worker_results_do_not_enter_resident_relay_recovery(resident):
    r, _ = resident
    r.cid = "fixture-worker"
    r.reply = ["Already acted with native tools"]
    r.events.put({"type": "result", "turn_id": "worker-turn"})
    assert r.turns_ended() == ["Already acted with native tools"]
    assert "relay_pending" not in r.state


def scheduler_for(resident):
    r, props = resident
    h = object.__new__(house.House)
    h.world, h.fake, h.dir = "fixture", True, r.house.dir
    w = r.house.load()
    w.subjects = {}
    h.load = lambda: w
    h.settings = lambda _: dict(house.DEFAULTS)
    h.corners = lambda _: {r.rid: w.nodes[r.rid]}
    h.residents = {r.rid: r}
    h.record_knocks = Mock(return_value=w)
    h.toasts, h.set_status, h.beat, h.wake = Mock(), Mock(), Mock(), Mock()
    h.workshop = SimpleNamespace(restart_wanted=False, step=Mock())
    h.plans, h.usage, h.feeds, h.scripts = Mock(), Mock(), Mock(), Mock()
    h.plans.wait_until.return_value = 0
    return h


def test_scheduler_switches_before_old_provider_cooldown(resident):
    r, props = resident
    codex(props)
    h = scheduler_for(resident)
    r.start = Mock()
    with patch.object(house.feeds, "house_states", return_value={}):
        h.step()
    r.start.assert_called_once_with("gpt-6.1-sol")
    assert "retry_at" not in r.state and r.state["session_provider"] == "codex"
    h.plans.wait_until.assert_called_once_with("codex")
    h.wake.assert_called_once()


def test_scheduler_does_not_overlap_an_inflight_provider(resident):
    r, props = resident
    codex(props)
    h = scheduler_for(resident)
    r.start, r.stop = Mock(), Mock()
    r.busy = True
    r.proc = Mock()
    r.proc.poll.return_value = None
    with patch.object(house.feeds, "house_states", return_value={}):
        h.step()
    r.start.assert_not_called()
    r.stop.assert_not_called()
    assert r.state["session_provider"] == "claude"


@pytest.mark.parametrize("block", ["relay", "provider"])
def test_one_blocked_resident_does_not_starve_the_house(resident, block):
    r, props = resident
    h = scheduler_for(resident)
    r.start = Mock()
    if block == "relay":
        r.state["relay_pending"] = {"phase": "applying"}
    else:
        props["provider"] = "unsupported"
    with patch.object(house.feeds, "house_states", return_value={}):
        h.step()
    r.start.assert_not_called()
    h.workshop.step.assert_called_once()
    assert h.set_status.call_args.args[-1] == ("recovery-needed" if block == "relay" else "error")


def test_offline_transport_failure_cannot_be_mistaken_for_success():
    h = object.__new__(house.House)
    h.world = "fixture"
    with (
        patch.dict("os.environ", {"DESKD": "off"}),
        patch.object(
            house.desk_mcp, "run_desk", return_value=("outcome unknown", True)
        ) as transport,
        pytest.raises(RuntimeError, match="inspect the outcome"),
    ):
        h.act("jeff", "do append task line=once", whole=True)
    assert transport.call_count == 1


@pytest.mark.parametrize("source", ["pending", "failed"])
def test_handover_keeps_entire_unresolved_request_across_failures(resident, source):
    r, props = resident
    body = "long request " + "x" * 30000 + " essential last instruction"
    pending = {"carry": body, "delivered": True}
    if source == "pending":
        r.state["pending"] = pending
    else:
        r.hold_unanswered(pending, "quota")
    codex(props)
    continuity.prepare(r, props, props["model"])
    assert body in r.state["handover_due"]
    # A failed first Codex turn and another handover must retain the full body.
    r.state["session"] = "codex-failed"
    props.update(provider="claude", model="claude-sonnet-5-5")
    continuity.prepare(r, props, props["model"])
    assert body in r.state["handover_due"]
    r.state["pending"] = {"handover_generation": r.state["provider_generation"]}
    r.events.put({"type": "result", "turn_id": "settled"})
    r.turns_ended()
    assert "handover_unanswered" not in r.state


def test_worker_rejects_api_auth_before_thread_creation(tmp_path):
    from contextlib import nullcontext

    import codex_worker

    client = client_for({"type": "apiKey"})
    client.__enter__ = Mock(return_value=client)
    client.__exit__ = Mock(return_value=False)
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Fixture only")
    args = SimpleNamespace(model="gpt-6.1-sol", prompt_file=prompt, mcp_config="unused")
    with (
        patch.object(codex_worker, "CodexClient", return_value=client),
        patch.object(codex_worker, "runtime_config"),
        patch.object(codex_worker, "child_job", return_value=nullcontext()),
        patch.object(codex_worker.sys, "stdin", io.StringIO("")),
        pytest.raises(RuntimeError, match="subscription"),
    ):
        codex_worker.serve(args)
    client.turn_start.assert_not_called()
    assert not any(x.args[0] == "thread/start" for x in client.request.call_args_list)


def test_worker_masks_api_key_environment(tmp_path):
    import codex_worker

    with patch.dict("os.environ", {"OPENAI_API_KEY": "fixture", "CODEX_API_KEY": "fixture"}):
        config = codex_worker.build_config(
            tmp_path, "unused.exe", tmp_path, tmp_path / "model.json")
    assert config.env["OPENAI_API_KEY"] == config.env["CODEX_API_KEY"] == ""


def test_house_os_lease_excludes_second_process_and_recovers_after_death(tmp_path):
    import subprocess

    from house_lease import HouseOwned, house_lease

    code = """
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from house_lease import house_lease
with house_lease(Path(sys.argv[2])):
    print('owned', flush=True)
    sys.stdin.read()
"""
    proc = subprocess.Popen(
        [sys.executable, "-B", "-c", code, str(house.HERE), str(tmp_path)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        assert proc.stdout.readline().strip() == "owned"
        with pytest.raises(HouseOwned), house_lease(tmp_path):
            pytest.fail("second house entered")
        h = object.__new__(house.House)
        h.dir, h.world, h._run_owned = tmp_path, "fixture", Mock()
        assert h.run() == house.ANOTHER
        h._run_owned.assert_not_called()
        other = tmp_path / "different-world"
        other.mkdir()
        with house_lease(other):
            pass
    finally:
        proc.kill()  # fixture process only; proves OS recovery, not cooperative unlock
        proc.communicate(timeout=5)
    with house_lease(tmp_path):
        pass


def test_unavailable_subscription_start_does_not_escape_house_pass(resident):
    r, props = resident
    codex(props)
    h = scheduler_for(resident)
    r.start = Mock(side_effect=ValueError("subscription login unavailable"))
    with patch.object(house.feeds, "house_states", return_value={}):
        h.step()
    h.wake.assert_not_called()
    assert r.state["retry_kind"] == "startup"
    assert r.state["provider_error"] == "subscription login unavailable"
    assert h.set_status.call_args.args[-1] == "error"


def test_applied_receipt_stages_once_across_restart_without_commands(resident):
    r, _ = resident
    r.state["relay_pending"] = {"phase": "applied", "text": "> do append secret",
                                "receipt": "created exactly one item"}
    r.state["undelivered"] = "an earlier message"
    r.state["woke"] = 42
    before = copy.deepcopy(r.state)
    assert r.recover_applied_relay()
    assert "relay_pending" not in r.state and "woke" not in r.state
    assert r.state["session"] == before["session"] and r.state["inbox"] == before["inbox"]
    assert r.state["relay_recovered"]["text"] == before["relay_pending"]["text"]
    assert "do append secret" not in r.state["undelivered"]
    assert "an earlier message" in r.state["undelivered"]
    restored = house.Resident(r.house, r.rid)
    assert not restored.recover_applied_relay()
    assert restored.state["undelivered"].count("created exactly one item") == 1
    r.house.act.assert_not_called()


@pytest.mark.parametrize("case", ["received", "applying", "no-receipt", "pending", "handoff", "busy", "worker"])
def test_relay_uncertainty_is_preserved(resident, case):
    r, _ = resident
    r.state["relay_pending"] = {"phase": "applied", "receipt": "receipt"}
    if case in ("received", "applying"):
        r.state["relay_pending"]["phase"] = case
    elif case == "no-receipt":
        del r.state["relay_pending"]["receipt"]
    elif case in ("pending", "handoff"):
        r.state[case] = {"carry": "uncertain"}
    elif case == "busy":
        r.busy = True
    else:
        r.cid = "worker"
    before = copy.deepcopy(r.state)
    assert not r.recover_applied_relay()
    assert r.state == before
    r.house.act.assert_not_called()


def test_receipt_recovery_save_failure_retains_original_journal(resident):
    r, _ = resident
    r.state["relay_pending"] = {"phase": "applied", "receipt": "receipt"}
    before = copy.deepcopy(r.state)
    with patch.object(r, "save", side_effect=OSError("fixture")), pytest.raises(OSError):
        r.recover_applied_relay()
    assert r.state == before


def test_scheduler_applied_recovery_respects_asleep_then_provider_gate(resident):
    r, props = resident
    r.state["relay_pending"] = {"phase": "applied", "receipt": "receipt"}
    h = scheduler_for(resident)
    props["want"] = "asleep"
    with patch.object(house.feeds, "house_states", return_value={}):
        h.step()
    assert "relay_pending" in r.state
    props.update(want="awake", provider="unsupported")
    r.start = Mock()
    with patch.object(house.feeds, "house_states", return_value={}):
        h.step()
    assert "relay_pending" not in r.state and "receipt" in r.state["undelivered"]
    r.start.assert_not_called()
    assert h.set_status.call_args.args[-1] == "error"
