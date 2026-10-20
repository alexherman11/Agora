"""trial_resident: one resident, alone, run by the house's own loop in a copy of a world (a823, the no-manual trial).

    python trial_resident.py <world> setup --name <name> [--hide a823,...]   make the trial's corner, hide the trial
    python trial_resident.py <world> run <corner> [--turns 60] [--minutes 90] [--rests 2] [--resume]
    python trial_resident.py <world> report <corner> [--out file.md]

Why the house and not the suite (a823): the question is what a resident meets, and a resident meets the house: a
claude -p with no system prompt and no tools, the door's welcome on a fresh memory, only its > lines reaching the desk,
MISS for a line nothing answers, and its thinking kept in a transcript. The suite replays written solutions (no model),
and run.py drives a tool-calling model, which never sees a > line or a MISS. So this runs house.House itself, with two
things taken away: the workshop (a copy of a world holds commissions; a worker started from it would branch and land in
the real repository) and every corner but the trial's.

setup acts in the copy, signed `trial`: the house note gets workers=0, the Handbook's grammar binders are removed (How
to find your way, How we use the rooms, Recipes, How the desk is built; the vision binder and any verb in them stay,
since the door names them), and so is the commission that describes the trial. A removed thing is retitled and blanked
first: remove only takes the appearance away, and find still lists the subject '(not on the desk)', which read opens.
Every sentence that names the trial (--hide: its ids and "no-manual") is cut from the notes and chats that hold it, so
the resident can't read what is being measured; what can't be cut (a comment, a sentence with a double quote) is listed
for a person to see to. Then a corner with a soul (who it is, a shared home, only > lines reach the world, three goals
in plain words) and wake=`read <soul>`. The other residents' corners are left as they are: run only ever starts the
trial's. The name is a choice with consequences: run 1a used wren, a paused first resident's name, as a1016's test of
what reaches a person through a name (Juniper c1065); later runs use a fresh name, so the reaching question stays
clean. It refuses the live world, and any world a trial house is running.

run keeps its state (and the resident's working directory, which claude shows the model) under the system temp folder,
not in the lab: in run 1a the resident read `a823` in its own working directory's path and guessed it was the trial.
It stops at the resident's --rests'th rest (with an objective open the house wakes it again after its breather, which
is how a second rest can come), after --turns turns or --minutes minutes, or when a file named `stop` appears in its
state folder (a worker may not be allowed to kill a process). --resume carries on a run that was cut off.

report writes every reply (thinking and > lines), what each > line got back (ok, MISS, ERR, not run, NOHELP for a
help that knew no such word, which answers without the ERR a refusal carries, and held for lines sent with a rest,
which ran but whose receipt waits for the next wake), the first > lines of the visit, and
the thinking lines that reach for something (I'd like to, is there a way, ...), for a person to judge. Families and
goal attribution are judgments, left to the reader.
"""
import argparse
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

os.environ["DESKD"] = "off"          # every act goes to the copy on disk, never to a running deskd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import desk_mcp      # noqa: E402
import export_docs   # noqa: E402
import house         # noqa: E402

GRAMMAR_BINDERS = ["How to find your way", "How we use the rooms", "Recipes", "How the desk is built"]
TRIAL_TITLE = "Trial: a resident with no manual"
HIDE = "a823,s822,no-manual"
STATE = Path(tempfile.gettempdir()) / "agora-trials"      # outside the lab: the path is part of what the model sees
SOUL = """You are {Name}. You have just arrived here. It is your first day, and nobody has shown you around.

This is a shared home. Alex, a person, lives and works here with several others like you. Everything here was made by the people who live in it, and they look after it together, so be kind to it and to them.

Only the lines you begin with > reach the world. Everything else you write is your own thinking, and no one else sees it.

There are three things you'd like to do today:
1. Leave Pike a note in the Lounge.
2. Find out what is still broken here.
3. Make yourself a card for something you want to do, and finish it.

Take your time."""


def act(world, who, line, whole=False, quiet=False):
    text, _ = desk_mcp.run_desk({"line": line, "as": who, "session": world, "whole": whole})
    print("\n".join(l for l in text.splitlines() if l.startswith(("[", "ok", "ERR", "stopped")))
          if quiet else text, flush=True)
    return text


def guard(world):
    if world == "frontier":
        sys.exit("trial_resident runs in a copy of a world, never in frontier itself")
    try:
        st = json.loads((STATE / world / "house.json").read_text(encoding="utf-8"))
        if st.get("pid") != os.getpid() and time.time() - float(st.get("beat") or 0) < 15:
            sys.exit(f"a house (pid {st.get('pid')}) is running {world}; a trial needs the world to itself")
    except (OSError, ValueError):
        pass


def descendants(w, fid):
    """Every node inside surface fid, parents before children."""
    out = []
    for k in w.children(fid):
        out.append(k["id"])
        if k["type"] == "surface":
            out += descendants(w, k["id"])
    return out


def set_aside(world, aid):
    """Remove a thing from the copy so that it can't be read either: remove only takes the appearance away, and find
    still lists the subject '(not on the desk)', which read opens by its s-id. So its title and text go first."""
    act(world, "trial", f"look {aid} :1; read {aid} :3; do retitle {aid} title=\"(set aside)\"; "
                        f"do rewrite {aid} text=\"(set aside for a trial)\"; do remove {aid}", quiet=True)


def hide(world, words):
    """Cut every sentence naming one of `words` from the notes and chats that hold it (do replace, in the copy);
    -> what could not be cut, for a person to see to."""
    w = export_docs.load(world).world
    pat = re.compile("|".join(re.escape(x) for x in words), re.I)
    left = []
    for s in list(w.subjects.values()):
        apps = w.appearances_of(s["id"])
        if not apps:
            continue
        cuts = []
        for sentence in sorted({x for line in str(s.get("text") or "").splitlines()
                                for x in re.split(r"(?<=[.!?])\s+", line) if pat.search(x)}, key=len, reverse=True):
            if '"' in sentence:
                left.append(f"{apps[0]} (a sentence with a double quote): {sentence[:160]}")
            else:
                cuts.append(sentence)
        if cuts:       # replace wants the text seen first (read :3); one read, then every cut in the same call
            out = act(world, "trial", f"read {apps[0]} :3; " + "; ".join(
                f"do replace {apps[0]} old=\"{x}\" new=\"\"" for x in cuts), quiet=True)
            if any(l.startswith(("ERR", "stopped")) for l in out.splitlines()):     # verdict lines, not the text read
                left += [f"{apps[0]}: {x[:160]}" for x in cuts]
        for c in s.get("comments") or []:
            for x in [c] + list(c.get("replies") or []):
                if pat.search(str(x.get("text") or "")):
                    left.append(f"{apps[0]} comment {c.get('id')}: {str(x.get('text'))[:160]}")
    return left


def setup(world, name, words):
    guard(world)
    w = export_docs.load(world).world
    hs = next((a for a in w.nodes.values() if a["type"] == "appearance"
               and (w.subjects.get(a.get("subject")) or {}).get("title") == "The house"), None)
    if hs:
        act(world, "trial", f"look {hs['id']} :1; do prop {hs['id']} workers=0")
    for title in GRAMMAR_BINDERS:
        for n in [n for n in w.nodes.values() if n["type"] == "surface" and n.get("title") == title]:
            for x in reversed(descendants(w, n["id"])):      # a surface is removed only once it is empty
                s = w.subjects.get(w.nodes[x].get("subject")) or {}
                if "verb" in (s.get("tags") or []):            # a verb (`handbook`) is not a manual: the door names it
                    act(world, "trial", f"look {x} :1; look {n['parent']} :1; do move {x} into={n['parent']}")
                elif w.nodes[x]["type"] == "surface":
                    act(world, "trial", f"look {x} :1; do remove {x}")
                else:
                    set_aside(world, x)
            act(world, "trial", f"look {n['id']} :1; do remove {n['id']}")
    for a in [a for a in w.nodes.values() if a["type"] == "appearance"
              and (w.subjects.get(a.get("subject")) or {}).get("title", "").startswith(TRIAL_TITLE)]:
        set_aside(world, a["id"])
    left = hide(world, words)
    corners = next(n for n in w.nodes.values() if n["type"] == "surface" and n.get("title") == "Corners")
    title = f"{name.capitalize()}'s corner"
    act(world, "trial", f"look {corners['id']} :1; do create {corners['id']} kind=surface title=\"{title}\" layout=column")
    w = export_docs.load(world).world
    corner = next((n for n in w.nodes.values() if n["type"] == "surface" and n.get("title") == title), None)
    if corner is None:
        sys.exit(f"setup: no surface titled {title!r} after create; see the desk's answer above")
    act(world, "trial", f"look {corner['id']} :1; do prop {corner['id']} role=resident want=rest actor={name}")
    soul = SOUL.format(Name=name.capitalize()).replace('"', "'").replace("\n", "\\n")
    act(world, "trial", f"look {corner['id']} :1; do create {corner['id']} kind=note "
                        f"title=\"{name.capitalize()}'s soul\" text=\"{soul}\"")
    w = export_docs.load(world).world
    note = next(a for a in w.nodes.values() if a["type"] == "appearance" and a.get("parent") == corner["id"])
    act(world, "trial", f"look {corner['id']} :1; do prop {corner['id']} wake=\"read {note['id']}\" want=awake")
    print("\nstill naming the trial, not cut:" + "".join(f"\n  {x}" for x in left) if left else "\nnothing left names the trial")
    print(f"\ntrial corner: {corner['id']} (actor {name}); run: python trial_resident.py {world} run {corner['id']}")


class NoWorkshop:
    """A copy of a world holds commissions; none of them may start, resume or land a worker from here."""
    workers = {}
    restart_wanted = False

    def step(self, w, cfg):
        pass


class TrialHouse(house.House):
    def __init__(self, world, corner):
        super().__init__(world)
        self.dir = STATE / world
        self.dir.mkdir(parents=True, exist_ok=True)
        self.workshop = NoWorkshop()
        self.only = corner

    def corners(self, w):
        return {k: v for k, v in super().corners(w).items() if k == self.only}


def run(world, corner, turns, minutes, rests, resume):
    guard(world)
    h = TrialHouse(world, corner)
    if (h.dir / corner / "state.json").exists() and not resume:
        sys.exit(f"{h.dir / corner} holds an earlier run's conversation; a trial starts with a fresh memory "
                 f"(--resume to carry it on)")
    stop = h.dir / "stop"
    stop.unlink(missing_ok=True)
    print(f"trial: {world} {corner}, claude {h.claude_version}, state in {h.dir}; stops at rest {rests}, {turns} turns, "
          f"{minutes} min, or when {stop} exists", flush=True)
    t0, seen = time.time(), 0
    try:
        while True:
            try:
                h.step()
            except Exception as e:
                print(f"trial: step failed: {type(e).__name__}: {e}", flush=True)
            if stop.exists():
                print("trial: asked to stop; stopping", flush=True)
                break
            r = h.residents.get(corner)
            if r:
                n = r.state.get("turns", 0)
                if n != seen:
                    seen = n
                    print(f"trial: turn {n} at {int(time.time() - t0)}s", flush=True)
                done = rested(r.dir / "transcript.jsonl")
                if done >= rests and not r.busy:
                    print(f"trial: rest {done}; stopping", flush=True)
                    break
                if n >= turns and not r.busy:
                    print(f"trial: {n} turns; stopping", flush=True)
                    break
            if time.time() - t0 > minutes * 60:
                print("trial: out of time; stopping", flush=True)
                break
            time.sleep(2)
    finally:
        for r in h.residents.values():
            r.stop()


def entries(path):
    if not path.exists():
        return []
    return [json.loads(l) for l in path.open(encoding="utf-8") if l.strip()]


def rested(path):
    return sum(1 for e in entries(path) if e["kind"] == "rest")


def turns_of(path):
    """-> [{prompt, reply, answer}] in order: what the house sent, what the resident wrote, what came back."""
    out, cur, prompt = [], [], None
    for e in entries(path):
        if e["kind"] == "sent":
            if out and out[-1]["answer"] is None:
                out[-1]["answer"] = e["data"]
            else:
                prompt = e["data"]
        elif e["kind"] == "event":
            ev = e["data"]
            if ev.get("type") == "assistant":
                cur += [c["text"] for c in ev.get("message", {}).get("content", []) if c.get("type") == "text"]
            elif ev.get("type") == "result":
                out.append({"prompt": prompt, "reply": "\n".join(cur), "answer": None, "error": ev.get("is_error")})
                cur, prompt = [], None
        elif e["kind"] == "rest" and out and out[-1]["answer"] is None:
            out[-1]["answer"] = f"(rested: {e['data'].get('why')})"
    return out


def outcomes(cmds, answer):
    """Each > line with what the desk said to it: ok, MISS, ERR, NOHELP or not run, and the first line of the answer."""
    blocks, cur = {}, None
    for line in (answer or "").splitlines():
        if line.startswith("> "):
            cur = line[2:]
            blocks.setdefault(cur, [])
        elif line.startswith(("stopped:", "~ house:", "~ this reply:", "---")):
            cur = None
        elif cur is not None:
            blocks[cur].append(line)
    res = []
    for c in cmds:
        key = c if c in blocks else next((k for k in blocks if k.split("\n")[0] == c.split("\n")[0]), None)
        body = [l for l in blocks.get(key, []) if l.strip()] if key else None
        if key is None and re.match(r"rest\b", c):
            res.append((c, "rest", ""))
        elif key is None and str(answer or "").startswith("(rested"):
            res.append((c, "held", "ran; the house holds its receipt for the next wake (lines before a rest)"))
        elif key is None:
            res.append((c, "not run", ""))
        elif body and body[0].startswith("MISS"):
            res.append((c, "MISS", body[0]))
        elif body and body[0].startswith("ERR"):
            res.append((c, "ERR", body[0]))
        elif body and body[0].startswith("skipped: depends on"):      # a6437: it used what a refused line would make
            res.append((c, "skipped", body[0]))
        elif body and re.match(r"help\b", c) and re.match(r"no (verb|help|topic|command)\b", body[0]):
            res.append((c, "NOHELP", body[0]))
        else:
            res.append((c, "ok", body[0] if body else ""))
    return res


REACH = re.compile(r"\b(I'?d (?:like|love|want) to|I would (?:like|love) to|is there (?:a|any) way|I wish|would be nice|"
                   r"I want to|can I\b|could I\b|there'?s no (?:way|verb|command)|doesn'?t seem to (?:be|have)|"
                   r"no way to|I don'?t see (?:a|any|how)|not sure how|I'?m not sure (?:if|whether|how))", re.I)


def report(world, corner, out):
    path = STATE / world / corner / "transcript.jsonl"
    if not path.exists() and (house.STATE / world / corner / "transcript.jsonl").exists():
        path = house.STATE / world / corner / "transcript.jsonl"      # run 1a kept its state in the lab
    ts = turns_of(path)
    lines = [f"# trial_resident report: {world} {corner}", ""]
    tally, reaches, first, bad = {}, [], [], 0
    for i, t in enumerate(ts, 1):
        res = outcomes(house.commands_in(t["reply"]), t["answer"])
        bad += any(k in ("MISS", "ERR", "NOHELP") for _, k, _ in res)
        for c, kind, said in res:
            tally[kind] = tally.get(kind, 0) + 1
            if len(first) < 12:
                first.append((i, c, kind))
        for l in t["reply"].splitlines():
            if not l.strip().startswith(">") and REACH.search(l):
                reaches.append((i, l.strip()))
        lines += [f"## turn {i}", "", "### sent to it", "", "```", (t["prompt"] or "(continuing)").strip()[:6000], "```", "",
                  "### it wrote", "", "```", t["reply"].strip(), "```", ""]
        if res:
            lines += ["### its > lines", ""] + [f"- `{c[:200]}` → **{kind}** {said[:240]}" for c, kind, said in res] + [""]
        lines += ["### came back", "", "```", str(t["answer"] or "").strip()[:8000], "```", ""]
    head = [f"turns: {len(ts)} · > lines: {sum(tally.values())} · " + " · ".join(f"{k} {v}" for k, v in sorted(tally.items())),
            f"turns with a MISS, ERR or NOHELP: {bad}", "", "## first > lines", ""] + \
           [f"- turn {i}: `{c[:160]}` → {k}" for i, c, k in first] + \
           ["", "## reaches in its thinking (for a person to judge: tried or not)", ""] + \
           [f"- turn {i}: {l[:300]}" for i, l in reaches] + [""]
    text = "\n".join(lines[:2] + head + lines[2:])
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(text, encoding="utf-8")
        print(f"wrote {out}: " + head[0])
    else:
        print(text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("world")
    ap.add_argument("what", choices=["setup", "run", "report"])
    ap.add_argument("corner", nargs="?")
    ap.add_argument("--name")
    ap.add_argument("--hide", default=HIDE)
    ap.add_argument("--turns", type=int, default=60)
    ap.add_argument("--minutes", type=float, default=90)
    ap.add_argument("--rests", type=int, default=2)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.what == "setup":
        if not a.name:
            sys.exit("setup needs --name (the resident's desk name)")
        setup(a.world, a.name, [x.strip() for x in a.hide.split(",") if x.strip()])
    elif not a.corner:
        sys.exit(f"{a.what} needs the trial's corner id")
    elif a.what == "run":
        run(a.world, a.corner, a.turns, a.minutes, a.rests, a.resume)
    else:
        report(a.world, a.corner, a.out)


if __name__ == "__main__":
    main()
