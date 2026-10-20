"""Read a copied world, optionally generate this worktree's AGENTS block, stub starts.

Never saves the world or starts a model. Uses the ordinary Worker.start code
with only Popen/the stdout reader stubbed.
"""

# ruff: noqa: E402 -- import the lab and its shared scratch helper after path bootstrap
import argparse
import io
import os
import re
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "window-lab"))
os.environ.setdefault("HOUSE_CLAUDE", "claude")
import agora_tmp
import charter
import export_docs
import workshop
from desk import split_batch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("world", default="frontier-try", nargs="?")
    parser.add_argument("--write-agents", action="store_true")
    args = parser.parse_args()
    d = export_docs.load(args.world)
    w = d.world
    print(f"Copy at {w.events[-1]['id']}: {len(w.events)} events")
    reading = charter.read(w)
    print(
        f"Live charter: {reading.words} injected words; "
        f"{reading.ref}; {reading.warning or 'whole note'}"
    )
    if args.write_agents:
        path = HERE.parents[2] / "AGENTS.md"
        with path.open(encoding="utf-8", newline="") as f:
            old = f.read()
        block = charter.generated(w)
        if "\r\n" in old:
            block = block.replace("\n", "\r\n")
        with path.open("w", encoding="utf-8", newline="") as f:
            f.write(charter.replace_block(old, block))
        print("Generated AGENTS.md block in this worktree only.")
    scratch = Path(agora_tmp.directory("charter-copy-"))

    def act(actor, lines):
        w.me = actor
        if actor not in d._per:
            d._per[actor] = ({}, {w.root}, len(w.events))
        d.seen, d.open, d.last_event_seen = d._per[actor]
        d._window = ""
        outputs = []
        for line in split_batch(lines):
            r = d.dispatch("desk", {"line": line, "whole": True})
            out = r.get("text", r.get("error", ""))
            if r.get("error") or re.search(r"(?:^|\n)(?:ERR|MISS|!! refused)\b", out):
                raise RuntimeError(out)
            outputs.append(out)
        return "\n".join(outputs)

    source = charter.source(w)
    assert source, "Copy needs a charter source"
    new_rule = "- Copy-only updated rule: tests stay hidden."
    act(
        "jeff",
        f"read {reading.ref} :3; do rewrite {reading.ref} "
        f"text={charter.q(new_rule + chr(10) + source['text'])}",
    )
    for provider in ("claude", "codex"):
        got = act(
            "jeff",
            f'look {w.root}; do create {w.root} kind=task title="Charter copy stub" '
            f"worker_provider={provider}",
        )
        cid = re.findall(r"created (a\d+)", got)[-1]
        tree = scratch / provider
        tree.mkdir()
        (tree / "AGENTS.md").write_text("# Copy stub\n", encoding="utf-8")
        host = SimpleNamespace(
            world=args.world,
            dir=scratch / "state",
            fake=True,
            claude="claude.exe",
            load=lambda: w,
            act=act,
        )
        host.dir.mkdir(exist_ok=True)
        wk = workshop.Worker(host, cid, tree, "worker/stub", "jeff")
        proc = MagicMock(pid=123)
        proc.stdout = io.StringIO("")
        with (
            patch.object(workshop.subprocess, "Popen", return_value=proc) as popen,
            patch.object(workshop.threading, "Thread"),
        ):
            wk.start("stub-model", args.world, None)
            cmd = popen.call_args.args[0]
            prompt = (
                cmd[cmd.index("--append-system-prompt") + 1]
                if provider == "claude"
                else (wk.dir / "worker-prompt.txt").read_text(encoding="utf-8")
            )
            popen.call_args.kwargs["stderr"].close()
        assert new_rule in prompt
        comments = w.subjects[w.nodes[cid]["subject"]]["comments"]
        receipt = next(c["text"] for c in reversed(comments) if "rules injected (" in c["text"])
        print(f"{provider} stub prompt contains: {new_rule}")
        print(receipt)
    print("Copy-only edits; no world saved, process or model started.")


if __name__ == "__main__":
    main()
