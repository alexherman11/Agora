"""move_jeff: JEFF moves into Alex's desktop world (MOVING-IN.md, build step 1, last piece).

    python move_jeff.py carry          his soul (frontier a5191) and Alex's standing rules (a6529) become things he
                                       made on the desktop, word for word; his house-agent names them
    python move_jeff.py wake           his house-agent want=awake: the house starts him (warm, no turn)
    python move_jeff.py retire-old     his old-desk corner f5189 want=asleep, so only one JEFF runs

Reads the old desk through its door (8794) and writes the desktop through its own (8810), as JEFF for what is his and as
Alex's agent for the house settings. Run again: what is already carried is left alone. Souls move as they are (T3: "i
approve it all"); the edits T3 names happen in step 2, with JEFF.
"""
import argparse
import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
DESK = HERE.parents[1] / "window-lab" / "kernel-desktop"
sys.path.insert(0, str(DESK))
from kd_say import say  # noqa: E402

OLD = "http://127.0.0.1:8794/api/do"
SOUL, CHARTER, CORNER = "a5191", "a6529", "f5189"


def old(line):
    req = urllib.request.Request(OLD, json.dumps({"session": "frontier", "as": "claude", "line": line,
                                                  "whole": True}).encode(), {"Content-Type": "application/json"})
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=30) as r:
        out = json.load(r)
    return out.get("text", "") if isinstance(out, dict) else str(out)


def note_text(ref):
    """`read <ref> :3` prints a header, ---, the note's text, ---, then its comments: the text alone."""
    got = old(f"read {ref} :3")
    parts = got.split("\n---\n", 1)
    if len(parts) < 2:
        raise RuntimeError(f"{ref}: could not read its text ({got[:200]})")
    head, rest = parts
    return head.splitlines()[0], rest.split("\n---", 1)[0].strip()


def q(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def tokens(world):
    s = json.loads((Path(world) / "keep" / "sessions.json").read_text(encoding="utf-8"))
    return {v.get("signer"): t for t, v in s.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["carry", "wake", "retire-old"])
    ap.add_argument("--world", default=str(DESK / "state" / "world"))
    ap.add_argument("--port", type=int, default=8810)
    a = ap.parse_args()
    tok = tokens(a.world)

    def line(text, who="claude"):
        r = say(text, tok[who], a.port)
        print(f"{who}> {text[:90]}\n  {r.get('text', '').splitlines()[0] if r.get('text') else r}")
        if not r.get("ok"):
            raise SystemExit(1)
        return r
    agent = line("rows house-agent name=JEFF")["rows"][0]
    if a.step == "carry":
        made = {}
        for kind, ref, name in (("soul", SOUL, "JEFF's soul"), ("charter", CHARTER, "Alex's standing rules")):
            have = line(f"rows {kind}", "jeff")["rows"]
            if have:
                made[kind] = have[0]["id"]
                continue
            header, text = note_text(ref)
            r = line(f"make kind={kind} name={q(name)} carried_from={q('frontier ' + ref + ': ' + header[:120])} "
                     f"text={q(text)}", "jeff")
            made[kind] = r["made"][0]
        line(f"look {agent['id']}")
        line(f"set {agent['id']} soul={made['soul']} charter={made['charter']} fallback_reasoning=low")
    elif a.step == "wake":
        line(f"look {agent['id']}")
        line(f"set {agent['id']} want=awake")
    else:
        print(old(f"do prop {CORNER} want=asleep"))
        print(old(f"look {CORNER} :1")[:300])


if __name__ == "__main__":
    main()
