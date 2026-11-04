"""EDITING A MODULE (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
A module is a seam to something outside the kernel (a model provider, git, Twitch, the media session, a map server) and
turns it into world facts and words. What the world does with them (who is told, when, in what words, how it looks)
belongs in rules, lenses and this module's settings thing, read at each use. Names (JEFF, Alex), ids (dk...), models,
counts, timeouts and message text in this file are debt: move them to settings when you touch them, and never add more.

Claude's SessionStart hook after a compaction: the charter, read again through the door as the agent, given back as
additional context (the old desk's charter.py --hook, on the kernel). Never acts; a failure says so and lets the
compaction go on.

    charter_hook.py --url http://127.0.0.1:8810 --token-file <file> --charter <id>
"""
import argparse
import json
import urllib.request
from pathlib import Path

from messages import message


def reading(url, token, line):
    req = urllib.request.Request(url.rstrip("/") + "/see", json.dumps({"line": line}).encode(),
                                 {"Content-Type": "application/json", "Authorization": "Bearer " + token})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=10) as r:
        out = json.load(r)
    if not out.get("ok"):
        raise RuntimeError("door reading refused")
    return out


def read(url, token, charter):
    rows = reading(url, token, f"look {charter}").get("rows") or [{}]
    return str(rows[0].get("text") or "").strip()


def task_context(url, token, agent):
    rows = reading(url, token, f"look {agent}").get("rows") or [{}]
    cfg = rows[0]
    if cfg.get("next_steps") != "on" or not cfg.get("person"):
        return ""
    return message(lambda line: reading(url, token, line), "Task list header", person=cfg["person"]) + "\n" \
        + reading(url, token, f"rows nextsteps:{cfg['person']}").get("text", "")


def context(url, token_file, charter, agent=None):
    try:
        token = Path(token_file).read_text(encoding="utf-8").strip()
        text = read(url, token, charter)
        if not text:
            raise ValueError("empty charter")
        text = message(lambda line: reading(url, token, line), "After a compaction", charter=charter) \
            + "\n\n" + text
    except Exception as exc:                          # noqa: BLE001  the compaction must go on
        text = f"charter: not read after the compaction ({type(exc).__name__}); look {charter} reads it."
    if agent:
        try:
            tasks = task_context(url, Path(token_file).read_text(encoding="utf-8").strip(), agent)
            if tasks:
                text += "\n\n" + tasks
        except Exception as exc:                      # no credentials or response bodies in diagnostics
            text += f"\nNext steps unavailable after compaction ({type(exc).__name__}); read your nextsteps rows."
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--token-file", required=True)
    ap.add_argument("--charter", required=True)
    ap.add_argument("--agent")
    a = ap.parse_args()
    text = context(a.url, a.token_file, a.charter, a.agent)
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
