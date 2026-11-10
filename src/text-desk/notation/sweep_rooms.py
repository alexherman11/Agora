"""sweep_rooms (a990, rooms step 2b): every built-in verb, typed from every room, on things made in that room.

    python sweep_rooms.py [world] [out.txt] [--mark]   default frontier-try; prints refusals, writes every try
                                                         --mark: the room titled Desktop says verbs=layout first

Rooms step 2b shows verbs by room and locks nothing: this is the evidence. Run it before and after a change and
compare the files; a line that went from ok to ERR is a built-in newly refused. The world is loaded fresh for each
room and never saved.
"""
import os
import pickle
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
MARK = "--mark" in sys.argv
WORLD = ARGS[0] if ARGS else "frontier-try"
OUT = ARGS[1] if len(ARGS) > 1 else None
RAW = (HERE / "sessions" / f"{WORLD}.pickle").read_bytes()
ME = "sweeper"

# $N a note made here, $M a second one, $S a free surface made here, $T a column surface made here (holding $M)
TRIES = [
    "look $N", "examine $N", "verbs $N", "read $N", "where $N", "pivot $N", "examine $S", "verbs $S",
    "do move $N into=$S", "do move $N to=20,20", "do move $N by=5,5", "do resize $N to=220x120", "do raise $N",
    "do lower $N", "do fold $N", "do unfold $N", "do match $N to=$M", "do tile $S as=row", "do untile $S",
    "do move $N into=$T", "do move $N before=$M", "do move $N after=$M", "do swap $N $M", "do beside $N $M",
    "do sort $T by=title", "do append $N line=sweep", "do retitle $N title=Swept",
    "do rewrite $N text=again", "do replace $N old=again new=anew", "do prop $N k=v", "do tag $N add=swept",
    "do due $N on=2026-10-01", "do comment $N line=hello", "do link $N $M", "do group $N,$M as=row title=G",
    "do create $S kind=note title=Inner", "do remove $M", "find ?swept", "history",
]


def run_room(fid):
    d = pickle.loads(RAW)
    w = d.world
    d._session = WORLD + "-sweep"
    w.me = ME
    d.seen, d.open, d.last_event_seen, d._window = {}, {w.root}, len(w.events), ""
    token = uuid.uuid4().hex

    def one(line):
        r = d.dispatch("desk", {"line": line, "whole": True, "reply": token})
        return r.get("text") or "", r.get("error") or ""

    import rooms
    if MARK:
        for f in rooms.all_rooms(w):
            if w.nodes[f]["title"] == "Desktop":
                w.nodes[f].setdefault("props", {})["verbs"] = "layout"
    rooms.go(w, ME, fid)
    made = {}
    one(f"look {fid} :1")
    for key, line in (("N", f"do create {fid} kind=note title=SweepN text=one"),
                      ("M", f"do create {fid} kind=note title=SweepM text=two"),
                      ("S", f"do create {fid} kind=surface title=SweepS layout=free"),
                      ("T", f"do create {fid} kind=surface title=SweepT layout=column")):
        t, e = one(line)
        if e:
            return [f"{fid} setup {line}: ERR {e.splitlines()[0]}"]
        made[key] = w.last_created
        one(f"look {fid} :1")
    one(f"do place {w.nodes[made['M']]['subject']} into={made['T']}")
    out = []
    for tpl in TRIES:
        line = tpl
        for k, v in made.items():
            line = line.replace("$" + k, v)
        for k, v in made.items():
            if v in w.nodes:
                one(f"look {v} :1")
        t, e = one(line)
        first = (e or "").strip().splitlines()
        err = next((l for l in first if not l.startswith("!!") and l.strip()), "") if e else ""
        out.append(f"{w.nodes[fid]['title']} ({fid}) | {tpl} | " + (f"ERR {err[:140]}" if e else "ok"))
    return out


def main():
    import rooms
    d0 = pickle.loads(RAW)
    lines = []
    for fid in rooms.all_rooms(d0.world):
        lines += run_room(fid)
    text = "\n".join(lines)
    print("\n".join(l for l in lines if "| ok" not in l))
    errs = sum(1 for l in lines if "| ERR" in l)
    print(f"\n{len(lines)} tries, {errs} refused")
    if OUT:
        Path(OUT).write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
