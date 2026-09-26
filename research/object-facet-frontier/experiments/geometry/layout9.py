"""sable-9, first grounding: is a flow's layout already a function of (order, share, parent size)?

sable-9 proposes that a child of a column or row holds only place = {parent, order} and share, and that its box is
derived. That is honest only if today's stored boxes can be reproduced from those choices. Today reflow() recomputes
boxes from the children's CURRENT sizes (equal_share off), so the test is idempotence: reflow the whole world again,
with nothing else changed, and compare every flow child's box.

    python layout9.py        prints, per world and per act, how many flow boxes a second reflow moves

Worlds: Juniper's suite solutions (run in memory) and a home desk driven through ordinary acts. No session is read.
"""

import copy
import importlib.util
import random
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
LAB = Path(__file__).resolve().parents[3] / "text-desk-lab" / "notation"
sys.path.insert(0, str(LAB))
spec = importlib.util.spec_from_file_location("suite_run", LAB / "suite" / "run.py")
suite = importlib.util.module_from_spec(spec)
spec.loader.exec_module(suite)
import explore  # noqa: E402


def flow_boxes(w):
    return {n: (x["x"], x["y"], x["w"], x["h"]) for n, x in w.nodes.items()
            if x.get("parent") in w.nodes and w.nodes[x["parent"]]["layout"] in ("column", "row")}


def reflow_all(w):
    for fid, n in list(w.nodes.items()):
        if n["type"] == "surface" and n.get("parent") is None:
            w.reflow(fid)
    for fid, n in list(w.nodes.items()):             # surfaces whose parent is free are roots of their own flows
        if n["type"] == "surface" and n.get("parent") in w.nodes and w.nodes[n["parent"]]["layout"] == "free":
            w.reflow(fid)


def drift(w):
    """How many flow boxes move when the world is reflowed again with nothing changed, and by how much at most."""
    before = flow_boxes(w)
    c = copy.deepcopy(w)
    reflow_all(c)
    after = flow_boxes(c)
    moved = [n for n in before if before[n] != after.get(n)]
    worst = max((max(abs(a - b) for a, b in zip(before[n], after[n])) for n in moved), default=0)
    return len(before), len(moved), worst


def suite_worlds():
    out = []
    for case in sorted(p.name for p in (LAB / "suite" / "cases").iterdir() if p.is_dir() and not p.name.startswith("_")):
        tspec = importlib.util.spec_from_file_location(f"task_{case}", LAB / "suite" / "cases" / case / "task.py")
        task = importlib.util.module_from_spec(tspec)
        tspec.loader.exec_module(task)
        for sol in sorted((LAB / "suite" / "cases" / case).glob("*.sol")):
            run = suite.Run()
            for line in getattr(task, "SEED", []):
                run.line(line)
            for step in suite.load_solution(sol)["steps"]:
                for op in step["ops"]:
                    if op[0] == "line":
                        run.line(op[3], op[2])
            out.append((f"{case}/{sol.stem}", run.desk.world))
    return out


def home_walk(seed=7, steps=60):
    """A home desk and a walk of ordinary acts, checking drift after each."""
    rnd = random.Random(seed)
    d = explore.fresh()
    run = lambda line: d.dispatch("desk", {"line": line}).get("text") or ""   # noqa: E731
    run("look")
    for t in ("Today", "Later", "Notes"):
        run(f"do create f01 kind=surface title={t} layout=column")
    surfaces = [n for n, x in d.world.nodes.items() if x["type"] == "surface" and x.get("parent") == d.world.root]
    rows = []
    for i in range(steps):
        kids = [n for n, x in d.world.nodes.items() if x["type"] == "appearance"]
        act = rnd.choice(["create", "create", "move", "resize", "remove"] if kids else ["create"])
        if act == "create":
            line = f"do create {rnd.choice(surfaces)} kind=note title=N{i}"
        else:
            k = rnd.choice(kids)
            run(f"look {k}")
            if act == "move":
                line = f"do move {k} into={rnd.choice(surfaces)}"
            elif act == "resize":
                line = f"do resize {k} to={rnd.randint(100, 900)}x{rnd.randint(40, 400)}"
            else:
                line = f"do remove {k}"
        out = run(line)
        total, moved, worst = drift(d.world)
        rows.append((i, line.split()[1], out.startswith("ok"), total, moved, worst))
    return d.world, rows


def main():
    print("SUITE WORLDS: flow boxes a second reflow moves (nothing else changed)")
    for label, w in suite_worlds():
        total, moved, worst = drift(w)
        print(f"- {label}: {moved} of {total} flow boxes move, worst {worst}px")
    w, rows = home_walk()
    print("HOME WALK: after each act, flow boxes a second reflow moves")
    bad = [r for r in rows if r[4]]
    print(f"- {len(rows)} acts ({sum(1 for r in rows if r[2])} ok); acts after which a second reflow moves boxes: {len(bad)}")
    for i, verb, ok, total, moved, worst in bad[:8]:
        print(f"    act {i} {verb} ({'ok' if ok else 'refused'}): {moved} of {total} boxes move, worst {worst}px")
    total, moved, worst = drift(w)
    print(f"- at the end: {moved} of {total} flow boxes move, worst {worst}px")


if __name__ == "__main__":
    main()
