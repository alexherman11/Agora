"""Live, bounded agent charter and generated AGENTS.md block (a6536).

The house owns initial reads. Claude's compact hook and the Codex transport use
the same reader at the provider's boundary; no model call or polling is needed.
"""

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
BEGIN = "<!-- agora:standing-rules:begin -->"
END = "<!-- agora:standing-rules:end -->"
ROLE = "agent-charter"
DEFAULT_TITLE = "Alex's standing rules (everyone reads this; JEFF keeps it current)"
LIMIT = 500


def q(value):
    return json.dumps(str(value), ensure_ascii=False).replace("$", r"\$")


def source(world):
    hits = [
        s
        for s in world.subjects.values()
        if (s.get("props", {}).get("role") == ROLE or s.get("title") == DEFAULT_TITLE)
        and world.appearances_of(s["id"])
    ]
    marked = [s for s in hits if s.get("props", {}).get("role") == ROLE]
    hits = marked or hits
    return hits[0] if len(hits) == 1 else None


def bullets(text):
    return [line.strip() for line in text.splitlines() if line.lstrip().startswith("- ")]


def bounded(header, lines, budget=LIMIT):
    """Keep whole rules where possible; one enormous rule cannot overflow."""
    out = header
    for line in lines:
        if len((out + "\n" + line).split()) <= budget:
            out += "\n" + line
        else:
            break
    return out


@dataclass
class Reading:
    text: str
    ref: str
    event: str
    warning: str = ""

    @property
    def words(self):
        return len(self.text.split())

    @property
    def receipt(self):
        return (
            f"rules injected ({self.words} words, as of event {self.event})"
            if not self.warning.startswith("unavailable")
            else f"rules unavailable ({self.warning}); start continues"
        )


def read(world, *, inline=False):
    note = source(world)
    event = world.events[-1]["id"] if world.events else "e0"
    ref = world.appearances_of(note["id"])[0] if note else "prop:role=agent-charter"
    text = (note or {}).get("text", "").strip()
    header = (
        "## Alex's standing rules\n"
        f"Read the live charter first: `read {ref} :3`. "
        f"Single source in the world; snapshot as of event {event}."
    )
    if not text:
        why = "unavailable: charter note is missing, ambiguous or empty"
        missing = "note empty" if note else "note missing or ambiguous"
        return Reading(
            header + f"\ncharter: not read: {missing}; starting without standing rules. Tell JEFF.",
            ref, event, why
        )
    if inline:
        header += "\nGenerated; never hand-edit this block. First ten rules in charter order:"
        return Reading(bounded(header, bullets(text)[:10]), ref, event)
    full = header + "\n\n" + text
    if len(full.split()) <= LIMIT:
        return Reading(full, ref, event)
    header += (
        "\nThe charter exceeds 500 words. This is a bounded extract; "
        "read the full live note before acting."
    )
    return Reading(
        bounded(header, bullets(text)),
        ref,
        event,
        "charter exceeds 500 words; bounded extract injected, full live read required",
    )


def generated(world):
    reading = read(world, inline=True)
    note = source(world)
    refs = set(world.appearances_of(note["id"]) + [note["id"]]) if note else set()
    event = next(
        (
            e["id"]
            for e in reversed(world.events)
            if (e.get("target") in refs and e.get("verb") in ("edit", "prop"))
            or (e.get("verb") == "create" and (e.get("undo") or {}).get("delete") in refs)
        ),
        "e0",
    )
    return (
        BEGIN
        + "\n"
        + reading.text.replace(f"as of event {reading.event}", f"as of event {event}")
        + "\n"
        + END
    )


def replace_block(text, block):
    """Only our marked region changes, even beside uncommitted human edits."""
    if BEGIN not in text and END not in text:
        # Early enough to read, after the title; preserve every existing byte.
        first, sep, rest = text.partition("\n")
        newline = "\r\n" if "\r\n" in text else "\n"
        return first + sep + newline + block + newline + rest
    if text.count(BEGIN) != 1 or text.count(END) != 1:
        raise ValueError("standing-rules markers missing or duplicated; left unchanged")
    a, b = text.index(BEGIN), text.index(END) + len(END)
    if a >= b:
        raise ValueError("standing-rules markers reversed; left unchanged")
    return text[:a] + block + text[b:]


def without_block(text):
    if BEGIN in text or END in text:
        return replace_block(text, "")
    return text


def report(act, target, words):
    # Corners are surfaces, which have no native comments. Keep their last
    # receipt as a world fact; the house also keeps the process event log.
    if target.startswith("f"):
        return act("house", f"look {target} :1; do prop {target} charter_read={q(words)}")
    return act("house", f"look {target} :1; do comment {target} line={q(words)} to=nobody")


def collect(world, act, target, actor, reason, *, commands=True):
    """Read a start charter; start= can add read-only desk commands, never acts."""
    reading = read(world)
    extra = []
    node = world.nodes.get(target) or {}
    start = (node.get("props") or {}).get("start", "")
    # Tasks store props on their subjects, resident surfaces on the node.
    if node.get("subject"):
        start = (world.subjects.get(node["subject"], {}).get("props") or {}).get("start", start)
    if start and commands:
        from desk import split_batch

        for line in split_batch(str(start)):
            line = line.strip()
            # The charter itself is already read whole and bounded above.
            if re.fullmatch(r"read\s+" + re.escape(reading.ref) + r"(?:\s+:3)?", line):
                continue
            if re.fullmatch(r"read\s+prop:role=agent-charter(?:\s+:3)?", line):
                continue
            if not re.fullmatch(r"read[ \t]+\S[^\r\n]*", line):
                extra.append("start hook skipped a non-read command; tell JEFF.")
                continue
            extra.append(act(actor, line))
    text = reading.text + (("\n\nAdditional start reads:\n" + "\n".join(extra)) if extra else "")
    report(
        act,
        target,
        f"charter read (reason: {reason}); {reading.words} words, as of event {reading.event}"
        + (f"; {reading.warning}; JEFF please shorten the charter" if reading.warning else ""),
    )
    return text


def live(world_name, target, actor, reason):
    import desk_mcp
    import export_docs

    world = export_docs.load(world_name).world

    def act(who, line):
        text, _ = desk_mcp.run_desk({"session": world_name, "as": who, "line": line})
        return text

    return collect(world, act, target, actor, reason)


def sync(world, act, path, state):
    """Called by the existing house pass. Revisions, not a new polling loop.

    Both the local file and its carried world note retain all non-generated text.
    An event stamp is the note's last change, so our own export cannot recurse.
    """
    note = source(world)
    key = hashlib.sha256(
        str(
            (
                (note or {}).get("id"),
                (note or {}).get("text", ""),
                world.appearances_of(note["id"]) if note else [],
            )
        ).encode()
    ).hexdigest()
    if state.get("charter_mirror") == key and path.exists():
        return
    # Re-render event provenance using the source revision event, not our mirror's events.
    block = generated(world)
    match = next(
        (
            s
            for s in world.subjects.values()
            if s.get("title") == "AGENTS.md" and world.appearances_of(s["id"])
        ),
        None,
    )
    reading = read(world)
    if note and reading.warning and state.get("charter_warning") != key:
        report(act, reading.ref, "@jeff: " + reading.warning + "; please shorten the charter.")
        state["charter_warning"] = key
    with path.open(encoding="utf-8", newline="") as f:
        before = f.read()
    after = replace_block(before, block.replace("\n", "\r\n") if "\r\n" in before else block)
    if after != before:
        # Recheck immediately before writing; never overwrite an intervening edit.
        with path.open(encoding="utf-8", newline="") as f:
            if f.read() != before:
                raise RuntimeError("AGENTS.md changed during charter generation; retry next pass")
        with path.open("w", encoding="utf-8", newline="") as f:
            f.write(after)
    if match:
        old = match.get("text", "")
        new = replace_block(old, block)
        if old != new:
            ref = world.appearances_of(match["id"])[0]
            if BEGIN in old:
                passage = old[old.index(BEGIN) : old.index(END) + len(END)]
                replacement = block
            else:
                passage = old.split("\n", 1)[0] + "\n"
                replacement = passage + "\n" + block + "\n"
            out = act(
                "house", f"read {ref} :3; do replace {ref} old={q(passage)} new={q(replacement)}"
            )
            if "ERR" in out or "MISS" in out or "refused" in out.lower():
                raise RuntimeError("carried AGENTS.md charter update refused")
    state["charter_mirror"] = key


def claude_hook(python, world, target, actor):
    command = (
        f'"{python}" "{Path(__file__).resolve()}" --world "{world}" '
        f'--target "{target}" --actor "{actor}" --hook'
    )
    return {
        "hooks": {
            "SessionStart": [
                {"matcher": "compact", "hooks": [{"type": "command", "command": command}]}
            ]
        }
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--hook", action="store_true")
    args = parser.parse_args()
    try:
        text = live(args.world, args.target, args.actor, "compaction")
    except Exception as exc:
        # A missing note/service must not break the provider's compaction.
        text = (
            f"charter: not read: source unavailable after compaction ({type(exc).__name__}); "
            "tell JEFF."
        )
    print(
        json.dumps(
            {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
