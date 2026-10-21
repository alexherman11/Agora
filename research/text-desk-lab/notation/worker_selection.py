"""Explicit per-commission requests; never aliases, prices or a second scheduler."""
import json
import math
import re
import subprocess


class Refused(ValueError):
    pass


def requested(props):
    return bool(props.get("requested_model") or props.get("requested_effort"))


def fingerprint(props):
    return [props.get(k) for k in ("requested_model", "requested_effort", "requested_retry")]


def provider(model):
    if re.fullmatch(r"claude-[a-z0-9.-]+", model):
        return "claude"
    if re.fullmatch(r"gpt-[a-z0-9.-]+", model):
        return "codex"
    raise Refused("requested_model needs an exact runtime catalog name; aliases are not accepted")


def resolve(props, saved, default_provider, default_model, cfg):
    model = str(props.get("requested_model") or "")
    runtime = provider(model) if model else default_provider
    model = model or (saved.get("model") if saved.get("session") else None) or default_model
    effort = str(props.get("requested_effort") or (
        saved.get("effort") if saved.get("session") else None) or (
        cfg.get("worker_claude_effort") if runtime == "claude"
        else props.get("worker_reasoning")) or "medium")
    if not re.fullmatch(r"[a-z]+", effort) or effort == "ultra":
        raise Refused("unsupported requested_effort (automatic delegation is not admitted)")
    if saved.get("session") and requested(props):
        bound = saved.get("session_provider", "claude")
        if bound != runtime or saved.get("model") != model:
            raise Refused("request conflicts with saved runtime; conversation preserved")
        if props.get("requested_effort") and saved.get("effort") != effort:
            raise Refused("request conflicts with saved or unknown effort; conversation preserved")
    return {"provider": runtime, "model": model, "effort": effort}


def validate_catalog(models, model, effort, *, codex=False):
    """Consume only public capability metadata, not account/profile contents."""
    for raw in models:
        if hasattr(raw, "model_dump"):
            raw = raw.model_dump(by_alias=True, mode="json")
        if not isinstance(raw, dict):
            raise Refused("malformed runtime catalog; no substitution")
        if raw.get("model" if codex else "value") != model:
            continue
        try:
            levels = ({v["reasoningEffort"] for v in raw.get("supportedReasoningEfforts", [])}
                      if codex else set(raw.get("supportedEffortLevels") or []))
        except (KeyError, TypeError):
            raise Refused("malformed effort capabilities; no substitution") from None
        if effort not in levels:
            raise Refused(f"{model} does not advertise effort {effort}; no substitution")
        return
    raise Refused(f"{model} unavailable in runtime catalog; no substitution")


def claude_catalog(binary, cwd, env):
    """One initialize-only CLI exchange, no user message, tools or saved session.

    Uses the Agent SDK's existing control protocol. Missing/old metadata refuses;
    no guessed fallback list and no inference-based availability probe.
    """
    request_id = "agora-model-capabilities"
    message = {"type": "control_request", "request_id": request_id,
               "request": {"subtype": "initialize", "hooks": {}, "agents": {}}}
    cmd = [binary, "-p", "--input-format", "stream-json", "--output-format", "stream-json",
           "--verbose", "--tools", "", "--strict-mcp-config", "--mcp-config",
           '{"mcpServers":{}}', "--setting-sources", "", "--settings",
           '{"disableAllHooks":true}', "--no-session-persistence", "--system-prompt", ""]
    try:
        auth = subprocess.run([binary, "auth", "status", "--json"], capture_output=True,
                              text=True, encoding="utf-8", cwd=cwd, env=env, timeout=10)
        auth_data = json.loads(auth.stdout)
        if (auth.returncode or not isinstance(auth_data, dict)
                or auth_data.get("loggedIn") is not True):
            raise Refused("Claude sign-in unavailable; no model turn sent")
        result = subprocess.run(cmd, input=json.dumps(message) + "\n", capture_output=True,
                                text=True, encoding="utf-8", cwd=cwd, env=env, timeout=20)
        if result.returncode or len(result.stdout) > 4 * 1024 * 1024:
            raise Refused("Claude model catalog unavailable; no model turn sent")
        for line in result.stdout.splitlines():
            event = json.loads(line)
            if not isinstance(event, dict):
                raise Refused("Claude model catalog malformed; no model turn sent")
            response = event.get("response") or {}
            if not isinstance(response, dict):
                raise Refused("Claude model catalog malformed; no model turn sent")
            if (event.get("type") == "control_response"
                    and response.get("request_id") == request_id
                    and response.get("subtype") == "success"):
                payload = response.get("response") or {}
                if not isinstance(payload, dict):
                    raise Refused("Claude model catalog malformed; no model turn sent")
                models = payload.get("models")
                if isinstance(models, list):
                    return models
    except Refused:
        raise
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass
    raise Refused("Claude model catalog unavailable; no model turn sent")


def receipt(event):
    """Allowlisted runtime evidence; absent fields stay absent, never estimated."""
    if event.get("type") == "system" and event.get("subtype") == "init":
        return {k: event[k] for k in ("model", "effort") if isinstance(event.get(k), str)}
    if event.get("type") == "result":
        out = {k: numbers(event[k]) for k in ("usage", "modelUsage")
               if isinstance(event.get(k), dict)}
        if numeric(event.get("total_cost_usd")):
            out["total_cost_usd"] = event["total_cost_usd"]
        return out
    if event.get("type") == "codex_event" and event.get("method") == "thread/tokenUsage/updated":
        return {"tokenUsage": numbers((event.get("data") or {}).get("tokenUsage") or {})}
    return {}


def numbers(data, depth=0):
    if not isinstance(data, dict) or depth > 3:
        return {}
    return {k: numbers(v, depth + 1) if isinstance(v, dict) else v
            for k, v in data.items()
            if isinstance(v, dict) or numeric(v)}


def numeric(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
