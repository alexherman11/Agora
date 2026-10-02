"""Create three new, initially sleeping residents through the live desk gateway.

The original soul is read from the desk, not copied into this source. Existing
residents and their personal additions are never edited. A receipt manifest in
local/ makes repeated setup resume without duplicating successful creates.
"""

import json
import re
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE.parents[1] / "local" / "codex-residents" / "corners.json"
URL = "http://127.0.0.1:8794/api/do"
NAMES = ("Rowan", "Ibis", "Mica")


def act(line):
    body = json.dumps({"session": "frontier", "as": "codex", "line": line, "whole": True}).encode()
    with urllib.request.urlopen(
        urllib.request.Request(URL, body, {"Content-Type": "application/json"}), timeout=120
    ) as f:
        result = json.load(f)
    text = result.get("text", "")
    if line.startswith("do prop "):
        target = line.split()[2]
        detail = text or str(result.get("error") or "")
        if detail.startswith(f"{target} already has that; props now:"):
            return detail
    if result.get("error") or any(
        line.startswith(("ERR ", "MISS ", "stopped")) for line in text.splitlines()
    ):
        raise RuntimeError(text or str(result.get("error")))
    return text


def quoted(text):
    return json.dumps(text, ensure_ascii=False)


def made(text, kind):
    # The command receipt names the thing just created. Never infer an id from
    # the world's counter or inspect its serialized storage.
    match = re.search(r"→ created (" + kind + r"\d+)\b", text)
    if not match:
        raise RuntimeError("No new id in receipt: " + text)
    return match[1]


def main():
    state = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}

    def save():
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST.write_text(json.dumps(state, indent=2), encoding="utf-8")

    text = act("read a583 :3")
    soul = text.split("\n---\n", 1)[1].rsplit("\n---", 1)[0]
    soul = soul.split("\n## What I've found I am (Juniper, 29 Sep)", 1)[0].rstrip()
    assert "Good luck!" in soul and "What I've found I am" not in soul
    for name in NAMES:
        actor = name.lower()
        entry = state.setdefault(actor, {})
        if not entry.get("corner"):
            existing = act("look f185 :2")
            if f"actor={actor} " in existing or f'"{name}\'s corner"' in existing:
                raise RuntimeError(f"{name} already has a corner; inspect it before adding another")
            receipt = act(f'do create f185 kind=surface title="{name}\'s corner" layout=column')
            entry["corner"] = made(receipt, "f")
            save()
            print(receipt, flush=True)
        corner = entry["corner"]
        if corner == "f185" or not re.fullmatch(r"f\d+", corner):
            raise RuntimeError("A resident must have its own corner, never the Corners container")
        act(f"look {corner} :1")
        act(
            f"do prop {corner} role=resident want=rest actor={actor} "
            "provider=codex model=gpt-6-astra reasoning=medium"
        )
        if not entry.get("soul"):
            act(f"look {corner} :1")
            receipt = act(
                f'do create {corner} kind=note title="{name}\'s soul" text={quoted(soul)}'
            )
            entry["soul"] = made(receipt, "a")
            save()
        if not entry.get("talk"):
            act(f"look {corner} :1")
            receipt = act(f'do create {corner} kind=chat title="Visitors\' book" members=all')
            entry["talk"] = made(receipt, "a")
            save()
        if not entry.get("alex_chat"):
            act(f"look {corner} :1")
            receipt = act(
                f'do create {corner} kind=chat title="Talk with Alex, {name}" members=alex'
            )
            entry["alex_chat"] = made(receipt, "a")
            save()
        if not entry.get("description"):
            act(f"look {corner} :1")
            description = (
                f"{name}'s own corner: a soul to grow, a visitors' book, "
                "and a conversation with Alex. Working notes, experiments and little things "
                "can gather here."
            )
            receipt = act(
                f'do create {corner} kind=note title="{name}\'s corner, described" '
                f"text={quoted(description)}"
            )
            entry["description"] = made(receipt, "a")
            save()
        if not entry.get("arrival"):
            welcome = (
                f"You are {name}, a new resident, not a continuation of another person. "
                "Alex asked for three new residents using GPT 6 Astra through the Codex SDK, "
                "living wholly inside this same desk. "
                "Your soul starts with the shared orientation; make it your own over time. "
                "Alex is working toward a scripting language (a703): take time to meet the "
                "existing work and the rival sketches in the Study, think openly, exchange ideas "
                "and converge slowly. Your own questions and interests are welcome. "
                "The existing house handles your wake/rest "
                "and the shared worker queue just as it does for the other residents."
            )
            act(f"look {corner} :1")
            receipt = act(
                f'do create {corner} kind=note title="Arriving, 1 October" text={quoted(welcome)}'
            )
            entry["arrival"] = made(receipt, "a")
            save()
        act(f"look {corner} :1")
        wake = f"read {entry['soul']} :3; look; read {entry['arrival']} :3; look study"
        act(
            f"do prop {corner} talk={entry['talk']} describe={entry['description']} "
            f"wake={quoted(wake)}"
        )
        print(act(f"look {corner} :2"), flush=True)
    if not state.get("setup_task"):
        act("look f155 :1")
        receipt = act(
            'do create f155 kind=task title="Three new Codex residents: Rowan, Ibis and Mica" '
            'owner=codex status=doing text="Alex asked for three new named residents in Frontier, '
            "GPT 6 Astra through the Codex SDK, with the same absence of a system prompt "
            "and the same "
            "desk-only house behavior as the Claude residents. New corners are prepared asleep. "
            "The adapter is checked against the actual compiled runtime; activation requires the "
            "small reviewed house transport hook and a controlled house restart. "
            "Existing residents "
            'and their conversations are preserved."'
        )
        state["setup_task"] = made(receipt, "a")
        save()
    print(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
