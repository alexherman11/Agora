"""Juniper's instruments: run an everyday task's solutions in memory and print, per step, what held.

    python suite/run.py trip              every solution of the trip (cases/trip/*.sol)
    python suite/run.py trip R H2         these solutions
    python suite/run.py trip R --show     also list every wrong statement, where and when
    python suite/run.py trip --bless      write the golden prints (golden/<task>/<solution>.txt)

A case is a folder: task.py holds the person's words, the plan each step leaves, readers and the judge; each
<name>.sol is one way of doing it in the desk (lines marked T target, R repair, A authoring retry, @W window W).
The world lives in memory for the run; sessions/ is never read or written. These are instruments, not gates:
a number that moves is something to look at, not a failure.
"""
import hashlib
import importlib.util
import pathlib
import re
import subprocess
import sys
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
HERE = pathlib.Path(__file__).resolve().parent
LAB = HERE.parent
sys.path.insert(0, str(LAB))
import explore  # noqa: E402  (the lab's fresh desk; nothing is saved)

WRITE = re.compile(r"^(do|rule|undo|script)\b")


# ---------------------------------------------------------------- reading prints

def parse_scene(text):
    """The text printer's scene as a tree of {part, item, text, role, absent, zero, key, kids}."""
    root = {"part": "(scene)", "kids": [], "depth": 0}
    stack = [root]
    for line in text.splitlines()[1:]:
        if not line.strip() or line.lstrip().startswith(("~", "!")):
            continue
        depth = (len(line) - len(line.lstrip(" "))) // 2
        body = line.strip()
        n = {"depth": depth, "kids": [], "line": body}
        m = re.match(r"(\S+)(?: ([asf]\d+))?", body)
        n["part"], n["item"] = m.group(1), m.group(2)
        t = re.search(r'"((?:[^"\\]|\\.)*)"', body)
        n["text"] = t.group(1) if t else None
        r = re.search(r"\[(\w+)\]", body)
        n["role"] = r.group(1) if r else None
        a = re.search(r"\(absent: not ([^)]*)\)", body)
        n["absent"] = a.group(1) if a else None
        n["zero"] = bool(re.search(r"· 0 of ", body))
        k = re.search(r" · key (\S+)$", body)
        n["key"] = k.group(1) if k else None
        while stack[-1]["depth"] >= depth:
            stack.pop()
        stack[-1]["kids"].append(n)
        stack.append(n)
    return root


def parse_table(text):
    """A view's `look <id> :3` table as a list of {column: value}."""
    lines = text.splitlines()
    head = next((i for i, l in enumerate(lines) if l.strip().startswith("id ")), None)
    if head is None:
        return []
    h = lines[head]
    cols = [(m.start(), m.group()) for m in re.finditer(r"\S+", h)]
    rows = []
    for l in lines[head + 1:]:
        if not l.strip():
            break
        row = {}
        for j, (s, name) in enumerate(cols):
            e = cols[j + 1][0] if j + 1 < len(cols) else None
            row[name] = (l[s:e] if e else l[s:]).strip()
        rows.append(row)
    return rows


def normalise(text):
    """A golden print keeps keys and gesture lines and drops what moves with every event: reads, revs, world @N."""
    text = re.sub(r"world @\d+", "world @N", text)
    text = re.sub(r" · read .*?(?= · |$)", "", text, flags=re.M)
    return text


# ---------------------------------------------------------------- the solution file

def load_solution(path):
    sol = {"recorded": {}, "steps": []}
    step = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line.strip() or line.startswith("#"):
            continue
        if line.startswith("recorded "):
            sol["recorded"] = dict(kv.split("=") for kv in line.split()[1:])
        elif line.startswith("step "):
            step = {"name": line.split()[1], "ops": []}
            sol["steps"].append(step)
        elif line == "check":
            step["ops"].append(("check",))
        elif line.startswith("place "):
            _, name, kind, what = line.split(" ", 3)
            step["ops"].append(("place", name, kind, what))
        elif line.startswith("probe "):
            step["ops"].append(("probe", line.split()[1]))
        elif line.startswith("unplace "):
            step["ops"].append(("unplace", line.split()[1]))
        elif line.startswith("fact "):
            _, name, rest = line.split(" ", 2)
            if rest.startswith("n/e"):
                step["ops"].append(("fact", name, None, rest[3:].strip()))
            else:
                cmd, shows = rest.split(" shows ", 1)
                step["ops"].append(("fact", name, cmd.strip(), shows.strip()))
        else:
            m = re.match(r"([TRA])(?:~([\w-]+))?(?:@(\S+))? (.*)$", line)     # T~ben: another person; @B: a window
            if not m:
                raise SystemExit(f"{path.name}: cannot read line: {line}")
            step["ops"].append(("line", m.group(1), m.group(3) or "", m.group(4), m.group(2) or ""))
    return sol


# ---------------------------------------------------------------- running

class Run:
    """One person at a fresh desk, in memory. Each window is its own reader slot, as explore.py --window."""

    def __init__(self, me="juniper"):
        self.desk = explore.fresh()
        self.me = me
        self.per = {}
        self.desk._session = "suite"

    def line(self, text, window=""):
        d, slot = self.desk, self.me + ("/" + window if window else "")
        if slot not in self.per:
            self.per[slot] = ({}, {d.world.root}, len(d.world.events))
        d.seen, d.open, d.last_event_seen = self.per[slot]
        d.world.me, d._window, d._per = self.me, window, self.per
        r = d.dispatch("desk", {"line": text})
        self.per[slot] = (d.seen, d.open, d.last_event_seen)
        out = r.get("text") or ("ERR " + str(r.get("error")))
        refused = bool(r.get("error")) or out.startswith("ERR") or "\nERR" in out
        return out, refused

    def view_id(self, title):
        for i, n in self.desk.world.nodes.items():
            if n.get("type") in ("view", "surface") and (n.get("title") or "").lower() == title.lower():
                return i
        return None

    def read_place(self, kind, what):
        if kind == "scene":
            out, refused = self.line(f"scene {what}")
            return out, refused, (parse_scene(out) if not refused else None)
        vid = self.view_id(what)
        if not vid:
            return f"no view {what}", True, None
        out, refused = self.line(f"look {vid} :3")
        return out, refused, (parse_table(out) if not refused else None)


KINDS = {"silent": "silent", "silent 0-of": "zero", "visible": "visible"}


def run_solution(task, path, show=False):
    sol = load_solution(path)
    run = Run()
    for l in task.SEED:
        run.line(l)
    plan = task.plan()
    places, rows, prints = {}, [], []
    tot = dict(writes=0, repairs=0, silent=0, zero=0, visible=0, ne=0, m4=0, refused=0, left=0)
    standing = set()             # wrongs the last step ended with: one that stands unchanged is counted once, when it appears
    for step in sol["steps"]:
        says, change = task.STEPS[step["name"]]
        if change:
            change(plan)
        seen_wrong = {}          # (place, statement, value) -> verdict: one wrong counted once per step
        refused_lines = []
        st = dict(writes=0, repairs=0, silent=0, zero=0, visible=0, ne=0, m4=0, refused=0, left=0)
        notes = []

        def check(final=False):
            left, now = 0, set()
            for name, (kind, what) in places.items():
                out, refused, parsed = run.read_place(kind, what)
                if final:
                    prints.append(f"== step {step['name']} · {name} ==\n{normalise(out)}")
                if refused:
                    stmts = {("place", name): "!" + out.splitlines()[0][:80]}
                else:
                    stmts = task.read_scene(parsed, plan) if kind == "scene" else task.read_view(parsed, plan)
                for key, value in sorted(stmts.items(), key=str):
                    v = "visible" if key[0] == "place" else task.judge(key, value, plan)
                    if v == "holds":
                        continue
                    left += 1
                    now.add((name, key, str(value)))
                    seen_wrong.setdefault((name, key, str(value)), v)
            return left, now

        for op in step["ops"]:
            if op[0] == "line":
                _, mark, window, text, actor = op
                me = run.me
                run.me = actor or me
                out, refused = run.line(text, window)
                run.me = me
                if WRITE.match(text):
                    st["writes"] += 1
                    st["repairs"] += mark == "R"
                if refused:
                    st["refused"] += 1
                    refused_lines.append(text)
                    notes.append(f"refused{'@' + window if window else ''}: {text[:60]} -> {out.splitlines()[0][:110]}")
            elif op[0] == "check":
                check()
            elif op[0] == "place":
                places[op[1]] = (op[2], op[3])
            elif op[0] == "unplace":
                places.pop(op[1], None)
            elif op[0] == "probe":
                verdict, note = task.probe(op[1], run)
                if verdict == "holds":
                    continue
                if verdict == "n/e":            # the word the fact needs does not exist yet
                    st["ne"] += 1
                    notes.append(f"n/e {op[1]}: {note}")
                    continue
                if op[1] in task.M4_FACTS:
                    st["m4"] += 1
                    notes.append(f"M4 {op[1]}: {note}")
                else:
                    seen_wrong.setdefault(("probe", ("probe", op[1]), note), verdict)
                    notes.append(f"{verdict} {op[1]}: {note}")
            elif op[0] == "fact":
                _, name, cmd, shows = op
                if cmd is None:
                    st["ne"] += 1
                    notes.append(f"n/e {name}: {shows}")
                    continue
                out, refused = run.line(cmd)
                if shows in out and not refused:
                    continue
                if any(shows in line for line in refused_lines):
                    # the words that should survive were never accepted: nothing was lost, but the person could not write
                    seen_wrong.setdefault(("fact", ("fact", name), "never written"), "visible")
                    notes.append(f"visible {name}: the write carrying '{shows}' was itself refused")
                elif name in task.M4_FACTS:
                    st["m4"] += 1
                    notes.append(f"M4 {name}: '{shows}' is gone")
                else:
                    seen_wrong.setdefault(("fact", ("fact", name), "missing"), "silent")
        st["left"], ending = check(final=True)
        for (place, key, value), v in seen_wrong.items():
            if (place, key, value) in standing:
                continue
            st[KINDS[v]] += 1
            if show:
                notes.append(f"{v}: {place} {key[0]} {' '.join(map(str, key[1:]))} says {value}")
        standing = ending
        for k in tot:
            tot[k] += st[k]
        rows.append((step["name"], st, notes))
    if hasattr(task, "audit"):
        found = task.audit(run.desk.world, plan)
        tot["m5"] = (len(found), sum(1 for f in found if not f[2]))
        rows.append(("M5", None, [f"{'agrees' if ok else 'DISAGREES'}: {where} = {what}" for where, what, ok in found]))
    return sol, rows, tot, "\n\n".join(prints) + "\n"


def identity():
    h = lambda f: hashlib.sha256((LAB / f).read_bytes()).hexdigest()[:12]
    try:
        git = lambda *a: subprocess.run(["git", "-C", str(LAB), *a], capture_output=True, text=True).stdout.strip()
        head = git("rev-parse", "--short", "HEAD")
        dirty = git("status", "--porcelain", "--", "scene.py", "knife.py", "desk_knife.py", "world.py", "moo.py", "desk_moo.py")
    except OSError:
        head, dirty = "?", ""
    return f"head {head}{' + uncommitted lab source' if dirty else ''} · scene.py {h('scene.py')} · world.py {h('world.py')}"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    show, bless = "--show" in sys.argv, "--bless" in sys.argv
    if not args:
        raise SystemExit(__doc__)
    case = HERE / "cases" / args[0]
    spec = importlib.util.spec_from_file_location(f"case_{args[0]}", case / "task.py")
    task = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(task)
    names = args[1:] or sorted(p.stem for p in case.glob("*.sol"))
    print(f"{args[0]} · {identity()}")
    for name in names:
        sol, rows, tot, prints = run_solution(task, case / f"{name}.sol", show)
        print(f"\n{args[0]} / {name}")
        cols = ("writes", "repairs", "silent", "zero", "visible", "ne", "m4", "refused", "left")
        print("  step  " + " ".join(f"{c.replace('zero', '0-of').replace('ne', 'n/e').replace('m4', 'M4'):>7}" for c in cols))
        for sname, st, notes in rows:
            if st is None:
                a, b = tot["m5"]
                print(f"  M5    stated-date statements stored at the end: {a}, disagreeing: {b}")
                for n in notes if show else []:
                    print(f"          {n}")
                continue
            print(f"  {sname:<5} " + " ".join(f"{st[c]:>7}" for c in cols))
            for n in notes:
                print(f"          {n}")
        print("  all   " + " ".join(f"{tot[c]:>7}" for c in cols))
        m1 = sum(st["writes"] for sname, st, _ in rows if sname in getattr(task, "M1_STEPS", {sname}))
        now = {"M1": m1, "M2": tot["repairs"], "M3": tot["silent"] + tot["zero"] + tot["visible"], "M4": tot["m4"], "M5": (tot.get("m5") or ("-",))[0]}
        rec = sol["recorded"]
        diff = [f"{k} {rec[k]} then, {now[k]} now" for k in rec if str(now.get(k)) != rec[k]]
        print("  against the recorded run: " + ("same" if not diff else "; ".join(diff)))
        gold = HERE / "golden" / args[0] / f"{name}.txt"
        if bless:
            gold.parent.mkdir(parents=True, exist_ok=True)
            gold.write_text(prints, encoding="utf-8", newline="\n")
            print(f"  golden prints written: golden/{args[0]}/{name}.txt")
        elif gold.exists():
            old, new = gold.read_text(encoding="utf-8").splitlines(), prints.splitlines()
            changed = [(i, a, b) for i, (a, b) in enumerate(zip(old, new)) if a != b]
            extra = abs(len(old) - len(new))
            if not changed and not extra:
                print("  golden prints: same")
            else:
                print(f"  golden prints: {len(changed)} line(s) differ, {extra} added or dropped")
                for i, a, b in changed[:4]:
                    print(f"    line {i + 1}\n      was {a.strip()}\n      now {b.strip()}")


if __name__ == "__main__":
    main()
