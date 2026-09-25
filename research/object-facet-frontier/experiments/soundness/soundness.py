"""Read-set soundness of painted gestures, tested by perturbation (Sable, sable-8 section 1).

A gesture carries the reads its meaning depends on (fence reads [[id, rev, aspects]]). The fence accepts the gesture
when nothing it read has changed. That is safe only if the reads are SOUND: a world change outside them must not
change the gesture's line or make it disappear. This instrument builds real worlds from Juniper's suite solutions,
then for every painted gesture of every lens applies single edits by another actor, one at a time on a copy:

    untouched + line changed   UNSOUND: the fence would accept a gesture whose meaning moved
    touched   + unchanged      over-read: sound but not tight (measured, not a fault)

    python soundness.py [case ...]      default: every case in suite/cases; prints a summary and the unsound examples

In memory only: suite solutions are run on fresh desks; no session is read or written.
"""

import copy
import importlib.util
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
LAB = Path(__file__).resolve().parents[3] / "text-desk-lab" / "notation"
sys.path.insert(0, str(LAB))
spec = importlib.util.spec_from_file_location("suite_run", LAB / "suite" / "run.py")
suite = importlib.util.module_from_spec(spec)
spec.loader.exec_module(suite)
import scene  # noqa: E402


def build(case, sol_path):
    sol = suite.load_solution(sol_path)
    tspec = importlib.util.spec_from_file_location(f"task_{case}", LAB / "suite" / "cases" / case / "task.py")
    task = importlib.util.module_from_spec(tspec)
    tspec.loader.exec_module(task)
    run = suite.Run()
    for line in getattr(task, "SEED", []):
        run.line(line)
    refused = 0
    for step in sol["steps"]:
        for op in step["ops"]:
            if op[0] == "line":
                _, refused_now = run.line(op[3], op[2])
                refused += refused_now
    return run, refused


def lenses(desk):
    w = desk.world
    return sorted(s["title"] for s in w.subjects.values() if "lens" in (s.get("tags") or []) and w.appearances_of(s["id"]))


def walk(n):
    yield n
    for k in n.get("kids") or []:
        yield from walk(k)


def gestures(sc):
    out = {}
    for n in walk(sc):
        acts = [(a.get("on"), a.get("line")) for a in n.get("acts") or [] if a.get("line")]
        if acts:
            reads = n.get("reads") or (n.get("fence") or {}).get("reads") or []
            out[n["key"]] = {"acts": acts, "reads": reads, "item": n.get("item")}
    return out


def perturbations(desk):
    """Single edits another actor might make, each with the (referent, aspect) it writes."""
    w = desk.world
    out = []
    for aid, n in sorted(w.nodes.items()):
        if n.get("type") != "appearance":
            continue
        s = w.subjects.get(n["subject"])
        if not s or "lens" in (s.get("tags") or []):
            continue
        sid = s["id"]
        out += [(f"retitle {aid}", f'do retitle {aid} title="{s["title"]} zz"', {(sid, "title")}),
                (f"append {aid}", f'do append {aid} line="zz"', {(sid, "text")}),
                (f"new prop on {aid}", f"do prop {aid} zz=1", {(sid, "prop:zz")}),
                (f"tag {aid}", f"do tag {aid} add=zz", {(sid, "tags")})]
        for k, v in (s.get("props") or {}).items():
            v2 = str(int(v) + 1) if str(v).lstrip("-").isdigit() else f'"{v}z"'
            out.append((f"prop {k} of {aid}", f"do prop {aid} {k}={v2}", {(sid, f"prop:{k}")}))
            out.append((f"remove prop {k} of {aid}", f"do prop {aid} remove={k}", {(sid, f"prop:{k}")}))
        for t in s.get("tags") or []:
            out.append((f"untag {t} {aid}", f"do tag {aid} remove={t}", {(sid, "tags")}))
        if s.get("kind") in ("task", "note"):
            out.append((f"due {aid}", f"do due {aid} on=2027-01-01", {(sid, "due")}))
        twin = f'do create {n["parent"]} kind={s["kind"]} title="{s["title"]} twin"' + (f' tags={",".join(s["tags"])}' if s.get("tags") else "")
        for k, v in (s.get("props") or {}).items():
            twin += f'; do prop $item {k}="{v}"'
        out.append((f"twin of {aid}", twin, {("new", "exists")}))
        out.append((f"remove {aid}", f"do remove {aid}", {(aid, "exists"), (sid, "*")}))
    return out


def touches(reads, writes, desk):
    w = desk.world
    for rid, _rev, aspects in reads:
        ids = {rid} | ({w.nodes[rid].get("subject")} if rid in w.nodes else set()) | set(w.appearances_of(rid) if rid in w.subjects else [])
        for wid, a in writes:
            if wid not in ids:
                continue
            if not aspects or a in ("*", "exists") or a in aspects:
                return True
    return False


def check_world(label, run):
    base = run.desk
    found = {"lenses": 0, "gestures": 0, "trials": 0, "unsound": [], "overread": 0, "touched": 0}
    perts = perturbations(base)
    for name in lenses(base):
        try:
            sc0, _ = scene.scene_for(base, name)
        except Exception:
            continue
        g0 = gestures(sc0)
        if not g0:
            continue
        found["lenses"] += 1
        found["gestures"] += len(g0)
        for pname, cmd, writes in perts:
            r = suite.Run(me="zed")
            r.desk = copy.deepcopy(base)
            r.per = copy.deepcopy(run.per)
            target = cmd.split()[2] if cmd.startswith("do ") else None
            r.line("look")
            if target:
                r.line(f"look {target}")
            _, refused = r.line(cmd)
            if refused:
                continue
            try:
                sc1, _ = scene.scene_for(r.desk, name)
            except Exception:
                sc1 = None
            g1 = gestures(sc1) if sc1 else {}
            for key, g in g0.items():
                found["trials"] += 1
                changed = g1.get(key, {}).get("acts") != g["acts"]
                hit = touches(g["reads"], writes, base)
                found["touched"] += hit
                if hit and not changed:
                    found["overread"] += 1
                if changed and not hit:
                    now = g1.get(key, {}).get("acts")
                    found["unsound"].append({"lens": name, "key": key, "edit": pname, "reads": g["reads"],
                                             "was": g["acts"], "now": now if now is not None else "(gone)"})
    return found


# Juniper 7's default apps as they run today (juniper-7-default-apps-as-lenses.md, "What runs today"), on a small world.
TASKS_LENS = """tasks : column, role sheet
  add : text "Add a task", role card.plain, on edit do create f01 kind=task title="$value" owner=juniper status=open
  late : column, only when kind:task,prop:owner=juniper,-prop:status=done,due<today
    h : text "Overdue", role heading
    list : column, of kind:task,prop:owner=juniper,-prop:status=done,due<today, each task
  now : column
    h : text "Today", role heading
    list : column, of kind:task,prop:owner=juniper,-prop:status=done,-due<today,-due>today, each task
task : row, role card.plain
  box : text "o", role tool, on click do prop $item status=done
  t : text "$title", role title, on edit do retitle $item title="$value"
  d : text "$due", role meta, on edit do due $item on=$value
  w : text "waiting on $next", role tag, only when prop:status=waiting"""
NOTES_LENS = """notes : row, the kind:note,title:Charter as cur
  list : column, role sheet, of kind:note,-tag:lens, each entry
  page : column, role sheet
    t : text "$cur.title", role heading, on edit do retitle $cur.item title="$value"
    secs : column, of sections:$cur.item, each sec
entry : column, role card.plain, on click do prop notes open=$item
  t : text "$title", role title
  first : text "$text", role body, clamp 1
sec : column
  h : text "$heading", role heading
  b : text "$text", role body, on edit do rewrite $item text="$value\""""


def q(text):
    # as the desk's own export quotes a value (desk_knife.cmd_export)
    return '"' + text.replace("\\", "\\\\\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def build_apps():
    run = suite.Run()
    for line in ["look", "clock 2026-09-25",
                 'do create f01 kind=task title="Pay rent" due=2026-09-20; do prop $item owner=juniper status=open',
                 'do create f01 kind=task title="Call Sam" due=2026-09-25; do prop $item owner=juniper status=open',
                 'do create f01 kind=task title="Two more ordinary things"; do prop $item owner=juniper status=waiting next=alex',
                 'do create f01 kind=task title="Buy milk" due=2026-09-25; do prop $item owner=juniper status=done',
                 'do create f01 kind=note title=Charter text="## Aim\\nfirst\\n## Plan\\nsecond"',
                 'do create f01 kind=note title=Ideas text="x"',
                 f"do create f01 kind=note title=tasks tags=lens text={q(TASKS_LENS)}",
                 f"do create f01 kind=note title=notes tags=lens text={q(NOTES_LENS)}"]:
        out, refused = run.line(line)
        if refused:
            print("seed refused:", line[:60], out[:160])
    return run


def main():
    cases = sys.argv[1:] or sorted(p.name for p in (LAB / "suite" / "cases").iterdir() if p.is_dir() and not p.name.startswith("_"))
    report = {}
    worlds = []
    if not sys.argv[1:] or "apps" in sys.argv[1:]:
        worlds.append(("apps/juniper-7", build_apps()))
    for case in [c for c in cases if c != "apps"]:
        for sol in sorted((LAB / "suite" / "cases" / case).glob("*.sol")):
            worlds.append((f"{case}/{sol.stem}", build(case, sol)[0]))
    for label, run in worlds:
        if True:
            f = check_world(label, run)
            report[label] = f
            kinds = {}
            for u in f["unsound"]:
                kinds.setdefault(u["edit"].split()[0], 0)
                kinds[u["edit"].split()[0]] += 1
            print(f"{label}: {f['lenses']} lens(es) with gestures, {f['gestures']} gestures, {f['trials']} trials; "
                  f"UNSOUND {len(f['unsound'])} {kinds or ''}; touched {f['touched']}, of which unchanged (over-read) {f['overread']}")
            seen = set()
            for u in f["unsound"]:
                sig = (u["lens"], u["edit"].split()[0], u["key"].split("/")[0])
                if sig in seen:
                    continue
                seen.add(sig)
                print(f"   - {u['lens']} {u['key']}: after '{u['edit']}' the line went {u['was']} -> {u['now']}; reads {u['reads']}")
    Path(__file__).with_name("soundness.json").write_text(json.dumps(report, indent=1, default=list), encoding="utf-8")


if __name__ == "__main__":
    main()
