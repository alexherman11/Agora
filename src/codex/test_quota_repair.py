"""Quota decisions and prepare draining: isolated state, fake pipes, no model."""

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "text-desk/notation"))
import plan_usage
import quota_policy as policy
import workshop


def props():
    return dict(
        provider="codex",
        model="gpt-6-astra",
        reasoning="low",
        preferred_provider="codex",
        preferred_model="gpt-6-astra",
        preferred_reasoning="low",
        fallback_provider="claude",
        fallback_model="claude-sonnet-5-5",
        fallback_reasoning="medium",
        quota_failover="on",
    )


def plans(codex=0, claude=0):
    return SimpleNamespace(
        wait_until=lambda p: {"codex": codex, "claude": claude}[p], reset=lambda p: 0
    )


@pytest.mark.parametrize(
    "text",
    [
        "You've hit your session limit · resets 1:20pm",
        "You've hit your usage limit",
        "usage_limit_reached",
        "insufficient_quota",
    ],
)
def test_explicit_subscription_exhaustion(text):
    assert policy.quota_error(text)


@pytest.mark.parametrize(
    "text",
    [
        "429 rate limit exceeded, retry shortly",
        "authentication expired",
        "permission denied",
        "thread not found",
        "Network connection lost",
        "not rate limited",
        "invalid API key, usage limit request rejected",
    ],
)
def test_other_failures_are_not_quota(text):
    assert not policy.quota_error(text)


def test_exhausted_codex_uses_independent_configured_subscription():
    target, reason = policy.choose({}, props(), plans(codex=1500), 1000)
    assert target == dict(provider="claude", model="claude-sonnet-5-5", reasoning="medium")
    assert reason == "verified subscription limit"


def test_model_switch_in_same_pool_cannot_evade_quota():
    p = props()
    p.update(fallback_provider="codex", fallback_model="gpt-6.1-sol")
    assert policy.choose({}, p, plans(codex=1500), 1000) is None


@pytest.mark.parametrize(
    "state,busy",
    [
        ({"relay_pending": {"phase": "applying"}}, False),
        ({"retry_kind": "process"}, False),
        ({"quota_check_after": 1100}, False),
        ({}, True),
        ({"session_provider": "claude"}, False),
    ],
)
def test_no_switch_during_uncertain_or_nonquota_work(state, busy):
    assert policy.choose(state, props(), plans(codex=1500), 1000, busy=busy) is None


def test_both_exhausted_wait_then_return_to_preferred_without_thrash():
    p = props()
    assert policy.choose({}, p, plans(1500, 1600), 1000) is None
    p.update(provider="claude", model="claude-sonnet-5-5", reasoning="medium")
    state = {"session_provider": "claude", "quota_check_after": 1000}
    assert policy.choose(state, p, plans(1500, 1600), 1400) is None
    target, _ = policy.choose(state, p, plans(1500, 1600), 1501)
    assert target["model"] == "gpt-6-astra" and target["reasoning"] == "low"
    assert policy.choose({}, props(), plans(), 1601) is None


def test_policy_requires_explicit_opt_in_and_exact_model():
    p = props()
    p.pop("quota_failover")
    assert policy.choose({}, p, plans(1500), 1000) is None
    p = props()
    p["fallback_model"] = ""
    assert policy.choose({}, p, plans(1500), 1000) is None


def test_claude_fallback_never_inherits_api_keys():
    result = SimpleNamespace(
        returncode=0,
        stdout='{"loggedIn":true,'
        '"authMethod":"claude.ai","apiProvider":"firstParty",'
        '"subscriptionType":"max"}',
    )
    with patch.object(policy.subprocess, "run", return_value=result) as run:
        env = policy.claude_environment(
            "fixture",
            {"ANTHROPIC_API_KEY": "fixture", "ANTHROPIC_AUTH_TOKEN": "fixture", "PATH": "keep"},
        )
    assert env == {"PATH": "keep"}
    assert run.call_args.kwargs["env"] == env


def test_claude_api_login_or_custom_endpoint_is_not_fallback():
    with patch.object(
        policy.subprocess,
        "run",
        return_value=SimpleNamespace(
            returncode=0, stdout='{"loggedIn":true,"authMethod":"api_key"}'
        ),
    ):
        with pytest.raises(ValueError, match="subscription"):
            policy.claude_environment("fixture", {})
    with pytest.raises(ValueError, match="routing"):
        policy.claude_environment("fixture", {"ANTHROPIC_BASE_URL": "fixture"})


def test_prepare_consumes_result_before_stopping_idle_owner():
    ws = object.__new__(workshop.Workshop)
    ws.house = SimpleNamespace(plans=Mock())
    wk = SimpleNamespace(busy=True, state={"session": "preserved"}, save=Mock(), log=Mock())

    def drain():
        wk.busy = False
        return ["completed"]

    wk.turns_ended = Mock(side_effect=drain)
    wk.alive, wk.stop = Mock(return_value=True), Mock()
    ws.prepare_idle("fixture", wk)
    wk.stop.assert_called_once()
    assert wk.state["session"] == "preserved" and wk._prepare_stopped_owner


def test_prepare_does_not_cut_genuine_active_turn():
    ws = object.__new__(workshop.Workshop)
    ws.house = SimpleNamespace(plans=Mock())
    wk = SimpleNamespace(busy=True, turns_ended=lambda: [], stop=Mock())
    ws.prepare_idle("fixture", wk)
    wk.stop.assert_not_called()


def test_old_claude_pause_cannot_relabel_codex_worker():
    p = object.__new__(plan_usage.Plans)
    worker = SimpleNamespace(state={"session_provider": "codex"})
    p.house = SimpleNamespace(workshop=SimpleNamespace(workers={"card": worker}))
    p.state = {"pauses": {}}
    p.clock = lambda: 1000
    p.save, p.target, p.flush_notices = Mock(), Mock(), Mock()
    p.paused("claude", "card", 2000)
    p.target.assert_not_called()
    assert p.state["pauses"]["claude"]["targets"] == ["card"]


def test_switch_notice_outbox_survives_repeated_house_passes():
    p = object.__new__(plan_usage.Plans)
    p.state = {}
    p.save, p.flush_notices = Mock(), Mock()
    p.announce("one-switch", "Switched once")
    p.announce("one-switch", "Switched once")
    assert len(p.state["announcements"]) == 1
    p.save.assert_called_once()


def test_native_switch_and_portable_resume_preserve_unfinished_state(tmp_path):
    import copy
    import json

    import resident_continuity as continuity

    native = props()
    p = plans(codex=1500)
    p.announce = Mock()
    h = SimpleNamespace(plans=p, claude="fixture")
    node = {"props": native}
    h.load = lambda: SimpleNamespace(nodes={"fixture": node})

    def act(who, line):
        assert who == "house" and "handover=portable" in line
        assert 'provider="claude"' in line
        native.update(
            provider="claude", model="claude-sonnet-5-5", reasoning="medium", handover="portable"
        )

    h.act = Mock(side_effect=act)
    r = SimpleNamespace(
        rid="fixture",
        house=h,
        dir=tmp_path,
        state_path=tmp_path / "state.json",
        busy=False,
        state={
            "session_provider": "codex",
            "session_model": "gpt-6-astra",
            "session": "private-thread",
            "cursor": 42,
            "pending": {"carry": "complete unanswered request", "delivered": True},
            "continuity": [{"kind": "receipt", "text": "completed once"}],
        },
        log=Mock(),
        alive=lambda: False,
    )
    r.save = lambda: r.state_path.write_text(json.dumps(r.state))
    with (
        patch.object(policy.time, "time", return_value=1000),
        patch.object(policy, "claude_environment", return_value={}),
    ):
        policy.apply(h, r, node)
    assert continuity.prepare(r, native, native["model"])
    assert "session" not in r.state and r.state["cursor"] == 42
    assert r.state["handover_unanswered"] == ["complete unanswered request"]
    assert "completed once" in r.state["handover_due"]
    saved = copy.deepcopy(r.state)
    assert policy.choose(r.state, native, p, 1050) is None
    assert r.state == saved
    assert h.act.call_count == 1 and p.announce.call_count == 1
    preferred, _ = policy.choose(r.state, native, p, 1501)
    native.update(preferred)
    assert continuity.prepare(r, native, native["model"])
    assert r.state["session_model"] == "gpt-6-astra"
    assert r.state["handover_unanswered"] == ["complete unanswered request"]


def test_failed_subscription_login_never_changes_provider(tmp_path):
    p = plans(codex=1500)
    p.target = Mock()
    h = SimpleNamespace(plans=p, claude="fixture", act=Mock())
    r = SimpleNamespace(rid="fixture", state={}, busy=False, save=Mock())
    node = {"props": props()}
    with (
        patch.object(policy.time, "time", return_value=1000),
        patch.object(
            policy, "claude_environment", side_effect=ValueError("subscription unavailable")
        ),
    ):
        assert policy.apply(h, r, node) is node
    h.act.assert_not_called()
    assert r.state["quota_check_after"] == 1300
