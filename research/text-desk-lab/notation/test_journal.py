"""Baseline: real-life scenarios against today's desk, seen from "the log as the truth" (Sable's direction).

    python test_journal.py            print each scenario: the story, what the desk did, what a journal of
                                      attributed per-(thing, aspect) operations would do instead
    python test_journal.py --json F   also write the results as JSON

An instrument, not a gate: it always exits 0. Each scenario says `holds` (the desk already does what the journal
model wants), `breaks` (it does something else) or `hidden` (a fact the pickle keeps and no record carries).
The J scenarios run the same moments against journal.py, the prototype; their status is `journal`.
Everything runs on in-memory desks or in a temporary directory: no shared session is read or written.
"""

import copy
import json
import os
import pickle
import re
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

import explore      # noqa: E402
import worktree     # noqa: E402
import deskd        # noqa: E402

RESULTS = []
SCRATCH = []


def scratch(name):
    d = tempfile.mkdtemp(prefix=f"sable-{name}-")
    SCRATCH.append(d)
    return d


def scenario(code, title):
    def wrap(fn):
        fn.code, fn.title = code, title
        return fn
    return wrap


def report(code, title, status, story, observed, journal):
    RESULTS.append({"code": code, "title": title, "status": status, "story": story, "observed": observed, "journal": journal})
    print(f"{code}  {title}   [{status}]")
    print("  story:    " + story)
    for o in ([observed] if isinstance(observed, str) else observed):
        print("  observed: " + o)
    print("  journal:  " + journal)
    print()


class Desk:
    """One in-memory desk with several readers. A slot is a person, or person/window, as explore.py keys them."""

    def __init__(self, d=None):
        self.d = d or explore.fresh()
        self.slots, self.cur = {}, None

    @property
    def w(self):
        return self.d.world

    def as_(self, slot):
        d = self.d
        if self.cur:
            self.slots[self.cur] = (d.seen, d.open, d.last_event_seen)
        if slot not in self.slots:
            self.slots[slot] = ({}, {d.world.root}, len(d.world.events))
        d.seen, d.open, d.last_event_seen = self.slots[slot]
        me, _, win = slot.partition("/")
        d.world.me, d._window, self.cur = me, win, slot

    def do(self, line, slot="alex"):
        self.as_(slot)
        r = self.d.dispatch("desk", {"line": line})
        return r.get("text") or ("ERR " + str(r.get("error")))


def refused(text):
    return text.startswith("ERR") or "\nERR" in text or text.startswith("refused")


def made(text):
    m = re.search(r"created (a\d+)", text)
    return m.group(1) if m else None


def first(text):
    return text.strip().splitlines()[0] if text.strip() else ""


def verdict(text):
    """The line that says what happened (ok or ERR), past any `!! since your last look` header."""
    lines = [l.strip() for l in text.strip().splitlines()]
    hit = next((l for l in lines if l.startswith(("ok ", "ERR", "refused"))), first(text))
    head = next((l for l in lines if l.startswith(("!!", "ERR !!"))), None)
    if hit.startswith("ERR !!"):         # a refusal printed under the delta header: the reason is the next line
        head = hit[4:]
        hit = "ERR " + next((l for l in lines[lines.index(hit) + 1:] if l), "")
    return hit + (f"   (after the header: {head})" if head and head not in hit else "")


def subj(dk, aid):
    return dk.w.subjects[dk.w.nodes[aid]["subject"]]


def fingerprint(d):
    """The desk without ids: what a faithful rebuild must reproduce (explore --shape, plus comments, rules, clock)."""
    w, out = d.world, []

    def walk(fid, depth):
        for k in w.children(fid):
            if k["type"] == "surface":
                out.append("  " * depth + f"surface {k['title']!r} {k['layout']} props={sorted((k.get('props') or {}).items())}")
                walk(k["id"], depth + 1)
            else:
                s = w.subjects[k["subject"]]
                out.append("  " * depth + f"{s['kind']} {s['title']!r} tags={s['tags']} due={s.get('due')} text={s['text']!r} "
                           f"props={sorted((s.get('props') or {}).items())} comments={[(c['by'], c['text'], c['resolved']) for c in s['comments']]}")
    walk(w.root, 0)
    out += sorted(f"link {w.subjects[l['from']]['title']!r} -> {w.subjects[l['to']]['title']!r} {l['kind']}" for l in w.links)
    out += [f"rule {r['sel']} {r['verb']} {r.get('kv')}" for r in d.rules or []]
    out += [f"script {k} = {v}" for k, v in sorted((d.scripts or {}).items())]
    out.append(f"clock {d.today}")
    return out


def diff(a, b):
    return [f"- {x}" for x in a if x not in b] + [f"+ {x}" for x in b if x not in a]


# ---------------------------------------------------------------------------------------------------------------
def build_home():
    """A small ordinary desk: a note, a task, a link, a rule, a script, a clock, an agent's write, an undo."""
    dk, lines = Desk(), []

    def run(line, slot="alex"):
        lines.append((slot, line))
        return dk.do(line, slot)
    run("look")
    run("clock 2026-09-25")
    note = made(run('do create f01 kind=note title=Groceries text="milk\\neggs"'))
    task = made(run("do create f01 kind=task title=\"Call dentist\""))
    run(f"do prop {task} status=open")
    run(f'do append {note} line="bread"')
    run(f"do link {note} to={task} kind=about")
    run("rule when prop:status=done do tag add=done")
    run("script morning = look")
    run(f'do append {note} line="oops"')
    run("undo")
    run("look", "jeff")
    run(f"do prop {task} status=done", "jeff")
    return dk, lines, note, task


@scenario("S1", "rebuild the desk from what was recorded")
def s1():
    dk, lines, note, task = build_home()
    want = fingerprint(dk.d)
    # (a) export: the desk's own rebuild script
    exp = dk.do("export")
    e = Desk()
    bad = [l for l in exp.splitlines() if l.strip() and not l.startswith(("#", "!!")) and refused(e.do(l))]
    da = diff(want, fingerprint(e.d))
    # (b) the command lines, replayed in order by the same readers (what worktree journals)
    c = Desk()
    for slot, l in lines:
        c.do(l, slot)
    db = diff(want, fingerprint(c.d))
    same_ids = sorted(c.w.nodes) == sorted(dk.w.nodes) and sorted(c.w.subjects) == sorted(dk.w.subjects)
    # (c) the events alone: rerun each event's verb on an empty world (the only way today, since events carry no values)
    import moo
    r = explore.fresh()
    fails = []
    for ev in dk.w.events:
        r.world.me = ev["by"]
        try:
            if ev["verb"] == "undo":
                r.world.undo(ev["target"])
            else:
                try:
                    r.world.apply(ev["verb"], ev["target"], None, dict(ev.get("args") or {}), ev["by"])
                except Exception:
                    moo.REGISTRY[ev["verb"]].run(r.world, ev["target"], dict(ev.get("args") or {}))
        except Exception as x:
            fails.append(f"{ev['id']} {ev['verb']}: {str(x)[:60]}")
    dc = diff(want, fingerprint(r))
    after = sum(1 for ev in dk.w.events if "after" in ev)
    report("S1", s1.title, "breaks",
           "Alex keeps groceries and a dentist task; a rule tags done tasks; the agent marks the task done; one append is undone. "
           "Can the desk be rebuilt from anything but the pickle?",
           [f"export replayed: {len(bad)} line(s) refused, {len(da)} fingerprint line(s) differ" + (": " + "; ".join(da[:4]) if da else ""),
            f"command lines replayed: {len(db)} line(s) differ, same ids: {same_ids}" + (": " + "; ".join(db[:3]) if db else ""),
            f"events rerun as verbs: {len(fails)} failed" + (" (" + "; ".join(fails[:3]) + ")" if fails else "") + f", {len(dc)} line(s) differ"
            + (": " + "; ".join(dc[:4]) if dc else ""),
            f"events carrying an after-value: {after} of {len(dk.w.events)}; rules, scripts and clock made "
            f"{sum(1 for ev in dk.w.events if ev['verb'] in ('rule', 'script', 'clock'))} events",
            "the rule's tag is signed: " + "; ".join(f"{ev['id']} {ev['verb']} by {ev['by']} via {ev.get('via')!r}" for ev in dk.w.events if ev.get("cause"))
            + " (the rule is alex's; jeff only set a status)"],
           "every batch carries its ops' before and after; replay assigns values and runs nothing, so the three routes collapse into one "
           "and definitions (rule, script, clock) are rows like any other")


CRASHY = '''import os, sys
from pathlib import Path
sys.path.insert(0, HERE)
import explore
explore.SESSIONS = Path(TMP)
K = int(os.environ["CRASH_AFTER"]); real = sys.stdout
class Tap:
    n = 0
    def write(self, s):
        real.write(s)
        Tap.n += sum(1 for l in s.splitlines() if l.startswith("ok "))
        if Tap.n >= K:
            real.flush(); os._exit(9)      # the process dies here: no finally, no atexit
        return len(s)
    def flush(self): real.flush()
sys.stdout = Tap()
sys.argv = ["explore.py", "scratch", "--as", "alex"]
explore.main()
'''


@scenario("S2", "a crash after the desk said ok")
def s2():
    tmp = Path(scratch("crash"))
    wrapper = tmp / "crashy.py"
    wrapper.write_text(f"HERE = {str(HERE)!r}\nTMP = {str(tmp)!r}\n" + CRASHY, encoding="utf-8")

    def go(lines, k):
        env = dict(os.environ, CRASH_AFTER=str(k), DESKD="off", PYTHONWARNINGS="ignore")
        p = subprocess.run([sys.executable, str(wrapper)], input="\n".join(lines) + "\n", capture_output=True, text=True, env=env, timeout=120)
        return p.returncode, sum(1 for l in p.stdout.splitlines() if l.startswith("ok "))

    pk, lock = tmp / "scratch.pickle", tmp / "scratch.lock"
    code1, acked1 = go(["look"] + [f"do create f01 kind=note title=N{i}" for i in range(4)], 2)
    kept1 = len(pickle.loads(pk.read_bytes()).world.subjects) if pk.exists() else 0
    lock_left = lock.exists()
    lock.unlink(missing_ok=True)
    go(["look", "do create f01 kind=note title=Kept"], 999)
    code3, acked3 = go(["look"] + [f"do create f01 kind=task title=T{i}" for i in range(3)], 2)
    kept3 = pickle.loads(pk.read_bytes()).world.subjects
    lock.unlink(missing_ok=True)
    # a torn save: deskd and explore write the pickle in place (write_bytes truncates, then writes); cut it half way
    whole = pk.read_bytes()
    pk.write_bytes(whole[: len(whole) // 2])
    try:
        pickle.loads(pk.read_bytes())
        torn = "the half file still loaded"
    except Exception as x:
        torn = f"the half-written pickle does not load ({type(x).__name__}): the whole session is gone, not just the last turn"
    inplace = [f for f in ("explore.py", "deskd.py") if "os.replace" not in (HERE / f).read_text(encoding="utf-8")]
    report("S2", s2.title, "breaks",
           "Alex types five lines into the CLI; the process dies after the desk printed ok twice. Then a session with work "
           "in it, the same crash. Then the save itself is cut short.",
           [f"run 1: exit {code1}, {acked1} ok printed, {kept1} thing(s) on disk afterwards (the CLI writes the pickle once, at the end)",
            f"the lock was {'left behind: the next CLI run on that session waits up to 60 s for it' if lock_left else 'removed'}",
            f"run 3: exit {code3}, {acked3} ok printed, the disk still holds only {sorted(s['title'] for s in kept3.values())}",
            torn + f"; no temp-file-and-rename in {', '.join(inplace) or 'none'}"],
           "a batch is one appended line, fsynced before the receipt prints (measured 0.86 ms median); an incomplete last line "
           "is an unacknowledged batch and is dropped, everything before it stands; the pickle becomes a cache stamped with an offset")


@scenario("S3", "a long-lived fork comes home")
def s3():
    tmp = Path(scratch("fork"))
    worktree.SESSIONS = tmp
    base = Desk()
    base.do("look")
    plan = made(base.do('do create f01 kind=note title="Trip plan" text="day 1"'))
    budget = made(base.do("do create f01 kind=note title=Budget"))
    text, base.d = worktree.handle("worktree fork trip", "base", base.d, "alex")
    fork = Desk(pickle.loads((tmp / "base@trip.pickle").read_bytes()))

    def fdo(line):
        before, n0 = worktree.ids_of(fork.d), len(fork.w.events)
        out = fork.do(line)
        worktree.record(fork.d, line, "alex", before, n0)
        return out

    def save():
        (tmp / "base@trip.pickle").write_bytes(pickle.dumps(fork.d))

    def reload():
        # a merge writes the fork's pickle (its merged_n); the next use of the fork loads it again, as a CLI run does
        fork.d = pickle.loads((tmp / "base@trip.pickle").read_bytes())
        fork.slots, fork.cur = {}, None
    fdo("look")
    hotels = made(fdo("do create f01 kind=note title=Hotels"))
    fdo(f"look {plan}")
    fdo(f"look {budget}")
    fdo(f'do append {plan} line="day 2: see {hotels} for where we sleep"')
    fdo(f"do prop {budget} currency=EUR")
    fdo(f'do retitle {plan} title="Lisbon trip"')
    save()
    # meanwhile, at home, the agent works the same desk
    base.do("look", "jeff")
    flights = made(base.do("do create f01 kind=note title=Flights", "jeff"))
    base.do(f"look {plan}", "jeff")
    base.do(f"look {budget}", "jeff")
    base.do(f"do prop {budget} total=900", "jeff")
    base.do(f'do retitle {plan} title="Trip plan (Lisbon)"', "jeff")
    base.as_("alex")
    m1, base.d = worktree.handle("worktree merge trip", "base", base.d, "alex")
    reload()
    applied1 = sum(1 for e in base.w.events if e.get("merged"))
    # Alex gives up his title in the fork and merges again
    fdo("undo")
    save()
    m2, base.d = worktree.handle("worktree merge trip", "base", base.d, "alex")
    reload()
    hotels_here = next((n for n, x in base.w.nodes.items() if x.get("subject") and base.w.subjects[x["subject"]]["title"] == "Hotels"), None)
    plan_text = subj(base, plan)["text"]
    # the fork keeps living: one more line in Hotels, merged again
    fdo(f"look {hotels}")
    fdo(f'do append {hotels} line="Alfama, two nights"')
    save()
    m3, base.d = worktree.handle("worktree merge trip", "base", base.d, "alex")
    hotels_text = base.w.subjects[base.w.nodes[hotels_here]["subject"]]["text"] if hotels_here else None
    renamed = [l.strip() for l in m2.splitlines() if "renamed" in l]
    report("S3", s3.title, "breaks",
           "Alex forks the desk to plan a trip: a new note, a line in the plan, a currency on the budget, a new title. At home the "
           "agent adds Flights (the id Hotels has in the fork), sets the budget total and retitles the plan too.",
           [f"merge 1: {first(m1)} / {' '.join(m1.splitlines()[1:3]).strip()}; {applied1} event(s) applied, so the clean changes waited on the one conflict",
            f"merge 2 (after undo in the fork): {first(m2)}; {renamed[0] if renamed else 'no ids renamed'}",
            f"Hotels is {hotels} there and {hotels_here} here; Flights took {flights}; the plan's text now reads {plan_text!r}",
            f"merge 3: {first(m3)}; Hotels here reads {hotels_text!r}",
            f"budget props here: {sorted((subj(base, budget).get('props') or {}).items())} (prop:currency and prop:total are different aspects)",
            "read, not run: merge rewrites the fork's pickle (merged_n, mapping) without taking the fork's lock, and deskd is a ThreadingHTTPServer; "
            "a fork turn that loaded before a merge and saves after it drops merged_n, and the next merge replays merged commands"],
           "merge by ops: each (thing, aspect) op is clean, agreed or held; clean ones land now, a held title waits for take/keep/set; "
           "ids are global (time + random) with a short alias per world, printed '(a07 there, a09 here)', so prose and journal never need rewriting")


@scenario("S4", "one person, two windows")
def s4():
    dk = Desk()
    dk.do("look", "alex/laptop")
    g = made(dk.do('do create f01 kind=note title=Groceries text="milk"', "alex/laptop"))
    dk.do(f"look {g}", "alex/laptop")
    dk.do("look", "alex/phone")
    dk.do(f"look {g}", "alex/phone")
    p = dk.do(f'do retitle {g} title="Groceries (Sat)"', "alex/phone")
    l1 = dk.do(f"do retitle {g} title=Shopping", "alex/laptop")
    l2 = dk.do(f'do append {g} line="bread"', "alex/laptop")
    kept = "Shopping" in json.dumps(dk.w.events) + json.dumps(dk.w.subjects)
    ok = refused(l1) and not refused(l2)
    report("S4", s4.title, "holds" if ok and kept else ("breaks" if not ok else "half"),
           "Alex has the desk open on the laptop and the phone. The phone retitles the grocery list; the laptop, still showing "
           "the old title, retitles it too, then adds a line.",
           [f"phone: {verdict(p)}", f"laptop title: {verdict(l1)}", f"laptop append: {verdict(l2)}",
            f"the refused title 'Shopping' is {'kept' if kept else 'nowhere'} in the world or its events"],
           "the fence refuses on the same aspect and admits the other, as it should; the journal adds a refusal line (proposed rows, "
           "reads, why, who) so the laptop's 'Shopping' is recoverable instead of living only in a printed message")


@scenario("S5", "undo meets somebody else's unrelated change")
def s5():
    dk = Desk()
    dk.do("look")
    n = made(dk.do('do create f01 kind=note title=Essay text="first line"'))
    dk.do(f"look {n}")
    dk.do(f"do prop {n} color=green")
    ev_prop = dk.w.events[-1]["id"]
    dk.do(f'do retitle {n} title="Essay draft"')
    ev_title = dk.w.events[-1]["id"]
    dk.do("look", "jeff")
    dk.do(f"look {n}", "jeff")
    ag = dk.do(f'do append {n} line="agent: two sources found"', "jeff")
    u1 = dk.do(f"undo {ev_prop}")
    u2 = dk.do(f"undo {ev_title}")
    u3 = dk.do("undo")
    report("S5", s5.title, "breaks" if refused(u1) or refused(u2) else "holds",
           "Alex colours his essay green and renames it; the background agent appends a line to its text; Alex takes back the colour, then the name.",
           [f"agent: {verdict(ag)}", f"undo colour: {verdict(u1)}", f"undo name: {verdict(u2)}", f"bare undo: {verdict(u3)}"],
           "undo is an inverse op per (thing, aspect), allowed while that aspect still holds the op's after; the agent's text line "
           "does not stand in the way of props or title")


@scenario("S6", "definitions are not in the history")
def s6():
    tmp = Path(scratch("defs"))
    worktree.SESSIONS = tmp
    dk = Desk()
    dk.do("look")
    made(dk.do("do create f01 kind=note title=Inbox"))
    n0 = len(dk.w.events)
    dk.do("rule when tag:urgent do move into=f01")
    dk.do("script morning = look")
    dk.do("clock 2026-09-25")
    n1 = len(dk.w.events)
    u = dk.do("undo")
    still = "Inbox" in [s["title"] for s in dk.w.subjects.values()]
    # a definition edited on both sides of a fork
    _, dk.d = worktree.handle("worktree fork defs", "base", dk.d, "alex")
    fork = Desk(pickle.loads((tmp / "base@defs.pickle").read_bytes()))
    fork.do("look")
    line = "script morning = find tag:urgent"
    before, k = worktree.ids_of(fork.d), len(fork.w.events)
    fork.do(line)
    worktree.record(fork.d, line, "alex", before, k)
    (tmp / "base@defs.pickle").write_bytes(pickle.dumps(fork.d))
    home = dk.do("script morning = look Inbox", "jeff")
    m, dk.d = worktree.handle("worktree merge defs", "base", dk.d, "alex")
    report("S6", s6.title, "breaks",
           "Alex writes a rule, a morning script and sets the clock, then says undo. Later he edits the morning script in a fork "
           "while the agent edits the same script at home.",
           [f"rule + script + clock made {n1 - n0} event(s)", f"undo after them: {first(u)} (Inbox {'survives' if still else 'was taken back instead'})",
            f"agent at home: {first(home)}",
            f"merge: {first(m)}; the script is now {(dk.d.scripts or {}).get('morning')!r}; the agent's version is gone and nothing said so"],
           "a definition is a referent with a code aspect: defining it is an op (undoable, attributed, fenced), and the two script "
           "edits are one held conflict on (morning, code)")


@scenario("S7", "what the pickle keeps that no record carries")
def s7():
    dk, lines, note, task = build_home()
    d = dk.d
    quiet = ["look", f"look {note}", "rule when tag:x do tag add=y", "script evening = look", "clock 2026-09-26", f"set g = {note}"]
    changed = {}
    for line in quiet:
        dk.as_("alex")
        before = {k: pickle.dumps(v) for k, v in vars(d).items() if k != "world"}
        wb = {k: pickle.dumps(v) for k, v in vars(d.world).items() if k != "me"}
        n = len(d.world.events)
        out = dk.do(line)
        if len(d.world.events) == n:
            ks = [k for k, v in vars(d).items() if k != "world" and pickle.dumps(v) != before.get(k)]
            ks += ["world." + k for k, v in vars(d.world).items() if k != "me" and pickle.dumps(v) != wb.get(k)]
            changed[line.split()[0]] = sorted(set(ks))
        else:
            changed[line.split()[0]] = [f"(made {len(d.world.events) - n} event(s): {first(out)})"]
    # history is edited in place: undo marks the old event
    dk.do(f'do append {note} line="x"')
    old = copy.deepcopy(d.world.events)
    dk.do("undo")
    edited = [e["id"] for e, o in zip(d.world.events, old) if e != o]
    report("S7", s7.title, "hidden",
           "The same home desk. Which parts of the saved state change with no event at all, and does history stay as written?",
           [f"{k}: {', '.join(v) or 'nothing'}" for k, v in changed.items()]
           + [f"undo rewrote old event(s) {edited} in place (the `undone` flag); merge does the same with `merged`"],
           "world facts and definitions are journal rows; per-viewer state (seen, open, windows, handles) is named viewer state "
           "on Pike's side, never mixed into one blob; the journal is append-only, and undone-ness is derived from later lines")


@scenario("S8", "Alex writes while a background task writes")
def s8():
    dk = Desk()
    dk.do("look", "alex/main")
    doc = made(dk.do('do create f01 kind=note title=Essay text="## Intro\\nold intro\\n## Notes\\n- first"', "alex/main"))
    task = made(dk.do("do create f01 kind=task title=Research", "alex/main"))
    dk.do(f"look {doc}", "alex/main")
    dk.do(f"look {task}", "alex/main")
    dk.do("look", "jeff")
    dk.do(f"look {doc}", "jeff")
    dk.do(f"look {task}", "jeff")
    ag = [dk.do(f'do append {doc} line="- agent: source {i + 1}"', "jeff") for i in range(3)]
    dk.do(f"do prop {task} status=running", "jeff")
    t = dk.do(f'do retitle {task} title="Research sources"', "alex/main")
    r = dk.do(f'do rewrite {doc} section=Intro text="A new intro, typed while the agent worked."', "alex/main")
    kept = "typed while the agent worked" in json.dumps(dk.w.subjects) + json.dumps(dk.w.events)
    dk.do(f"look {doc}", "alex/main")
    r2 = dk.do(f'do rewrite {doc} section=Intro text="A new intro, typed while the agent worked."', "alex/main")
    a = dk.do(f'do append {doc} line="- agent: source 4"', "jeff")
    report("S8", s8.title, "breaks" if refused(r) else "holds",
           "Alex's four-region workspace: he retitles his task and rewrites the essay's Intro while a background agent appends "
           "sources under Notes and marks the task running.",
           [f"agent appends: {sum(1 for x in ag if not refused(x))} of 3 landed",
            f"task title (agent wrote status): {verdict(t)}", f"Intro rewrite (agent appended under Notes): {verdict(r)}",
            f"Alex's typed paragraph is {'kept' if kept else 'nowhere'} after that",
            f"after looking again, the rewrite: {verdict(r2)}", f"then the agent's next append: {verdict(a)}"],
           "text is one aspect today; with anchored hunks (the qc experiment: 42 intact, 0 silent drifts) an Intro rewrite and a Notes "
           "append touch different anchors and both land; where they do meet, the refusal line keeps the paragraph")


@scenario("S9", "one call, two commands, half applied")
def s9():
    dk = Desk()
    dk.do("look")
    n = made(dk.do("do create f01 kind=note title=Inbox"))
    dk.do(f"look {n}")
    k = len(dk.w.events)
    out = dk.do(f"do prop {n} filed=yes; do retitle a99 title=Filed")
    added = len(dk.w.events) - k
    shown = re.findall(r"^ok .*\[(e\d+)\]", out, re.M)
    other = made(dk.do("do create f01 kind=note title=Other"))
    later = dk.w.events[-1]["id"]
    u = dk.do(f"undo {shown[0]}") if shown else ""
    reused = bool(shown) and later == shown[0]
    report("S9", s9.title, "breaks" if added else ("half" if reused else "holds"),
           "Alex files a note in one call: set a prop, then retitle (he mistypes the id). Then he makes another note, "
           "and later undoes the event number the first receipt showed him.",
           [" / ".join(l.strip() for l in out.splitlines() if l.strip())[:220],
            f"events added: {added}; props now {subj(dk, n).get('props')}",
            f"the rolled-back receipt said {shown[0] if shown else '-'}; the next note ({other}) became {later}; undo {shown[0] if shown else '-'}: {verdict(u)}"],
           "a call is one batch: all rows commit in one appended line or none do (Jeff's step 1b, begin/apply/commit)")


@scenario("S10", "an undo is a change, but the fences do not see it")
def s10():
    dk = Desk()
    dk.do("look")
    n = made(dk.do('do create f01 kind=note title=Call text="call Sam at 5"'))
    sid = dk.w.nodes[n]["subject"]
    dk.do("look", "wren")
    dk.do(f"look {n}", "wren")
    dk.do(f'do rewrite {n} text="call Sam at 3"', "wren")
    ev = dk.w.events[-1]["id"]
    dk.do(f"look {n}", "alex")
    seen = dk.w.subjects[sid]["rev"]
    u = dk.do(f"undo {ev}", "wren")
    now = dk.w.subjects[sid]["rev"]
    ta = deskd.touched_aspects(dk.w, sid, seen, now, ["text"])
    r = dk.do(f'do rewrite {n} text="call Sam at 3, bring the forms"', "alex")
    report("S10", s10.title, "breaks" if not refused(r) or not ta else "holds",
           "Wren changes the call to 3; Alex reads it; Wren takes it back (5 again). Alex adds 'bring the forms' to what he read.",
           [f"wren's undo: {first(u)}", f"deskd.touched_aspects(text, rev {seen} -> {now}) = {ta} (False = a painted gesture is accepted)",
            f"Alex's rewrite: {verdict(r)}; the text is now {subj(dk, n)['text']!r}, so Wren's undo is silently reversed"],
           "an undo is a batch of inverse ops on (thing, aspect) rows; any read of that aspect before it is stale, exactly")


@scenario("S11", "who did it: another actor's write from the CLI")
def s11():
    import moo
    dk = Desk()
    dk.do("look")
    w = dk.w
    w.me = "jeff"
    # explore.py's `!priya verb target k=v` line: registry verbs get the actor as _by, as main() does
    r = moo.REGISTRY["create"].run(w, "f01", {"kind": "task", "title": "Book flights", "_by": "priya"})
    a = r["created"]
    moo.REGISTRY["prop"].run(w, a, {"status": "open", "_by": "priya"})
    moo.REGISTRY["tag"].run(w, a, {"add": "travel", "_by": "priya"})
    s = subj(dk, a)
    signed = [(e["verb"], e["by"]) for e in w.events]
    ok = all(b == "priya" for _, b in signed) and "_by" not in (s.get("props") or {})
    report("S11", s11.title, "holds" if ok else "breaks",
           "Priya, from a terminal, creates a task, sets its status and tags it (explore.py's `!priya ...` line), while jeff owns the desk.",
           [f"events signed: {signed}", f"the task's props: {s.get('props')}"],
           "the actor is a field of the batch, set once by the gateway from the caller, never an argument a verb may drop or store")


# ---------------------------------------------------------------------------------------------------------------
# The same moments against journal.py, the prototype (not wired into the desk). Status `journal` = what it did.

def jnew(name):
    import journal
    return journal.Journal(Path(scratch("j")) / f"{name}.jsonl", fsync=True)


def thing(j, actor, kind, title, text="", parent="root"):
    import journal
    g = journal.gid()
    j.commit(actor, actor, f"create {kind} {title}", [(g, "kind", kind), (g, "title", title), (g, "text", text), (g, "place", [parent, 0])])
    return g


@scenario("J2", "prototype: a crash in the middle of a line")
def j2():
    import journal
    j = jnew("crash")
    for i in range(3):
        thing(j, "alex", "note", f"N{i}")
    with open(j.path, "ab") as f:
        f.write(b'{"v":1,"seq":4,"actor":"alex","ops":[{"target":["x","title"],"bef')   # the process died here
    k = journal.Journal(j.path)
    stood = k.head
    seq = thing(k, "alex", "note", "after the crash") and k.head
    lines = j.path.read_text(encoding="utf-8").splitlines()
    ok = k.torn > 0 and seq == 4 and all(json.loads(line) for line in lines)
    report("J2", j2.title, "journal" if ok else "error",
           "Three notes acknowledged, then the process dies while writing the fourth line.",
           [f"reopened: {stood} batches stand, {k.torn} torn byte(s) dropped; the next batch is seq {seq}; every line parses: {ok}"],
           "as designed: acknowledged means on disk; only the unacknowledged tail is lost")


@scenario("J3", "prototype: the long fork, merged by ops")
def j3():
    import journal
    base = jnew("base")
    names = journal.Aliases()
    plan = thing(base, "alex", "note", "Trip plan", "day 1")
    budget = thing(base, "alex", "note", "Budget")
    names.mint("a", plan), names.mint("a", budget)
    fork, F = journal.fork(base, base.path.with_name("base@trip.jsonl"))
    fnames = names.fork()
    hotels = thing(fork, "alex", "note", "Hotels")
    h_there = fnames.mint("a", hotels)
    fork.commit("alex", "alex", "append plan", [(plan, "text", f"day 1\nday 2: see {h_there}")], reads=[[plan, ["text"], F]])
    fork.commit("alex", "alex", "prop budget currency", [(budget, "prop:currency", "EUR")])
    fork.commit("alex", "alex", "retitle plan", [(plan, "title", "Lisbon trip")])
    flights = thing(base, "jeff", "note", "Flights")
    f_here = names.mint("a", flights)
    base.commit("jeff", "jeff", "prop budget total", [(budget, "prop:total", "900")])
    base.commit("jeff", "jeff", "retitle plan", [(plan, "title", "Trip plan (Lisbon)")])
    m1 = journal.merge(base, fork, F, "trip", "alex")
    h_here = names.adopt(hotels, h_there)
    title_held = [h for h in m1["held"] if h["target"][1] == "title"]
    journal.resolve(base, title_held[0], "keep", "alex") if title_held else None
    fork.commit("alex", "alex", "append hotels", [(hotels, "text", "Alfama, two nights")])
    m2 = journal.merge(base, fork, F, "trip", "alex")
    # an import from outside the family collides on a short id; the guard refuses a write by the old alias
    other = journal.Aliases()
    stranger = journal.gid()
    other.mint("a", journal.gid()), other.mint("a", journal.gid()), other.mint("a", stranger)
    memory = {"a03": other.resolve("a03")}          # alex read a03 over there: his viewer store remembers the gid
    moved = names.adopt(stranger, "a03")
    try:
        names.resolve("a03", memory["a03"])
        guard = "a03 resolved (wrong)"
    except journal.Refusal as e:
        guard = f"refused: {e.why}"
    report("J3", j3.title, "journal",
           "The same trip fork: Hotels, a line in the plan, a currency, a title; at home Flights, a total and another title.",
           [f"merge 1: {m1['clean']} clean landed at seq {m1['seq']}, {m1['agreed']} agreed, {len(m1['held'])} held: "
            + "; ".join(f"{h['target'][1]} here {h['here']!r} ({h['by_here']}) vs there {h['there']!r} ({h['by_there']})" for h in m1["held"]),
            f"Hotels is {h_there} there and {h_here} here (the fork's block); Flights is {f_here}; the plan reads {base.value(plan, 'text')!r}",
            f"budget: currency={base.value(budget, 'prop:currency')} total={base.value(budget, 'prop:total')}; title kept as {base.value(plan, 'title')!r}",
            f"merge 2: {m2['clean']} clean (only the new line; nothing replayed), Hotels reads {base.value(hotels, 'text')!r}",
            f"a thing imported from another world was a03 there; here a03 is Flights, so it arrives as {moved}; alex, who read a03 there, types a03 here: {guard}"],
           "as designed; one thing to argue: the family block makes fork ids four digits (a1000), which is honest but longer")


@scenario("J5", "prototype: undo per aspect")
def j5():
    j = jnew("undo")
    n = thing(j, "alex", "note", "Essay", "first line")
    s_col = j.commit("alex", "alex", "prop color", [(n, "prop:color", "green")])
    s_tit = j.commit("alex", "alex", "retitle", [(n, "title", "Essay draft")])
    j.commit("jeff", "jeff", "append", [(n, "text", "first line\nagent: two sources found")])
    out = []
    for s in (s_col, s_tit):
        try:
            seq, notes = j.undo(s, "alex", "alex")
            out.append(f"undo seq {s}: ok as seq {seq}")
        except Exception as e:
            out.append(f"undo seq {s}: refused: {e}")
    j.commit("jeff", "jeff", "append", [(n, "text", "first line\nagent: two sources found\nagent: three")])
    s_txt = j.head
    j.commit("alex", "alex", "rewrite", [(n, "text", "a new first line")])
    try:
        j.undo(s_txt, "jeff", "jeff")
        out.append("undo the agent's append after alex's rewrite: ok (wrong)")
    except Exception as e:
        out.append(f"undo the agent's append after alex's rewrite: refused: {e}")
    report("J5", j5.title, "journal",
           "Colour, title, then an agent's line of text; Alex undoes colour and title. Then the agent's append is overwritten and he tries to undo it.",
           out + [f"now: title {j.value(n, 'title')!r}, color {j.value(n, 'prop:color')!r}"],
           "as designed: the text line does not block props or title; a real conflict names the blocker and offers the forward write")


@scenario("J6", "prototype: a script edited on both sides of a fork")
def j6():
    import journal
    base = jnew("defs")
    script = journal.gid()
    base.commit("alex", "alex", "script morning = look", [(script, "kind", "script"), (script, "title", "morning"), (script, "code", "look")])
    fork, F = journal.fork(base, base.path.with_name("defs@x.jsonl"))
    fork.commit("alex", "alex", "script morning = find tag:urgent", [(script, "code", "find tag:urgent")])
    base.commit("jeff", "jeff", "script morning = look Inbox", [(script, "code", "look Inbox")])
    m = journal.merge(base, fork, F, "x", "alex")
    report("J6", j6.title, "journal",
           "The morning script, edited in a fork by Alex and at home by the agent.",
           [f"merge: {m['clean']} clean, {len(m['held'])} held: " + "; ".join(f"{h['target'][1]}: here {h['here']!r} vs there {h['there']!r}" for h in m["held"]),
            f"the script still reads {base.value(script, 'code')!r} until someone takes, keeps or sets"],
           "as designed: a definition is a referent with a code aspect, so the conflict is held, not silent")


@scenario("J9", "prototype: a refused batch keeps its number, and says who")
def j9():
    import journal
    j = jnew("batch")
    casey = thing(j, "ana", "note", "Casey")
    try:
        j.commit("ana", "ana", "Casey owes 514.29", [(casey, "prop:owe", "514.29"), (casey, "prop:owe", "514.2857", "rule r3")])
        why, rseq = "committed (wrong)", None
    except journal.Refusal as e:
        why, rseq = e.why, e.seq
    nxt = thing(j, "ana", "note", "Other") and j.head
    report("J9", j9.title, "journal",
           "Ana types Casey's share while rule r3 computes it in the same batch (Juniper c346, 1). Then she makes another note.",
           [f"refused as seq {rseq}: {why}", f"the next batch is seq {nxt}; seq {rseq} is a refusal line with no ops: {not j.line(rseq)['ops']}",
            f"the refusal line holds no values: {'514' not in json.dumps(j.line(rseq))}; it reads {j.line(rseq)['refused']['why']!r}"],
           "as designed; the refused values belong in Ana's viewer store (Pike's side), the fact of the refusal in the journal")


@scenario("J10", "prototype: an undo is a change the fence sees")
def j10():
    import journal
    j = jnew("fence")
    n = thing(j, "alex", "note", "Call", "call Sam at 5")
    s = j.commit("wren", "wren", "rewrite", [(n, "text", "call Sam at 3")])
    seen = j.head
    j.commit("ben", "ben", "statement", [(journal.gid(), "text", "Sam at 3")], reads=[[n, ["text"], seen]])
    _, notes = j.undo(s, "wren", "wren")
    try:
        j.commit("alex", "alex", "rewrite", [(n, "text", "call Sam at 3, bring the forms")], reads=[[n, ["text"], seen]])
        r = "accepted (wrong)"
    except journal.Refusal as e:
        r = f"refused: {e.why}"
    report("J10", j10.title, "journal",
           "Wren changes the call to 3; Alex and Ben read it (Ben's statement copies it); Wren undoes; Alex adds to what he read.",
           [f"wren's undo notes: {notes}", f"Alex's rewrite: {r}"],
           "as designed: the undo is inverse ops, so the read is stale exactly; the undo is not blocked by Ben's read, it says so")



@scenario("J8", "prototype: Alex types in a document while an agent appends to it (text as hunks)")
def j8():
    import journal
    j = jnew("doc")
    doc = journal.gid()
    ops, _ = journal.text_ops(j, doc, "## Intro\nold intro\n## Notes\n- first")
    j.commit("alex", "alex/main", "create Essay", [(doc, "kind", "note"), (doc, "title", "Essay")] + ops)
    seen = j.head                                    # Alex's editor shows the text as of here, and he starts typing
    for i in range(3):
        ops, reads = journal.text_ops(j, doc, journal.text(j, doc) + f"\n- agent: source {i + 1}")
        j.commit("jeff", "jeff", f"append source {i + 1}", ops, reads)
    mine = "## Intro\nA new intro, typed while the agent worked.\n## Notes\n- first"
    ops, reads = journal.text_ops(j, doc, mine, seen)
    try:
        r = f"ok as seq {j.commit('alex', 'alex/main', 'rewrite Intro', ops, reads)}, {len(ops)} op(s) on hunks Alex saw"
    except journal.Refusal as e:
        r = f"refused: {e.why}"
    both = journal.text(j, doc)
    # now the agent and Alex both edit the Intro line, from the same view
    seen2 = j.head
    ops, reads = journal.text_ops(j, doc, both.replace("A new intro", "An agent's intro"), seen2)
    j.commit("jeff", "jeff", "edit intro", ops, reads)
    ops, reads = journal.text_ops(j, doc, both.replace("A new intro", "Alex's second intro"), seen2)
    try:
        j.commit("alex", "alex/main", "edit intro again", ops, reads)
        r2 = "accepted (wrong)"
    except journal.Refusal as e:
        r2 = f"refused: {e.why[:110]}"
    report("J8", j8.title, "journal",
           "Alex's four-region workspace again: the agent appends three sources under Notes while Alex rewrites the Intro from the text he saw.",
           [f"Alex's rewrite, diffed against what he saw: {r}", "the document now reads: " + " | ".join(both.split("\n")),
            f"the same line written by both, from the same view: {r2}"],
           "as designed: hunks are aspects, so a person and a background writer meet only where they touch the same hunk")


def main():
    out = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv[:-1] else None
    here = Path.cwd()
    keep = worktree.SESSIONS
    for fn in (s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, j2, j3, j5, j6, j8, j9, j10):
        try:
            fn()
        except Exception:
            import traceback
            report(fn.code, fn.title, "error", "", traceback.format_exc().strip().splitlines()[-3:], "")
        finally:
            worktree.SESSIONS = keep
            os.chdir(here)
    tally = {}
    for r in RESULTS:
        tally[r["status"]] = tally.get(r["status"], 0) + 1
    print("tally: " + ", ".join(f"{v} {k}" for k, v in sorted(tally.items())))
    import shutil
    for d in SCRATCH:
        shutil.rmtree(d, ignore_errors=True)
    if out:
        Path(out).write_text(json.dumps(RESULTS, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
