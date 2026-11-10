"""Explicit resident subscription policy. No inference, login or credentials here."""

import json
import re
import subprocess
import time

PROVIDERS = {"claude", "codex"}


def quota_error(detail):
    """An ordinary 429, auth error or tool failure is not subscription exhaustion."""
    text = str(detail or "").lower()
    if any(
        x in text
        for x in (
            "invalid api",
            "unauthorized",
            "authentication",
            "permission denied",
            "thread not found",
            "conversation not found",
            "not rate limited",
        )
    ):
        return False
    return text.strip() == "usage limit" or bool(
        re.search(
            r"usage[_ ]limit[_ ](?:reached|exceeded)|insufficient_quota|"
            r"you.ve (?:hit|reached) your (?:session |weekly |usage )?limit|"
            r"(?:weekly|subscription|session) (?:usage )?limit (?:reached|exceeded)|"
            r"(?:usage|weekly|session) limit.*resets",
            text,
        )
    )


def claude_environment(cli, env):
    """Require the existing subscription login in exactly the child environment."""
    child = dict(env)
    for name in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
        child.pop(name, None)
    if any(
        child.get(k)
        for k in (
            "ANTHROPIC_BASE_URL",
            "CLAUDE_CODE_USE_BEDROCK",
            "CLAUDE_CODE_USE_VERTEX",
            "CLAUDE_CODE_USE_FOUNDRY",
        )
    ):
        raise ValueError("Claude custom/API routing is not an eligible subscription fallback")
    result = subprocess.run(
        [cli, "auth", "status"],
        env=child,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=20,
    )
    try:
        account = json.loads(result.stdout)
    except ValueError:
        account = {}
    if (
        result.returncode
        or not account.get("loggedIn")
        or account.get("authMethod") != "claude.ai"
        or account.get("apiProvider") != "firstParty"
        or not account.get("subscriptionType")
    ):
        raise ValueError("Claude subscription login unavailable; no inference was attempted")
    return child


def selection(props, prefix=""):
    provider = props.get(prefix + "provider", "claude" if not prefix else "")
    model = props.get(prefix + "model", "")
    effort = props.get(prefix + "reasoning", "medium")
    if provider not in PROVIDERS or not model:
        return None
    if (provider == "codex" and not model.startswith("gpt-")) or (
        provider == "claude" and not model.startswith("claude-")
    ):
        return None
    return {"provider": provider, "model": model, "reasoning": effort}


def blocked(plans, provider, now):
    return max(plans.wait_until(provider), plans.reset(provider), 0) > now


def choose(state, props, plans, now, *, busy=False):
    """Only independent provider pools; no Astra-to-Sol quota workaround."""
    if props.get("quota_failover") != "on" or busy or state.get("relay_pending"):
        return None
    if state.get("retry_kind") not in (None, "limit"):
        return None  # never disguise auth/transport/permission/missing-session failures
    if now < state.get("quota_check_after", 0):
        return None
    current, preferred = selection(props), selection(props, "preferred_")
    if not current or not preferred:
        return None
    if state.get("session_provider", current["provider"]) != current["provider"]:
        return None  # finish an already requested handover first
    if current["provider"] != preferred["provider"] and not blocked(
        plans, preferred["provider"], now
    ):
        return preferred, "return to preferred subscription"
    if not blocked(plans, current["provider"], now):
        return None
    fallback = selection(props, "fallback_")
    target = preferred if current["provider"] != preferred["provider"] else fallback
    if not target or target["provider"] == current["provider"]:
        return None
    if blocked(plans, target["provider"], now):
        return None
    return target, "verified subscription limit"


def apply(house, resident, corner):
    """Native selection change, then ordinary portable handover owns the transition."""
    props = corner.get("props") or {}
    now = time.time()
    decision = choose(resident.state, props, house.plans, now, busy=resident.busy)
    if not decision:
        return corner
    target, reason = decision
    # Auth failures never cause another automatic provider change.
    if target["provider"] == "claude":
        try:
            claude_environment(house.claude, __import__("os").environ)
        except (ValueError, OSError, subprocess.SubprocessError) as exc:
            resident.state["quota_check_after"] = now + 300
            resident.state["quota_blocker"] = (
                str(exc) if isinstance(exc, ValueError) else type(exc).__name__
            )
            resident.save()
            house.plans.target(resident.rid, resident.state["quota_blocker"])
            return corner
    fresh = (house.load().nodes.get(resident.rid) or {}).get("props") or {}
    if selection(fresh) != selection(props) or fresh.get("quota_failover") != "on":
        return house.load().nodes.get(resident.rid, corner)
    old = props.get("provider", "claude")
    text = (
        f"JEFF: {reason}; switching {old.title()} to "
        f"{target['model']} ({target['reasoning']}). Work is kept."
    )
    resident.state["quota_check_after"] = now + 60
    resident.save()  # one dispatch attempt; uncertain native outcomes are inspected next pass
    args = " ".join(f"{key}={json.dumps(value)}" for key, value in target.items())
    house.act(
        "house",
        f"look {resident.rid} :1; do prop {resident.rid} {args} "
        f"handover=portable quota_status={json.dumps(text)}",
    )
    node = house.load().nodes.get(resident.rid, corner)
    if selection(node.get("props") or {}) != target:
        return node
    resident.state.pop("quota_blocker", None)
    resident.log("quota_switch", {"from": old, "to": target, "reason": reason})
    resident.save()
    key = (
        f"{resident.rid}:{resident.state.get('provider_generation', 0)}:{old}:{target['provider']}"
    )
    house.plans.announce(key, text)
    return node
