"""test_due_any (a3359): 'has a due date' is asked as due:any, and prop:due names the door instead of matching nothing.

    python test_due_any.py

Lived 4 Oct (Wishes e6030; Pike e6040): a thing printed 'due 2026-10-10', `find prop:due` answered 'nothing matches' and
a lens's `only when prop:due` was silently empty, because due is a field of its own, not a prop. Builds its own small
world in memory (roomworld.py) and runs every line through the desk's own dispatch, as explore.py and deskd call it.
"""
import os
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

import knife       # noqa: E402
import lens_ir     # noqa: E402
import roomworld   # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1500]}"))
    if not ok:
        fails.append(name)


D, R = roomworld.build(say=False)
W = D.world
ME = "juniper"
CORNER = R.corner[ME]
DOORS = "due is not a prop: use due:any, due<DATE or due>DATE"


def say(*lines):
    """One reply as juniper. -> [(text, error)] for each line run; it stops at the first refusal, as explore does."""
    W.me = ME
    per = D._per
    if ME not in per:
        per[ME] = ({}, {W.root}, len(W.events))
    D.seen, D.open, D.last_event_seen = per[ME]
    D._window = ""
    token, out = uuid.uuid4().hex, []
    for line in lines:
        r = D.dispatch("desk", {"line": line, "whole": True, "reply": token})
        out.append((r.get("text") or "", r.get("error") or ""))
        if r.get("error"):
            break
    return out


def one(line):
    return say(line)[0]


def make(words):
    txt, err = say(f"look {CORNER} :1", f"do create {CORNER} {words}")[-1]
    return (None if err else W.last_created), txt, err


def ids(sel):
    return set(D._parse_selection(sel)[0])


# an ordinary week: a bill and a call with dates, a note with a date, two tasks with none, and a task that carries an
# old shadow prop named like a date but no due date
BILL, _, _ = make('kind=task title="Pay the water bill" due=2026-10-10')
CALL, _, _ = make('kind=task title="Call the dentist"')
say(f"do due {CALL} on=2026-10-06")
LIST, _, _ = make('kind=note title="Packing list" due=2026-11-01')
SOCKS, _, _ = make('kind=task title="Buy socks"')
SHELF, _, _ = make('kind=task title="Fix the shelf"')
say(f"do prop {SHELF} deadline=friday")
check("the week is made", all((BILL, CALL, LIST, SOCKS, SHELF)) and W.subjects[W.nodes[CALL]["subject"]]["due"] == "2026-10-06")
HERE_TASKS = ids(f"kind:task,in:{CORNER}")

# (i) due:any, and its negation
txt, err = one(f"find due:any,in:{CORNER}")
check("find due:any lists the dated things, of any kind", not err and all(x in txt for x in (BILL, CALL, LIST))
      and SOCKS not in txt and SHELF not in txt and "3 thing(s)" in txt, err or txt)
check("due:any is what due<2999-12-31 was standing in for", ids("due:any") == ids("due<2999-12-31") and BILL in ids("due:any"))
txt, err = one(f"find -due:any,kind:task,in:{CORNER}")
check("find -due:any,kind:task lists the tasks without a date", not err and SOCKS in txt and SHELF in txt
      and BILL not in txt and CALL not in txt and LIST not in txt, err or txt)
check("with and without make the whole", ids(f"due:any,kind:task,in:{CORNER}") | ids(f"-due:any,kind:task,in:{CORNER}") == HERE_TASKS
      and not ids(f"due:any,kind:task,in:{CORNER}") & ids(f"-due:any,kind:task,in:{CORNER}"))
say(f"read {CALL}", f"do due {CALL} clear=1")
check("a date cleared leaves due:any", CALL not in ids("due:any") and CALL in ids("-due:any,kind:task"))
say("undo")
check("undo brings it back", CALL in ids("due:any"))
check("due:any combines with due<", ids(f"due:any,due<2026-10-08,in:{CORNER}") == {CALL})
txt, err = one(f"do tag due:any,in:{CORNER} add=dated")
check("a verb takes due:any as its target", not err and ids("tag:dated") == {BILL, CALL, LIST}, err or txt)

# (ii) prop:due is refused, naming the three forms
for line in ("find prop:due", "find prop:due=2026-10-10", "find -prop:due,kind:task", f"find kind:task,prop:due,in:{CORNER}",
             "do tag prop:due add=x", "table prop:due"):
    txt, err = one(line)
    check(f"{line}: refused, naming the door", err and DOORS in err, err or txt)
txt, err = one("find due:2026-10-10")
check("due:<a date> is refused, naming the three forms too", err and "due:any, due<DATE or due>DATE" in err, err or txt)
txt, err = one("find prop:deadline")
check("a prop that only sounds like a date is still a prop", not err and SHELF in txt, err or txt)
txt, err = one("find ?due")
check("the word due is still a word", "is not a prop" not in err, err)

# (iii) saved in a view, a rule or a lens: the author hears it at save
before = len(W.nodes)
V, txt, err = make('kind=view title="Dated" query=kind:task,prop:due')
check("a view made with prop:due is refused, naming the door, and nothing is made", not V and DOORS in err and len(W.nodes) == before, err or txt)
V, txt, err = make('kind=view title="Dated" query=kind:task,due:any cols=title,due')
check("a view of due:any is made", V and not err, err)
txt, err = say(f"look {V}")[-1]
check("and shows the dated tasks", BILL in txt and CALL in txt and SOCKS not in txt, err or txt)
_, ferr = one("find bogus:x")
_, err = say(f"look {CORNER} :1", f'do create {CORNER} kind=view title="Bogus" query=bogus:x')[-1]
check("any term that doesn't parse refuses a new view, in find's own words", err and err == ferr, (err, ferr))
txt, err = one(f"do prop {V} query=prop:due")
check("prop query=prop:due on it is refused; its selection stays", DOORS in err and W.nodes[V]["query"] == "kind:task,due:any", err or W.nodes[V])
txt, err = one(f"do prop {V} query=-due:any,kind:task")
check("prop query=-due:any is taken", not err and W.nodes[V]["query"] == "-due:any,kind:task", err)

RULE, txt, err = make('kind=note tags=rule title="flag the dated" text="when prop:due,kind:task do tag add=flagged"')
check("a rule saved with prop:due is saved broken, naming the door", "saved broken" in txt and DOORS in txt, err or txt)
txt, err = one("rules")
check("rules lists it as broken, with the door", DOORS in txt, err or txt)
txt, err = say(f"read {RULE}", f'do rewrite {RULE} text="when due:any,kind:task do tag add=flagged"')[-1]
check("rewritten with due:any it is saved whole", not err and "saved broken" not in txt, err or txt)
check("what was dated already is not acted on (a rule acts on what enters)", ids("tag:flagged") == set(), ids("tag:flagged"))
say(f"read {SOCKS}", f"do due {SOCKS} on=2026-10-20")
check("a task given a date later enters it, alone", ids("tag:flagged") == {SOCKS}, ids("tag:flagged"))

LENS_OK = 'window : column\\n  rows : column, of kind:task,due:any,in:%s, each card\\ncard : row\\n  t : text \\"$title\\"\\n  d : text \\"due $due\\", only when due:any' % CORNER
L, txt, err = make(f'kind=note tags=lens title="dated-lens" text="{LENS_OK}"')
check("a lens with `of ...due:any` and `only when due:any` compiles when saved", L and "compiles" in txt and "does not compile" not in txt, err or txt)
txt, err = one("scene dated-lens")
check("its scene has the dated tasks and not the undated", not err and "Pay the water bill" in txt and "Fix the shelf" not in txt, err or txt)
for word, text in (("only when", LENS_OK.replace("only when due:any", "only when prop:due")),
                   ("of", LENS_OK.replace("of kind:task,due:any", "of kind:task,prop:due")),
                   ("role when", LENS_OK.replace('text \\"$title\\"', 'text \\"$title\\", role title, role heading when prop:due=2026-10-10')),
                   ("count", LENS_OK.replace('\\ncard', '\\n  n : text \\"$count dated\\", count prop:due\\ncard', 1))):
    txt, err = say(f"read {L}", f'do rewrite {L} text="{text}"')[-1]
    said = err or txt
    check(f"a lens saved with prop:due in `{word}` is told so, with its line", "does not compile" in said and DOORS in said and "line " in said, said)
txt, err = say(f"read {L}", f'do rewrite {L} text="{LENS_OK}"')[-1]
check("put back, it compiles again", "compiles" in txt and "does not compile" not in txt, err or txt)

# a `bind many` member is fenced by its due date under due:any, as under due<
check("due:any reads the due aspect", lens_ir.term_aspects("kind:task,due:any")[0] == {"due"} and lens_ir.term_aspects("-due:any")[0] == {"due"})
# (v) the Help binder's selections note is held to naming due: (helpnotes.check reads knife.TERMS)
check("due: is a selection term the help check asks for", "due:" in knife.TERMS)

print(f"\n{len(fails)} failed" if fails else "\nall passed")
sys.exit(1 if fails else 0)
