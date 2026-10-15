"""trial_builders: standing builders with a real model, on a copy of a world (a5378). Costs model turns: a few short ones.

    python trial_builders.py <world-copy> <board> [--model claude-sonnet-5-5] [--screen]

The house's own House (load, act, settings) on the copy, and its workshop's step(), but no resident is ever started:
this script drives the passes. Worktrees are made from a throwaway git repository in a temp folder, never this one, and
a card that is set ready is marked landed without landing anything. Three cards, in turn:
  1. A: the builder chooses a secret word, writes it nowhere, and commits a small file
  2. B: asked what word it chose on its previous card; with --screen it also runs screen_tools look and record and
     opens what they made (nothing appears on the screen: look and record only read it)
  3. C, worker_fresh=yes: a fresh disposable worker says one word
It prints what each card was given (builder, resume, the words it said) and whether B's answer is the word A chose.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

import house      # noqa: E402
import workshop   # noqa: E402

TOOLS = (HERE.parents[1] / "window-lab" / "screen_tools.py").as_posix()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("world")
    ap.add_argument("board")
    ap.add_argument("--model", default="claude-sonnet-5-5")
    ap.add_argument("--screen", action="store_true")
    ap.add_argument("--minutes", type=float, default=8, help="the most one card may take")
    a = ap.parse_args()
    if a.world in ("frontier",) or not (HERE / "sessions" / f"{a.world}.pickle").exists():
        sys.exit("give a copy of a world that exists in sessions/, never the live one")

    tmp = Path(tempfile.mkdtemp(prefix="builders-trial-"))
    repo = tmp / "repo"
    repo.mkdir()
    for args in (["init", "-q", "-b", "main"], ["config", "user.name", "trial"], ["config", "user.email", "trial@local"],
                 ["commit", "-q", "--allow-empty", "-m", "start"]):
        subprocess.run(["git", *args], cwd=repo, check=True)
    real_git = workshop.git
    workshop.git = lambda *args, cwd=None, **k: real_git(*args, cwd=cwd or repo, **k)
    workshop.TREES = tmp / "trees"
    workshop.REPO = repo

    H = house.House(a.world)
    H.dir = tmp / "house-state"            # every worker's and builder's state, in the temp folder
    H.dir.mkdir()
    WS = H.workshop
    cfg = {**H.settings(H.load()), "model": a.model, "worker_model": "", "workers": "4",
           "worker_pool": "2 claude"}

    # only the trial's own cards: a copy holds the live world's open commissions too, and on 15 Oct the first run of
    # this script started builders on three of them before it was stopped
    mine, every = set(), WS.commissions
    WS.commissions = lambda w: {k: v for k, v in every(w).items() if k in mine}

    def land(w, cid, s, wk, wait=True):     # nothing lands: the card is marked landed and its worker finished
        WS.set_state(cid, "landed")
        WS.finish(cid, wk, keep_branch=False)
    WS.land = land

    def card(title, text, **props):
        out = H.act("trial", f"look {a.board} :1")
        out = H.act("trial", f"do create {a.board} kind=task title={json.dumps(title)} text={json.dumps(text)}"
                    + "".join(f" {k}={v}" for k, v in props.items()))
        cid = re.findall(r"created (a\d+)", out)[-1]
        mine.add(cid)
        H.act("trial", f"look {cid} :1; do prop {cid} commission=asked asked_by=trial")
        return cid

    def run(cid, until=("landed", "reported", "done", "failed", "cancelled")):
        end = time.time() + a.minutes * 60
        state = ""
        while time.time() < end:
            w = H.load()
            WS.step(w, cfg)
            s, state = WS.commissions(H.load()).get(cid, (None, ""))
            if state in until:
                return state
            time.sleep(2)
        return f"timed out ({state})"

    def said(cid):
        """Everything the card's worker said this trial: its reply texts and its comments."""
        t = H.dir / f"worker-{cid}" / "transcript.jsonl"
        texts = []
        for line in t.read_text(encoding="utf-8").splitlines() if t.exists() else []:
            e = json.loads(line)
            if e["kind"] == "event" and e["data"].get("type") == "assistant":
                for c in e["data"]["message"].get("content", []):
                    if c.get("type") == "text":
                        texts.append(c["text"])
                    if c.get("type") == "tool_use":
                        texts.append(json.dumps(c.get("input"), ensure_ascii=False))
        return "\n".join(texts)

    def starts(cid):
        t = H.dir / f"worker-{cid}" / "transcript.jsonl"
        return [json.loads(l)["data"] for l in t.read_text(encoding="utf-8").splitlines()
                if json.loads(l)["kind"] == "start"] if t.exists() else []

    trial = ("This is a trial of the house's standing builders on a copy of the world: skip the builders' notebook, the "
             "health checks and the Handbook; nothing here lands. The card is in your desk tool's own default world: "
             "never pass session= (on 15 Oct a worker here guessed 'frontier' and read the live world). ")
    A = card("Trial A: choose a secret word",
             trial + "Choose a secret word of your own, one English word of six letters or more. Do not write it anywhere: "
             "not on the card, not in a file, not in a commit. Say it only in your own reply text, as: SECRET=<word>. "
             "Then make hello.txt in your worktree with the line hi, commit it (git add hello.txt, then git commit), "
             "comment 'done' on the card, and set commission=ready.")
    print("A:", A, run(A))
    look = (f" Then, to try seeing the screen (nothing appears on it): run python {TOOLS} look trial-look.png and open the "
            f"PNG it names with Read; run python {TOOLS} record 3 trial-record.mp4 and open the last frame it names with "
            "Read. Name both files in your comment, and say in two words what kind of thing was on the screen (no more: "
            "it is Alex's own screen).") if a.screen else ""
    B = card("Trial B: what was the word?",
             trial + "On your previous card you chose a secret word. Without looking anywhere (it is written nowhere), "
             "say it in a comment on this card as: WORD=<word>." + look + " Then set commission=reported.")
    print("B:", B, run(B))
    C = card("Trial C: a fresh pair of eyes", trial + "Comment the one word 'fresh' on this card, then set "
             "commission=reported.", worker_fresh="yes")
    print("C:", C, run(C))

    secret = re.findall(r"SECRET=([A-Za-z]+)", said(A))
    answer = re.findall(r"WORD=([A-Za-z]+)", said(B))
    sa, sb, sc = starts(A), starts(B), starts(C)
    print(json.dumps({
        "A": {"builder": [s.get("builder") for s in sa], "resumed": ["--resume" in s["cmd"] for s in sa], "secret": secret},
        "B": {"builder": [s.get("builder") for s in sb], "resumed": ["--resume" in s["cmd"] for s in sb], "answer": answer},
        "C": {"builder": [s.get("builder") for s in sc], "resumed": ["--resume" in s["cmd"] for s in sc]},
        "same_builder": bool(sa and sb and sa[0].get("builder") == sb[0].get("builder") == "builder-1"),
        "remembered": bool(secret and answer and secret[-1].lower() == answer[-1].lower()),
        "fresh_is_disposable": bool(sc and sc[0].get("builder") is None and "--resume" not in sc[0]["cmd"]),
        "state": str(H.dir),
    }, indent=1))
    if a.screen:
        print("B's words about the screen tools:\n" + "\n".join(l for l in said(B).splitlines()
                                                              if "trial-look" in l or "trial-record" in l)[:2000])


if __name__ == "__main__":
    main()
