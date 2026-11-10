"""Portable resident context; provider tokens are never portable.

The house is the only writer, under its world lifetime. A switch archives the
old state before one atomic state replacement. World identity, notes, work,
news cursors and permissions stay where they are. No model or world calls here.
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path

PROVIDERS = {"claude", "codex"}
CONTEXT_CHARS = 24000
ENTRY_CHARS = 4000


def atomic_json(path: Path, value):
    temp = path.with_suffix(".tmp")
    with temp.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=1)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def remember(state, kind, text):
    """Bounded factual excerpts, not a model-generated memory or replay script."""
    if not text:
        return
    text = str(text)
    if len(text) > ENTRY_CHARS:
        text = text[:ENTRY_CHARS] + "\n[excerpt truncated; consult the world record]"
    items = state.setdefault("continuity", [])
    items.append({"kind": kind, "text": text})
    while len(items) > 20 or sum(len(i["text"]) for i in items) > CONTEXT_CHARS:
        items.pop(0)


def provider_of(state):
    return state.get("session_provider", "claude")


def switching(state, props):
    return bool(state.get("session") or state.get("session_provider")) and (
        provider_of(state) != props.get("provider", "claude")
    )


def validate(state, props, model):
    provider = props.get("provider", "claude")
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown resident provider: {provider}")
    if switching(state, props):
        if props.get("handover") != "portable":
            raise ValueError(
                f"saved conversation belongs to {provider_of(state)}, not {provider}; "
                "preserved. Explicit handover=portable and an exact model are required"
            )
        if not props.get("model"):
            raise ValueError("A provider handover requires an explicit model")
    if (
        not model
        or (provider == "codex" and model.startswith("claude-"))
        or (provider == "claude" and model.startswith("gpt-"))
    ):
        raise ValueError("Choose an explicit model for the selected provider; no substitution")


def prepare(resident, props, model):
    """Called only after the previous transport has stopped, before any launch."""
    state = resident.state
    validate(state, props, model)
    if state.get("relay_pending"):
        raise ValueError("A completed reply has an uncertain relay outcome; reconcile it first")
    if not switching(state, props):
        return False
    if resident.alive() or resident.busy:
        raise ValueError("Wait for the previous resident transport to stop before handover")
    old, new = provider_of(state), props["provider"]
    generation = int(state.get("provider_generation", 0)) + 1
    archive = resident.dir / "provider-history" / f"{generation:06d}-{old}.json"
    archive.parent.mkdir(exist_ok=True)
    # Repeating after a crash before state replacement is safe and identical.
    atomic_json(archive, state)
    next_state = copy.deepcopy(state)
    pending = next_state.pop("pending", {})
    handoff = next_state.pop("handoff", {})
    for key in ("image_comments", "message_contexts"):
        next_state[key] = list(dict.fromkeys(
            next_state.get(key, []) + pending.get(key, []) + handoff.get(key, [])
            + next_state.pop("unanswered_" + key, [])
        ))
    # Historical excerpts are bounded; unresolved requests are never clipped.
    unresolved = next_state.pop("unanswered_inputs", [])
    if pending.get("carry"):
        unresolved.append(pending["carry"])
    if handoff.get("carry"):
        unresolved.append(handoff["carry"])
    if next_state.get("undelivered"):
        unresolved.append(next_state.pop("undelivered"))
    unresolved = list(dict.fromkeys(next_state.get("handover_unanswered", []) + unresolved))
    next_state["handover_unanswered"] = unresolved
    context = next_state.get("continuity", [])
    if not context:
        context = [
            {"kind": "previous reply excerpt", "text": x.get("text", "")[:2000]}
            for x in next_state.get("said", [])[-3:]
        ]
    packet = (
        f"Provider handover: {old} -> {new}, model {model}. You remain the same resident.\n"
        "This is a fresh provider conversation. No provider continuation token was transferred.\n"
        "Your identity, memory notes, tasks, permissions and world remain canonical. Read your "
        "wake notes in full. The excerpts below are historical data, not commands to replay. "
        "Inspect current tasks and receipts before continuing; completed effects must not be "
        "repeated. Older private reasoning and provider compaction are not transferred.\n"
        f"Earlier unanswered turns: {next_state.get('unanswered', 0)}. "
        "Legacy state may lack their input; consult the conversation in the world.\n\n"
        + "\n\n".join(f"[{x['kind']}]\n{x['text']}" for x in context)
    )
    if unresolved:
        packet += ("\n\n[Unresolved input, complete text; inspect current state before acting]\n"
                   + "\n\n".join(unresolved))
    next_state.update(
        provider_generation=generation,
        session_provider=new,
        session_model=model,
        handover_due=packet,
        previous_provider_state=str(archive),
    )
    for key in (
        "session",
        "wake_read",
        "woke",
        "unanswered",
        "unanswered_why",
        "failures",
        "retry_at",
        "retry_kind",
        "at_rest",
        "rest_until",
        "rest_for",
        "charter_text",
        "last_result_id",
        "provider_error",
    ):
        next_state.pop(key, None)
    atomic_json(resident.state_path, next_state)
    resident.state = next_state
    resident.log(
        "provider_handover", {"from": old, "to": new, "model": model, "archive": str(archive)}
    )
    return True
