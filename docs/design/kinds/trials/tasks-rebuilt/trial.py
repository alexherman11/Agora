"""The tasks-rebuilt trial: Alex's taskboard beside a second team's Tracker (kind=issue) and a GitHub adapter
(kind=gh-issue), ~2,170 task-like things on a copy of the desktop log (build.py makes it). Each section opens its own
copy of the built world, so experiments never leak into one another. Prints what ran; FINDINGS.md quotes it.

    python trial.py [section ...]       sections: lens dispatch house rules govern perf (default: all)
"""
import ast
import json
import re
import shutil
import sys
import time
from collections import Counter

from common import SCRATCH, Kernel, Refused, Actor, steward, say, short
from kernel import lines as L
from painter.arrangement import compile_view

BUILT = SCRATCH / "w-built"
SABLE = "dk1148"                         # a member, not a steward, in the real world copy


def open_built(name):
    d = SCRATCH / name
    if d.exists():
        shutil.rmtree(d)
    (d / "log").mkdir(parents=True)
    shutil.copy(BUILT / "log" / "0001.jsonl", d / "log" / "0001.jsonl")
    t = time.perf_counter()
    k = Kernel(d)
    conv = json.load(open(BUILT / "conv.json"))
    return k, steward(k), Actor(SABLE, SABLE, "person"), conv, time.perf_counter() - t


def H(title):
    print("\n" + "=" * 100 + "\n## " + title + "\n" + "=" * 100)


def run(k, actor, line, label=None, n=420, mode="do"):
    try:
        out = k.run(actor, line, mode=mode)
    except Refused as e:                     # run reports refusals as ok=False; a raise is a different path
        out = {"ok": False, "text": f"(raised) {e}"}
    print(f"  [{label or k.name(actor.person)}] {line[:150]}\n      -> {short(out, n)}")
    return out


def ids(k, kind):
    return [t for t in k.things(kind) if not k.state.get(t, "forgotten")]


def decl(k, name):
    return [t for t in k.things("kind") if k.state.get(t, "name") == name and not k.state.get(t, "forgotten")][-1]


def entry(k, word):
    return k.find_entry(word)


def pick(k, actor, line):
    """What step does for a plain word (step calls plain_verb when no entry answers): the word picked, or the refusal."""
    st = L.parse(line)
    try:
        e = k.plain_verb(actor, st, None)
        return ("pick", k.state.get(e, "word")) if e else ("none", None)
    except Refused as ex:
        msg = str(ex)
        kind = "ask" if ("say which" in msg or "could mean" in msg or "could take" in msg) else "refuse"
        return (kind, msg)


def board_counts(view):
    """Cards drawn per (lane, own kind) in a compiled board view."""
    c = Counter()

    def walk(node, lane):
        if not isinstance(node, dict):
            return
        if node.get("component") == "lane":
            lane = (node.get("settings") or {}).get("name") or (node.get("facts") or {}).get("name")
        if node.get("component") == "card":
            c[(lane, (node.get("facts") or {}).get("kind"))] += 1
        for ch in node.get("children") or []:
            walk(ch, lane)
    for r in view.get("rows") or []:
        walk(r.get("tree"), None)
    return c


def lens_text(k, lens):
    return k.state.get(lens, "text")


def set_text(k, actor, thing, text, label=None):
    """A steward editing a lens by a line, as the desk would: the whole text, quotes escaped."""
    esc = text.replace("\\", "\\\\").replace('"', '\\"')
    return run(k, actor, f'set {thing} text="{esc}"', label=label, n=200)


def offer_house(k):
    """The House's OFFER, read from modules/house/house.py without importing it (its import starts transports)."""
    src = open("C:/Projects/Agora4/src/agora/modules/house/house.py", encoding="utf-8").read()
    tree = ast.parse(src)
    ns = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") in ("TASK_KINDS", "TASK_NEEDS", "OFFER")
                                                for t in node.targets):
            exec(compile(ast.Module([node], []), "house.py", "exec"), ns)
    mid = k.module_named("house")
    return ns["OFFER"], mid, k.on_offer(mid, ns["OFFER"])


def builders_logic():
    """held() and HELD from modules/house/builders.py, exec'd from its source (its import needs transport)."""
    src = open("C:/Projects/Agora4/src/agora/modules/house/builders.py", encoding="utf-8").read()
    tree = ast.parse(src)
    ns = {}
    for node in tree.body:
        if (isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "HELD" for t in node.targets)) or \
                (isinstance(node, ast.FunctionDef) and node.name == "held"):
            exec(compile(ast.Module([node], []), "builders.py", "exec"), ns)
    return ns["held"]


def shape_words(k, alex):
    """Phase B: each app gives its own words the shape their steps read, as the design asks (SHAPE 17)."""
    for w, how in [("issue.close", "acts_on=issue"), ("issue.reopen", "acts_on=issue"), ("issue.move", "acts_on=issue"),
                   ("issue.assign", "acts_on=issue"), ("issue.estimate", "acts_on=issue"),
                   ("gh.close", 'needs="kind=gh-issue"'), ("gh.reopen", 'needs="kind=gh-issue"'),
                   ("gh.assign", 'needs="kind=gh-issue"'),
                   ("task.done", 'acts_on=taskboard-task'), ("task.move", 'acts_on=taskboard-task'),
                   ("task.assign", 'acts_on=taskboard-task')]:
        k.run(alex, f"look {k.find_entry(w)}", mode="see")      # word-set is fenced like set: look first
        out = k.run(alex, f"word-set {w} {how}")
        if not out.get("ok"):
            print("   word-set", w, how, "->", short(out, 200))


# ====================================================================================================== Q1 lens
def sec_lens():
    H("Q1. Can Alex's board lens show the other apps' items?")
    k, alex, sable, conv, dt = open_built("t-lens")
    print(f"  opened built world in {dt:.2f}s; things={len(k.state.things)}")
    view, t = None, time.perf_counter()
    view = compile_view(k, alex, "dk262")
    print(f"  board before: {dict(board_counts(view))}  ({(time.perf_counter() - t) * 1000:.0f} ms)")

    print("\n  -- steward opens Alex's own kind to the other apps' things")
    run(k, alex, f'set {decl(k, "taskboard-task")} needs="title|name lane|status|state"', "steward")
    run(k, alex, f'set {decl(k, "taskboard-task")} extends=issue', "steward")

    print("\n  -- steward instead declares a shared kind and points the board at it")
    run(k, alex, 'make kind=kind name=task needs="title|name lane|status|state"', "steward")
    kinds_of_task = Counter(r.get("kind") for r in k.run(alex, "rows task", mode="see")["rows"])
    print("  rows task, by own kind:", dict(kinds_of_task))
    text = lens_text(k, "dk262").replace("tag:taskboard-task", "tag:task")
    set_text(k, alex, "dk262", text, "steward")
    print("  lens now says tag:task:", "tag:task," in lens_text(k, "dk262"))
    t = time.perf_counter()
    view = compile_view(k, alex, "dk262")
    print(f"  board after tag:task: {dict(board_counts(view))}  ({(time.perf_counter() - t) * 1000:.0f} ms)")
    i0 = conv["issue"][0]
    filled = k.kinds.filled(k.shown(alex.person, i0), "task")
    print(f"  an issue read as a task: title={filled.get('title')!r} lane={filled.get('lane')!r} as={filled.get('as')!r} who={filled.get('who')!r}")
    g0 = conv["gh"][0]
    filled = k.kinds.filled(k.shown(alex.person, g0), "task")
    print(f"  a gh-issue read as a task: title={filled.get('title')!r} lane={filled.get('lane')!r} as={filled.get('as')!r}")

    print("\n  -- the only way to get them on the board: lanes named after the other apps' values")
    for i, v in enumerate(["open", "in_progress", "closed"]):
        run(k, alex, f"make kind=taskboard-lane name={v} order={3 + i}", "steward", n=120)
    t = time.perf_counter()
    view = compile_view(k, alex, "dk262")
    print(f"  board with six lanes: {dict(board_counts(view))}  ({(time.perf_counter() - t) * 1000:.0f} ms)")
    print("  view text:", view["text"])

    print("\n  -- what else is a task now (false fits in the real world)")
    for need in ['title|name lane|status|state', 'title|name status|lane', 'name status', 'title state']:
        k2 = k
        others = Counter()
        from kernel.kinds import parse
        needs = parse(need)
        for tid, a in k2.state.things.items():
            if a.get("forgotten") or a.get("kind") in ("taskboard-task", "issue", "gh-issue"):
                continue
            row = k2.shown(alex.person, tid)
            if row and row.get("kind") not in k2.kinds.__class__.__dict__.get("NOT_FITTED", ()) and not k2.kinds.missing(row, needs):
                from kernel.kinds import NOT_FITTED
                if row.get("kind") not in NOT_FITTED:
                    others[row.get("kind")] += 1
        print(f"   needs={need!r}: other things that fit: {dict(others)}")

    print("\n  -- the work lens (dk898) reads who=Alex and lane=Now; issues say assignee and status")
    k.run(alex, "look dk898", mode="see")
    text = lens_text(k, "dk898").replace("tag:taskboard-task", "tag:task")
    set_text(k, alex, "dk898", text, "steward")
    run(k, alex, f'set {decl(k, "task")} needs="title|name lane|status|state who|assignee"', "steward (widen? adds a need)")
    v = compile_view(k, alex, "dk898")
    print("  work view:", v["text"][:300])


# ====================================================================================================== Q2 dispatch
def dispatch_stats(k, actor, conv, label, words=("done", "close", "move", "assign"), by_name_sample=60):
    apps = {"taskboard-task": ids(k, "taskboard-task"), "issue": ids(k, "issue"), "gh-issue": ids(k, "gh-issue")}
    for w in words:
        for app, xs in apps.items():
            c, eg = Counter(), {}
            t = time.perf_counter()
            for x in xs:
                r = pick(k, actor, f"{w} {x}")
                key = r[0] + ":" + (r[1] if r[0] == "pick" else re.sub(r"dk\d+", "<id>", r[1])[:90])
                c[key] += 1
            dt = (time.perf_counter() - t) / max(1, len(xs))
            print(f"   [{label}] {w} <{app} id> x{len(xs)} ({dt * 1000:.2f} ms each): " +
                  "; ".join(f"{n} {kk}" for kk, n in c.most_common(4)))
    # by name: converted names exist in all three apps
    names = [k.state.get(t, "title") for t in ids(k, "taskboard-task")[:58]][:by_name_sample]
    for w in ("done", "close"):
        c = Counter()
        t = time.perf_counter()
        for nm in names:
            r = pick(k, actor, f'{w} "{nm}"')
            c[r[0] + ":" + (r[1] if r[0] == "pick" else re.sub(r"dk\d+", "<id>", r[1])[:100])] += 1
        dt = (time.perf_counter() - t) / max(1, len(names))
        print(f"   [{label}] {w} <name of a converted card> x{len(names)} ({dt * 1000:.1f} ms each): " +
              "; ".join(f"{n} {kk}" for kk, n in c.most_common(4)))


def sec_dispatch():
    H("Q2. done <thing> across three apps")
    k, alex, sable, conv, dt = open_built("t-dispatch")
    print("  entries for the plain words themselves:", {w: k.find_entry(w) for w in ("done", "close", "move", "assign")})
    print("\n  Phase A: apps as installed (no word has a shape)")
    dispatch_stats(k, alex, conv, "A")

    print("\n  Phase B1: the two new apps add done words with shapes; Alex's task.* are untouched (no shape)")
    run(k, alex, 'verb issue.done acts_on=issue steps="set $1 status=closed" help="issue.done <issue>: close it."', "steward")
    run(k, alex, 'verb gh.done needs="kind=gh-issue" steps="set $1 state=closed" help="gh.done <gh-issue>: close it."', "steward")
    nm = k.state.get("dk91", "title")
    print(f"   {nm!r} is dk91 (Alex's card), {conv['issue'][1]} (issue), {conv['gh'][1]} (gh-issue)")
    print("   done <name> ->", pick(k, alex, f'done "{nm}"'))
    c1 = run(k, alex, 'make kind=taskboard-task title="Pay rent" lane=Now who=Alex', "steward")["made"][0]
    i1 = run(k, alex, 'make kind=issue name="Pay rent" status=open', "Tracker import")["made"][0]
    print(f"   card {c1}, issue {i1}: done \"Pay rent\" ->", pick(k, alex, 'done "Pay rent"'))
    print(f"   done {c1} (the card, by id) ->", pick(k, alex, f"done {c1}"))
    dispatch_stats(k, alex, conv, "B1", words=("done",))

    print("\n  Phase B2: every app's words say their shape (task.* acts_on=taskboard-task, issue.* acts_on=issue, gh.* needs=kind=gh-issue)")
    shape_words(k, alex)
    dispatch_stats(k, alex, conv, "B2")
    print("   done <name in three apps> ->", pick(k, alex, f'done "{nm}"'))
    print("   done \"Pay rent\" ->", pick(k, alex, 'done "Pay rent"'))
    k.run(alex, "look dk91", mode="see")
    print("   task.done <name> (explicit word) ->", short(k.run(alex, f'task.done "{nm}"'), 200))

    print("\n  Phase B, a thing that fits two shapes: an issue imported from GitHub that keeps both vocabularies")
    both = run(k, alex, 'make kind=gh-issue title="Both worlds" name="Both worlds" number=9999 state=open status=open', "steward")
    tb = both["made"][0]
    run(k, alex, f'word-set issue.done acts_on="" needs="name status"', "steward: issue.done reads name and status, not the kind")
    print("   done <both> ->", pick(k, alex, f"done {tb}"))
    k.run(alex, f"look {k.find_entry('gh.done')}", mode="see")
    run(k, alex, f'word-set gh.done needs="title state"', "steward: gh.done reads title and state")
    print("   done <both> ->", pick(k, alex, f"done {tb}"))
    print("   done <a plain note with name+status> ->",
          pick(k, alex, "done " + run(k, alex, 'make kind=note name="Groceries" status=open', "steward")["made"][0]))

    print("\n  Phase B, a thing that fits none: a document, a chat, a lane")
    for x in ("dk79", next(iter(ids(k, "chat"))), next(iter(ids(k, "document")))):
        print(f"   done {x} ({k.state.get(x, 'kind')}) ->", pick(k, alex, f"done {x}"))

    print("\n  Phase C: a member hijacks the plain word with a more specific shape")
    run(k, sable, 'verb tidy.done acts_on=issue needs="project estimate" steps="forget $1" help="tidy.done <issue>: tidy it away."', "Sable (member)")
    print("   Alex: done <issue with project+estimate> ->", pick(k, alex, f"done {conv['issue'][0]}"))
    out = run(k, alex, f"done {conv['issue'][0]}", "Alex types done")
    print("   issue forgotten?", k.state.get(conv["issue"][0], "forgotten"))

    print("\n  Phase D (fresh copy): the Tracker team learns Agora says done, and aliases issue.close as issue.done")
    k, alex, sable, conv, dt = open_built("t-dispatch-alias")
    run(k, alex, f"look {k.find_entry('issue.close')}", "steward", n=40, mode="see")
    run(k, alex, "word-set issue.close aliases=issue.done", "steward")
    print("   done <issue> ->", pick(k, alex, f"done {conv['issue'][3]}"))
    run(k, alex, 'verb issue.done acts_on=issue steps="set $1 status=closed" help="issue.done <issue>: close it."', "steward")
    run(k, alex, f'word-set issue.done needs="name"', "steward edits 'issue.done'")

# ====================================================================================================== Q3 house
def sec_house():
    H("Q3. Can the House build an issue? (reaches isn't works)")
    k, alex, sable, conv, dt = open_built("t-house")
    offer, mid, receipt = offer_house(k)
    print("  re-offer:", receipt[:6])
    hb = entry(k, "house.build")
    print("  house.build entry:", {x: k.state.get(hb, x) for x in ("needs", "acts_on", "may")})
    card, issue, gh = "dk91", conv["issue"][1], conv["gh"][1]
    run(k, alex, f"house.build {card}", "steward: card")
    run(k, alex, f"house.build {issue}", "steward: issue")
    run(k, alex, f"task.build {issue}", "steward: task.build verb on an issue")
    print("   build <issue> (plain) ->", pick(k, alex, f"build {issue}"))
    print("   build <card> (plain) ->", pick(k, alex, f"build {card}"))

    print("\n  -- the steward widens the House to the Tracker and GitHub kinds")
    k.run(alex, f"look {hb}", mode="see")
    run(k, alex, 'word-set house.build needs="kind=taskboard-task|task|issue|gh-issue"', "steward")
    run(k, alex, f"house.build {issue}", "steward: issue")
    run(k, alex, f"house.build {gh}", "steward: gh-issue")
    print("   house.build <task_thing>:")
    tt = run(k, alex, 'make kind=task_thing title="A task by another name" text="Build me" who=Alex lane=Now', "steward")["made"][0]
    run(k, alex, f"house.build {tt}", "steward: task_thing")

    print("\n  -- what builders.py then reads (modules/house/builders.py: held() :39, who :196, title/basis :205-208, prompt :405-408)")
    held = builders_logic()
    stats = Counter()
    for app, xs in (("taskboard-task", ids(k, "taskboard-task")), ("issue", ids(k, "issue")), ("gh-issue", ids(k, "gh-issue"))):
        for x in xs:
            row = (k.run(alex, f"look {x}", mode="see").get("rows") or [{}])[0]
            closed = (row.get("lane") == "Done") or (row.get("status") == "closed") or (row.get("state") == "closed")
            if closed and not held(row):
                stats[(app, "finished but not held: buildable")] += 1
            if not row.get("title"):
                stats[(app, "no title: prompt says 'Codex — Builder', Current task: <id>")] += 1
            if not row.get("text"):
                stats[(app, "no text: prompt's Task text is empty")] += 1
            owner = row.get("assignee") or row.get("who")
            if not row.get("who") and owner and owner not in ("Alex", "JEFF", "alexherman11"):
                stats[(app, "owned by someone else under another spelling: owner check skipped")] += 1
        stats[(app, "total")] = len(xs)
    for (app, what), n in sorted(stats.items()):
        print(f"   {app:15s} {n:5d}  {what}")
    row = (k.run(alex, f"look {issue}", mode="see").get("rows") or [{}])[0]
    print("   look <issue> as the House reads it: keys", sorted(x for x in row if not x.startswith("in:"))[:20])

    print("\n  -- an honest shape: what builders.py reads, as needs")
    for need in ["title text", "title text who", "title text acceptance", "title|name text|description|body"]:
        from kernel.kinds import parse
        ns = parse(need)
        c = Counter()
        for app in ("taskboard-task", "issue", "gh-issue"):
            for x in ids(k, app):
                if not k.kinds.missing(k.shown(alex.person, x), ns):
                    c[app] += 1
        print(f"   needs={need!r}: reaches {dict(c)} (Alex's real 58 cards: "
              f"{sum(1 for x in ids(k, 'taskboard-task')[:58] if not k.kinds.missing(k.shown(alex.person, x), ns))})")

    print("\n  -- widening by the shared kind instead: house.build acts_on=task")
    run(k, alex, 'make kind=kind name=task needs="title|name lane|status|state"', "steward")
    k.run(alex, f"look {hb}", mode="see")
    run(k, alex, 'word-set house.build acts_on=task needs=""', "steward")
    print("   house.build entry:", {x: k.state.get(hb, x) for x in ("needs", "acts_on")})
    reach = Counter()
    for t, a in k.state.things.items():
        if a.get("forgotten") or not a.get("kind") or k.shown(alex.person, t) is None:
            continue
        try:
            k.kinds.check_word(alex, k.state.things[hb], t)
            reach[a.get("kind")] += 1
        except Refused:
            pass
    print("   house.build now reaches:", dict(reach))

    print("\n  -- the House re-offers (as at every start), then ships a narrower shape")
    print("   re-offer:", k.on_offer(mid, offer)[2:3])
    off2 = [dict(w, needs="kind=taskboard-task|task title") if w["word"] == "house.build" else w for w in offer]
    print("   new House offer:", k.on_offer(mid, off2)[2:3], "| notices:", k.notices[-1:] if getattr(k, "notices", None) else None)
    print("   house.build entry:", {x: k.state.get(hb, x) for x in ("needs", "acts_on")})


# ====================================================================================================== Q4 rules, grants
def sec_rules():
    H("Q4. Rules (of_kind=) and grants (only=kind:) after widening")
    k, alex, sable, conv, dt = open_built("t-rules")
    issue, card = conv["issue"][5], "dk92"

    def posts_about(t):
        return [p for p in ids(k, "post") if k.state.get(p, "about") == t]

    print("  -- the steward widens task.done to issues (needs=kind=taskboard-task|issue), no shared kind")
    k.run(alex, "look dk85", mode="see")
    run(k, alex, 'word-set task.done needs="kind=taskboard-task|issue"', "steward")
    run(k, alex, f"rows issue", "steward", n=60, mode="see")
    run(k, alex, f"task.done {issue}", "steward")
    print("   the issue now says:", {x: k.state.get(issue, x) for x in ("status", "lane")})
    run(k, alex, f"look {card}", "steward", n=40, mode="see")
    run(k, alex, f"task.done {card}", "steward")
    time.sleep(1.5)
    print("   announcement posts about the card:", len(posts_about(card)), "| about the issue:", len(posts_about(issue)))

    print("\n  -- a shared kind exists (title|name lane|status), then task.done on an issue")
    run(k, alex, 'make kind=kind name=task needs="title|name lane|status|state"', "steward")
    issue2 = conv["issue"][6]
    run(k, alex, f"look {issue2}", "steward", n=40, mode="see")
    run(k, alex, f"task.done {issue2}", "steward")

    print("\n  -- the steward widens the rule to the shared kind")
    k.run(alex, "look dk168", mode="see")
    run(k, alex, 'set dk168 of_kind=task', "steward")
    card2 = "dk93"
    run(k, alex, f"look {card2}", "steward", n=40, mode="see")
    run(k, alex, f"task.done {card2}", "steward")
    time.sleep(1.5)
    print("   announcement posts about the card after of_kind=task:", len(posts_about(card2)))
    k.run(alex, "look dk168", mode="see")
    run(k, alex, 'set dk168 of_kind="taskboard-task,issue"', "steward")
    print("   rule matches a card's happening?", k._rule_matches(k.state.things["dk168"], {"entry": "dk85", "target": card2}))

    print("\n  -- grants: summarize may write only kind:taskboard-task")
    summ = Actor("dk174", alex.person, "module", module="dk174", caller=alex)
    k.mark(summ, issue, ["short"])
    k.mark(summ, card, ["short"])
    run(k, summ, f'set {card} short="sum"', "summarize for Alex: card")
    run(k, summ, f'set {issue} short="sum"', "summarize for Alex: issue")
    run(k, alex, 'set dk175 only=kind:task', "steward widens the grant to the shared kind")
    run(k, alex, 'grant dk174 words="set" only=kind:task', "steward adds a grant for the shared kind")
    k.mark(summ, issue, ["short"])
    run(k, summ, f'set {issue} short="sum2"', "summarize for Alex: issue, after only=kind:task")
    run(k, alex, 'grant dk174 words="set" only=kind:issue', "steward adds a grant for issue by own kind")
    k.mark(summ, issue, ["short"])
    run(k, summ, f'set {issue} short="sum3"', "summarize for Alex: issue, after only=kind:issue")
    note = run(k, alex, 'make kind=note title="Private plan" lane=Now text="not for the model"', "steward")["made"][0]
    k.mark(summ, note, ["short"])
    run(k, summ, f'set {note} short="x"', "summarize: a note that fits task (title, lane)")

    print("\n  -- the board widget draws issues (lens tag:task), then Alex drags one to Done")
    widget = Actor("dk263", alex.person, "module", module="dk263", caller=alex)
    issue3 = conv["issue"][7]
    saw = {issue3: k.state.rev.get(issue3, 0)}
    try:
        out = k.run(widget, f"task.move {issue3} to=Done", saw=saw)
    except Refused as e:
        out = {"ok": False, "text": str(e)}
    print(f"  [board widget for Alex] task.move {issue3} to=Done\n      -> {short(out, 300)}")
    out = k.run(widget, f"issue.move {issue3} to=closed", saw=saw)
    print(f"  [board widget for Alex] issue.move {issue3} to=closed\n      -> {short(out, 300)}")
    run(k, alex, 'grant dk263 words="issue.move set" only=kind:issue', "steward grants the board the Tracker's word")
    out = k.run(widget, f"issue.move {issue3} to=closed", saw=saw)
    print(f"  [board widget for Alex] issue.move {issue3} to=closed (after grant)\n      -> {short(out, 300)}")
    out = k.run(widget, f"task.move {issue3} to=Done", saw={issue3: k.state.rev.get(issue3, 0)})
    print(f"  [board widget for Alex] task.move {issue3} to=Done (the board's own drop word, after grant)\n      -> {short(out, 300)}")


# ====================================================================================================== Q5 governance
def sec_govern():
    H("Q5. Spellings, mark, widen-only, leaders-only: a member and the steward")
    k, alex, sable, conv, dt = open_built("t-govern")
    run(k, sable, 'make kind=kind name=todo needs="name status"', "Sable (member)")
    run(k, sable, 'make kind=kind name=todo', "Sable (member)")

    print("\n  -- order matters: words first, then the shape")
    shape_words(k, alex)
    run(k, alex, f'set {decl(k, "issue")} needs="name status"', "steward: shape issue after words use it")
    run(k, alex, 'make kind=kind name=issue needs="name status"', "steward: a second declaration instead")
    print("   issue shape now:", [n.text() for n in (k.kinds.shape("issue") or [])])
    n_rows = len(k.run(alex, "rows issue", mode="see")["rows"])
    print("   rows issue:", n_rows, "| issue.close reaches a note with name+status?")
    note = run(k, alex, 'make kind=note name="Shopping" status=open', "steward")["made"][0]
    run(k, alex, f"look {note}", "steward", n=30, mode="see")
    run(k, alex, f"issue.close {note}", "steward")
    bare = run(k, alex, 'make kind=issue name="No status yet"', "steward")["made"][0]
    run(k, alex, f"look {bare}", "steward", n=30, mode="see")
    print("   a bare issue is in rows issue?", bare in [r["id"] for r in k.run(alex, "rows issue", mode="see")["rows"]])
    run(k, alex, f"issue.close {bare}", "steward: close an issue that has no status yet")

    print("\n  -- a member shadows the steward's kind with a later, closed declaration")
    run(k, sable, 'make kind=kind name=issue help="my issues"', "Sable (member)")
    print("   issue shape now:", k.kinds.shape("issue"), "| rows issue:", len(k.run(alex, "rows issue", mode="see")["rows"]))
    run(k, alex, f"look {note}", "steward", n=30, mode="see")
    run(k, alex, f"issue.reopen {note}", "steward: reopen the note it reached a moment ago")
    run(k, sable, f'forget {decl(k, "issue")}', "Sable forgets her own declaration")
    print("   issue shape back:", [n.text() for n in (k.kinds.shape("issue") or [])])
    run(k, sable, f'set {decl(k, "issue")} needs="name"', "Sable edits the steward's declaration")
    run(k, sable, f'set {decl(k, "issue")} help="hijacked"', "Sable edits the steward's declaration's help")

    print("\n  -- widen-only lets the steward widen a kind under the words that act on it")
    run(k, alex, f'set {decl(k, "issue")} needs="name"', "steward drops status (a widening)")
    run(k, alex, "look dk79", "steward", n=30, mode="see")
    run(k, alex, "issue.close dk79", "steward: issue.close on Alex's Backlog LANE")
    print("   lane dk79 now:", {x: k.state.get("dk79", x) for x in ("name", "status")})
    w = next(iter(ids(k, "window")))
    run(k, alex, f"look {w}", "steward", n=30, mode="see")
    run(k, alex, f"issue.assign {w} who=Bea", "steward: issue.assign on a window")
    run(k, alex, f'set {decl(k, "issue")} needs="name status"', "steward: take it back (narrow)")

    print("\n  -- spellings: a shared kind with lane|status, then the House's own hold")
    run(k, alex, 'make kind=kind name=task needs="title|name lane|status|state"', "steward")
    card = "dk94"
    run(k, alex, f"look {card}", "steward", n=30, mode="see")
    run(k, alex, f"set {card} status=paused", "steward: hold a build (builders.py HELD reads status)")
    lacking = sum(1 for t in ids(k, "taskboard-task")[:58] if not k.state.get(t, "status"))
    print(f"   of Alex's 58 real cards, {lacking} have no status, so none of them can be held this way now")
    gh = conv["gh"][2]
    run(k, alex, f"look {gh}", "steward", n=30, mode="see")
    run(k, alex, f"set {gh} status=triaged", "steward: the adapter mirrors GitHub Projects' status field")
    issue = conv["issue"][2]
    run(k, alex, f"look {issue}", "steward", n=30, mode="see")
    run(k, alex, f"task.move {issue} to=Now", "steward: drag an issue on the board")

    print("\n  -- mark")
    run(k, alex, 'make kind=kind name=tracked needs="title|name tracked=yes"', "steward")
    run(k, sable, f"look {gh}", "Sable", n=30, mode="see")
    run(k, sable, f"mark {gh} tracked", "Sable marks a GitHub issue (the adapter made it)")
    run(k, alex, f"mark {gh} tracked", "steward marks it")
    run(k, alex, f"mark {gh} task", "steward: mark a gh-issue a task")

    print("\n  -- the needs grammar on real values")
    run(k, alex, 'make kind=kind name=wip needs="status=In Progress"', "steward: Linear's real status value")
    print("   wip shape:", [n.text() for n in (k.kinds.shape("wip") or [])])
    run(k, alex, 'make kind=kind name=finished needs="lane|status|state=Done|closed"', "steward")
    print("   finished shape:", [n.text() for n in (k.kinds.shape("finished") or [])])
    c = Counter(r.get("kind") for r in k.run(alex, "rows finished", mode="see")["rows"])
    print("   rows finished:", dict(c))
    run(k, alex, 'verb issue.archive acts_on=isue steps="set $1 archived=yes" help="issue.archive <issue>"', "steward: a typo in acts_on")
    run(k, alex, f"look {issue}", "steward", n=30, mode="see")
    run(k, alex, f"issue.archive {issue}", "steward")


# ====================================================================================================== Q6 perf
def sec_perf():
    H("Q6. Timings at scale")
    k, alex, sable, conv, dt = open_built("t-perf")
    print(f"  open the built world ({len(k.log.records)} records, {len(k.state.things)} things): {dt:.2f}s")
    shape_words(k, alex)
    run(k, alex, 'verb issue.done acts_on=issue steps="set $1 status=closed" help="issue.done <issue>"', "steward", n=80)

    def tm(label, fn, reps=3):
        best = None
        for _ in range(reps):
            t = time.perf_counter()
            out = fn()
            d = time.perf_counter() - t
            best = d if best is None else min(best, d)
        extra = ""
        if isinstance(out, dict) and "rows" in out:
            extra = f" rows={len(out['rows'])}"
        print(f"   {label:58s} {best * 1000:9.1f} ms{extra}")
        return out
    see = lambda line: (lambda: k.run(alex, line, mode="see"))
    for phase in ("no shared kind", "shared kind task + 3 more kinds"):
        print(f"\n  [{phase}]")
        tm("rows taskboard-task (closed kind)", see("rows taskboard-task"))
        tm("rows issue (closed kind)", see("rows issue"))
        if phase != "no shared kind":
            tm("rows task (fitted, 2174 fit)", see("rows task"))
            tm("rows task exact=yes", see("rows task exact=yes"))
            tm("rows task lane=Now", see("rows task lane=Now"))
        tm("actions <card>", see("actions dk91"))
        tm("actions <issue>", see(f"actions {conv['issue'][1]}"))
        tm("kinds <issue>", see(f"kinds {conv['issue'][1]}"))
        tm("plain dispatch: done <issue id>", lambda: pick(k, alex, f"done {conv['issue'][1]}"), reps=5)
        tm("plain dispatch: done <card id>", lambda: pick(k, alex, "done dk91"), reps=5)
        nm = k.state.get("dk91", "title")
        tm("plain dispatch: done <name in three apps>", lambda: pick(k, alex, f'done "{nm}"'), reps=3)
        tm("task.done <name> (resolve only, refusal path)", lambda: pick(k, alex, 'done "no such name anywhere"'), reps=3)
        tm("compile board lens dk262", lambda: compile_view(k, alex, "dk262"), reps=2)
        tm("compile work lens dk898", lambda: compile_view(k, alex, "dk898"), reps=2)
        tm("users('taskboard-task')", lambda: k.kinds.users("taskboard-task"), reps=3)

        def a_set():
            t = conv["issue"][9]
            k.run(alex, f"look {t}", mode="see")
            return k.run(alex, f"set {t} estimate=3")
        tm("look + set <issue> estimate=3", a_set, reps=3)
        if phase == "no shared kind":
            run(k, alex, 'make kind=kind name=task needs="title|name lane|status|state"', "steward", n=60)
            for nm2, nd in [("event", None), ("dated", "due|when"), ("assigned", "assignee|who"), ("labelled", "labels")]:
                if nd:
                    run(k, alex, f'make kind=kind name={nm2} needs="{nd}"', "steward", n=60)
            text = lens_text(k, "dk262").replace("tag:taskboard-task", "tag:task")
            set_text(k, alex, "dk262", text, "steward")
            k.run(alex, "look dk898", mode="see")
            text = lens_text(k, "dk898").replace("tag:taskboard-task", "tag:task")
            set_text(k, alex, "dk898", text, "steward")


SECTIONS = {"lens": sec_lens, "dispatch": sec_dispatch, "house": sec_house, "rules": sec_rules,
            "govern": sec_govern, "perf": sec_perf}
if __name__ == "__main__":
    for name in (sys.argv[1:] or list(SECTIONS)):
        try:
            SECTIONS[name]()
        except Exception as e:                       # report and go on: a crash is a finding too
            import traceback
            print(f"\n!! section {name} crashed: {e!r}")
            traceback.print_exc(limit=6)
    sys.stdout.flush()
