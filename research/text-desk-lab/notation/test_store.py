"""test_store (7 Oct 2026): the log of records beside the world (store.py).

    python test_store.py            the in-memory part, then the CLI and deskd parts (processes; about 40 s)
    python test_store.py --quick    the in-memory part only (what health runs)

Builds its own small world (roomworld.py). Every line goes through the desk as a person's would, with store.begin
before it and store.commit after, as deskd and explore.py do. What is asked:

  - the log replayed says exactly what the world says, after several hundred lines of every kind;
  - a world rebuilt from its facts says the same facts;
  - what is on the log and what is not (reads, refusals, presence);
  - a record's size does not grow with the thing it changed (the 0.7 MB chat line of 7 Oct);
  - a command and what it set off are one record, put back whole by its facts, and that equals the world before;
  - the scenarios Alex and Claude walked on 7 Oct: an old change undone after later ones, a line someone answered,
    a rule firing, something changed outside the log, a write cut short, a record tampered with;
  - a document as blocks: two people in different paragraphs change different facts.
"""
import copy
import json
import os
import re
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"
sys.stdout.reconfigure(encoding="utf-8")

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:2500]}"))
    if not ok:
        fails.append(name)


import roomworld   # noqa: E402
import store       # noqa: E402

sys.path.insert(0, str(HERE.parents[1] / "window-lab"))
import agora_tmp   # noqa: E402

TMP = Path(agora_tmp.directory("store-test-"))
PATH = TMP / "t.pickle"
LOG = store.Log(store.log_path(PATH))
D, R = roomworld.build()
W = D.world


def be(me):
    per = D._per = getattr(D, "_per", None) or {}
    W.me = me
    if me not in per:
        per[me] = ({}, {W.root}, len(W.events))
    D.seen, D.open, D.last_event_seen = per[me]
    D._window = ""


def keep(me):
    D._per[me] = (D.seen, D.open, D.last_event_seen)


def run(me, *lines, press=None):
    """Lines as one reply of `me`, each one record at most. -> the last line's outcome."""
    be(me)
    token, last = uuid.uuid4().hex, None
    for line in lines:
        ctx = store.begin(D, PATH)
        r = D.dispatch("desk", {"line": line, "whole": True, "reply": token})
        text = r.get("text") or ""
        err = r.get("error") or (text if text.startswith(("ERR", "MISS")) else "")
        seq = store.commit(ctx, D, line, me, press)
        last = SimpleNamespace(line=line, text=text, error=err, seq=seq, made=W.last_created)
        if err:
            break
    keep(me)
    return last


def ok(me, *lines):
    r = run(me, *lines)
    assert not r.error, (r.line, r.error)
    return r


def rec(seq):
    return LOG.find(lambda r: r["seq"] == seq)


def facts(seq):
    return [(t, a) for t, a, _v in store.facts_of(rec(seq))]


def size(seq):
    return len(json.dumps(rec(seq), ensure_ascii=False).encode("utf-8"))


def subj(nid):
    return W.nodes[nid]["subject"]


def q(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def agrees(label):
    good, lines = store.check(W, LOG)
    check(label, good, "\n".join(lines))


BOARD, LOUNGE, TALK = R.BOARD, R.LOUNGE, R.TALK[R.LOUNGE]
CARD1, CARD2 = R.CARDS

# ---- the beginning ---------------------------------------------------------------------------------------------------
first = store.genesis(D, PATH, why="test")
check("genesis: one record holds the world as it is", first == 1 and len(store.facts_of(rec(1))) == len(store.flatten(W)))
agrees("the log replayed says what the world says, and the round trip holds, at the start")
try:
    store.genesis(D, PATH)
    check("a second genesis is refused", False)
except ValueError:
    check("a second genesis is refused", True)

# ---- what makes a record and what does not ---------------------------------------------------------------------------
n = LOG.head()[0]
for line in (f"look {BOARD} :3", f"read {CARD1}", "find card", "help look", f"verbs {CARD1}", f"history {CARD1}", f"where {CARD1}"):
    r = run("alex", line)
    check(f"a read makes no record: {line.split()[0]}", r.seq is None and not r.error, r.error)
r = run("pike", f"go {LOUNGE} :1")
check("walking makes no record (presence is not on the log), though the world's own list still gets a go event",
      r.seq is None and not r.error and W.events[-1]["verb"] == "go", r.error or r.seq)
r = run("mallory", f"do retitle {CARD1} title=Stolen")
check("a refusal makes no record", r.seq is None and bool(r.error), r.text)
check("so the log has not moved", LOG.head()[0] == n)

# ---- one prop: the record ---------------------------------------------------------------------------------------------
r = ok("alex", f"look {CARD1} :1", f"do prop {CARD1} status=doing")
one = rec(r.seq)
check("a prop is one record with one part and one fact, on the subject",
      len(one["parts"]) == 1 and one["parts"][0]["cause"] == "act" and facts(r.seq) == [(subj(CARD1), "prop:status")], one)
check("the record says who, the words, and the event it made",
      one["by"] == "alex" and one["words"] == f"do prop {CARD1} status=doing" and one["parts"][0]["e"] == W.events[-1]["id"]
      and one["parts"][0]["verb"] == "prop", one)
check("and what its author had seen of what it touched", {CARD1, subj(CARD1)} & set(one.get("saw") or {}), one.get("saw"))
check("a fact names the value before by its hash ('-' for none)", one["parts"][0]["facts"][0][2] == "-" and one["parts"][0]["facts"][0][3] == "doing", one)
r2 = ok("alex", f"do prop {CARD1} status=done")
check("the next fact on it names the value the first one left", rec(r2.seq)["parts"][0]["facts"][0][2] == store.h("doing"))

# ---- a chat line does not carry the chat ------------------------------------------------------------------------------
sizes, undo_copies = [], []
for i in range(160):
    who = ("sable", "juniper", "pike", "alex")[i % 4]
    r = ok(who, f'do append {TALK} line="line {i}: ' + "the couches hold a long conversation about nothing much " * 2 + '"')
    sizes.append(size(r.seq))
    undo_copies.append(len(json.dumps(W.events[-1].get("undo"), ensure_ascii=False)))
check("a chat line is one fact", [a.split(":")[0] for _t, a in facts(r.seq)] == ["line"], facts(r.seq))
check("the 160th line's record is no bigger than the 5th's (within 5%)", sizes[-1] <= sizes[4] * 1.05, (sizes[4], sizes[-1]))
check("where the world's own event kept a copy of the whole chat, 20 times the size by now",
      undo_copies[-1] > 20 * sizes[-1] and undo_copies[-1] > 10 * undo_copies[4], (undo_copies[4], undo_copies[-1], sizes[-1]))
print(f"     a line's record: {sizes[4]} bytes at line 5, {sizes[-1]} at line 160; the event's undo copy: {undo_copies[4]} then {undo_copies[-1]} bytes")

# ---- every kind of change ---------------------------------------------------------------------------------------------
ok("alex", f"look {BOARD} :3")
r = ok("alex", f'do create {BOARD} kind=task title="Write the log" text="first line" status=open owner=alex')
TASK = r.made
check("a create is one record: the subject, its appearance, where it is and what it comes after",
      {"kind", "title", "text", "prop:status", "prop:owner", "type", "subject", "in", "after", "folded"} <= {a for _t, a in facts(r.seq)}, facts(r.seq))
ok("alex", f'do retitle {TASK} title="Write the log, slowly"')
ok("alex", f'do rewrite {TASK} text="first line\\nsecond line\\nthird line"')
ok("alex", f'do replace {TASK} old="second" new="2nd"')
ok("alex", f'do append {TASK} line="fourth line"')
ok("alex", f"do tag {TASK} add=store,log")
ok("alex", f"do tag {TASK} remove=log")
ok("alex", f"do due {TASK} on=2026-10-20")
r = ok("sable", f"read {TASK}", f'do comment {TASK} line="what about undo?"')
check("a comment is one fact, on the comment", [a.split(":")[0] for _t, a in facts(r.seq)] == ["comment"], facts(r.seq))
CID = facts(r.seq)[0][1].split(":")[1]
r = ok("alex", f"read {TASK}", f'do resolve {TASK} id={CID} line="by facts"')
check("resolving it changes that one fact", facts(r.seq) == [(subj(TASK), f"comment:{CID}")], facts(r.seq))
r = ok("alex", f"look {CARD2} :1", f"do link {TASK} to={CARD2} as=blocks")
check("a link is one fact, a thing of its own", [a for _t, a in facts(r.seq)] == ["link"], facts(r.seq))
LINK = facts(r.seq)[0][0]
r = ok("alex", f"do unlink {TASK} id={LINK}")
check("unlinking takes that fact away", rec(r.seq)["parts"][0]["facts"][0][:2] == [LINK, "link"] and len(rec(r.seq)["parts"][0]["facts"][0]) == 3, rec(r.seq))
ok("alex", f"do rekind {TASK} kind=note")
ok("alex", f"do rekind {TASK} kind=task")
ok("alex", f"do fold {TASK}")
ok("alex", f"do unfold {TASK}")
ok("alex", f"do prop {TASK} owner=sable priority=2")
ok("alex", f"do prop {TASK} remove=priority")
ok("alex", f"look {BOARD} :3")
r = ok("alex", f"do move {TASK} before={CARD1}")
check("a move in a flow is at most three facts (what each of three things comes after), not one per sibling",
      len(facts(r.seq)) <= 3 and {a for _t, a in facts(r.seq)} == {"after"}, facts(r.seq))
r = ok("alex", f"look {LOUNGE} :3", f"do move {TASK} into={R.SHELF}")
check("a move to another surface says where it is now", (TASK, "in") in facts(r.seq), facts(r.seq))
ok("alex", f"look {BOARD} :3", f"do move {TASK} into={BOARD}")
r = ok("alex", f'do group {BOARD} title="Done" as=column')
DONE = r.made
ok("alex", f"look {DONE} :1", f'do rename {DONE} title="Done lane"')
ok("alex", f"do prop {DONE} role=lane")
r = ok("alex", f"look {R.SHELF} :1", f"do untile {LOUNGE}")
ok("alex", f"look {LOUNGE} :3", f"do move {R.NOTE} to=40,60")
r = ok("alex", f"do resize {R.NOTE} to=300x200")
check("in a free surface a box is a fact someone chose", (R.NOTE, "box") in facts(r.seq), facts(r.seq))
ok("alex", f"do raise {R.NOTE}")
ok("alex", f"look {LOUNGE} :3", f"do tile {LOUNGE} as=column")
ok("alex", f"look {BOARD} :3", f"do sort {BOARD} by=title")
r = ok("alex", f'do create {BOARD} kind=note title="Scrap" text="to throw away"')
SCRAP = r.made
r = ok("alex", f"do remove {SCRAP}")
check("removing an appearance takes its facts away and leaves what it said", (SCRAP, "type") in facts(r.seq) and SCRAP not in W.nodes, facts(r.seq))
agrees("after every kind of change, the log replayed still says what the world says")

# ---- a rule: one record, the act and what it set off -------------------------------------------------------------------
ok("juniper", f"go {BOARD} :1", f"look {BOARD} :1", f"do create {BOARD} kind=surface title=Rules layout=column")
RULES = W.last_created
ok("juniper", f"look {RULES} :1", f"do create {RULES} kind=note tags=rule title={q('Done cards go to the Done lane')} "
   f"text={q(f'when kind:task,prop:status=done do move $item into={DONE}')}")
RULE = W.last_created
r = ok("alex", f"look {BOARD} :3", f'do create {BOARD} kind=task title="Ship it" text="x" status=open')
SHIP = r.made
before_ship = store.flatten(W)
r = ok("alex", f"do prop {SHIP} status=done")
ship = rec(r.seq)
causes = [p["cause"] for p in ship["parts"]]
check("marking a card done, with a rule that moves done cards: one record, the act then the rule",
      causes[0] == "act" and any(c == f"rule {RULE}" for c in causes[1:]) and W.nodes[SHIP]["parent"] == DONE, (causes, W.nodes[SHIP]["parent"]))
check("the rule's part holds the move's facts", any(p["cause"].startswith("rule") and [f[:2] for f in p["facts"] if f[1] == "in"] == [[SHIP, "in"]]
                                                   for p in ship["parts"]), ship)
SHIP_SEQ = r.seq

# ---- undo: a record put back whole by its facts -------------------------------------------------------------------------
def put_back(seq):
    """Put record `seq` back on a copy of the world -> the copy's facts. The world itself is not changed."""
    w2 = copy.deepcopy(W)
    plan = store.undo_plan(LOG, rec(seq), store.flatten(W))
    store.apply(w2, plan)
    return store.flatten(w2)


after_ship = put_back(SHIP_SEQ)
d = store.diff(before_ship, after_ship)
check("put back whole: the card is open again AND back on the Board, as before the command", not d, d[:8])

kinds = []
for label, me, lines in (
        ("a prop", "alex", [f"look {CARD2} :1", f"do prop {CARD2} status=waiting"]),
        ("a retitle", "alex", [f"do retitle {CARD2} title={q('Card two, renamed')}"]),
        ("a rewrite", "alex", [f"read {CARD2}", f"do rewrite {CARD2} text={q('all new text')}"]),
        ("a chat line", "pike", [f"do append {TALK} line={q('one more')}"]),
        ("a comment", "sable", [f"read {CARD2}", f"do comment {CARD2} line={q('hm')}"]),
        ("a tag", "alex", [f"do tag {CARD2} add=x"]),
        ("a due date", "alex", [f"do due {CARD2} on=2026-11-01"]),
        ("a create", "alex", [f"look {BOARD} :3", f"do create {BOARD} kind=note title=New text=t"]),
        ("a move in a flow", "alex", [f"look {BOARD} :3", f"do move {CARD2} before={CARD1}"]),
        ("a move to another surface", "alex", [f"look {R.SHELF} :1", f"do move {CARD2} into={R.SHELF}"]),
        ("a link", "alex", [f"look {CARD1} :1", f"do link {CARD2} to={CARD1} as=refers"]),
        ("a rekind", "alex", [f"do rekind {CARD2} kind=task"]),
        ("a new surface", "alex", [f"look {BOARD} :3", f"do group {BOARD} title=Later as=column"])):
    for line in lines[:-1]:
        ok(me, line)
    was = store.flatten(W)
    old_world = copy.deepcopy(W)
    r = ok(me, lines[-1])
    back = put_back(r.seq)
    d = store.diff(was, back)
    check(f"{label}, put back by its facts, is the world before it", not d, d[:6])
    # and the old undo, on the same event, arrives at the same facts (one event: the two must agree)
    w3 = copy.deepcopy(W)
    try:
        w3.undo(rec(r.seq)["parts"][0]["e"])
        d3 = store.diff(back, store.flatten(w3))
    except Exception as e:      # noqa: BLE001
        d3 = [("the verb's own undo refused", str(e), "")]
    if d3:
        kinds.append((label, d3))

# found 7 Oct by this comparison: the verb's own undo of a move to another surface restores the card's old box, and the
# flow it returns to has been laid out again since, so the card lands in another place in the order. By facts it comes
# back after the thing it came after. Any other disagreement is news.
check("the verbs' own undos arrive at the same facts, but for the one known difference (a move to another surface: the old undo loses the place in the order)",
      [k for k, _d in kinds] == ["a move to another surface"] and all(a_ == "after" for _t, a_, _v in kinds[0][1]), kinds)

# scenario 1: an old change undone after later ones on the same thing
ok("alex", f"look {CARD1} :1")
r1 = ok("alex", f"do retitle {CARD1} title={q('Card one, by Alex')}")
ok("sable", f"look {CARD1} :1", f"do prop {CARD1} owner=sable")
try:
    copy.deepcopy(W).undo(rec(r1.seq)["parts"][0]["e"])
    old_refused = False
except Exception:      # noqa: BLE001
    old_refused = True
back = put_back(r1.seq)
check("scenario 1: Alex retitles, Sable sets a prop, Alex's retitle is put back; the title returns and Sable's prop stays",
      back[(subj(CARD1), "title")] == "Card one" and back[(subj(CARD1), "prop:owner")] == "sable" and old_refused,
      (back[(subj(CARD1), "title")], old_refused))
r2 = ok("sable", f"look {CARD1} :1", f"do retitle {CARD1} title={q('Card one, by Sable')}")
try:
    put_back(r1.seq)
    check("but once the title itself was changed again, putting the first back is refused, naming the fact", False)
except store.CannotUndo as e:
    check("but once the title itself was changed again, putting the first back is refused, naming the fact", "title" in str(e), e)

# scenario 2: a chat line someone answered
p = ok("pike", f'do append {TALK} line="shall we move the couches?"')
MID = facts(p.seq)[0][1].split(":")[1]
ok("juniper", f'do append {TALK} line="yes, to the window" reply_to={MID}')
try:
    put_back(p.seq)
    check("scenario 2: a line someone answered cannot be put back (the answer would point at nothing)", False)
except store.CannotUndo as e:
    check("scenario 2: a line someone answered cannot be put back (the answer would point at nothing)", "answers" in str(e) or "replies" in str(e), e)
p2 = ok("pike", f'do append {TALK} line="never mind"')
check("   a line no one answered can", (subj(TALK), facts(p2.seq)[0][1]) not in put_back(p2.seq))

# something made later lives in what a record made
g = ok("alex", f"look {BOARD} :3", f"do group {BOARD} title=Shelf2 as=column")
ok("sable", f"look {g.made} :1", f"do create {g.made} kind=note title=Inside text=t")
try:
    put_back(g.seq)
    check("a surface someone has since put a note in cannot be put back (the note would be nowhere)", False)
except store.CannotUndo as e:
    check("a surface someone has since put a note in cannot be put back (the note would be nowhere)", "points at" in str(e), e)

agrees("after the undo trials (all on copies), the log still says what the world says")

# ---- something changes the world without a record ------------------------------------------------------------------------
# 14 Oct (Snappy Desk, stage 1): a command in the process that wrote the last record begins from the facts it kept, so a
# change made in that process behind the log's back is found when a quick record is checked against the whole world:
# every 20th record, or each one with DESK_LOG_VERIFY=1 (as here). A world loaded from its file is checked the whole way.
os.environ["DESK_LOG_VERIFY"] = "1"
W.subjects[subj(CARD2)]["title"] = "changed behind the log's back"
n = LOG.head()[0]
r = ok("alex", f"look {CARD1} :1", f"do prop {CARD1} seen=yes")
out = rec(r.seq - 1)
check("a change made outside any command is written first, as its own record, at the next command",
      r.seq == n + 2 and out["parts"][0]["cause"] == "outside" and [f[:2] for f in out["parts"][0]["facts"]] == [[subj(CARD2), "title"]], out)
agrees("so the log never falls behind the world")

# ---- a write cut short -----------------------------------------------------------------------------------------------
with open(LOG.path, "ab") as f:
    f.write(b'{"seq": 99999, "shape": 1, "state": "dead", "parts": [{"cause": "act", "fa')
n = len(list(LOG.records()))
r = ok("alex", f"do prop {CARD1} seen=again")
check("half a line at the end of the log (a write cut short) is dropped; the next record follows the last whole one",
      len(list(LOG.records())) == n + 1 and r.seq == n + 1, (n, r.seq, len(list(LOG.records()))))
agrees("and the log is whole")

# ---- a record tampered with ------------------------------------------------------------------------------------------
tampered = TMP / "tampered.log.jsonl"
lines = LOG.path.read_text(encoding="utf-8").splitlines()
k = next(i for i, l in enumerate(lines) if '"status", "-", "doing"' in l or '"doing"' in l and i > 0)
lines[k] = lines[k].replace('"doing"', '"dozing"')
tampered.write_text("\n".join(lines) + "\n", encoding="utf-8")
good, why = store.check(W, store.Log(tampered))
check("a value changed in an old record is found: the next fact on it says what it was before, and the digests stop agreeing",
      not good and any("record" in x for x in why), why[:6])

# ---- the world at an earlier record ----------------------------------------------------------------------------------
then = LOG.value_at((subj(CARD1), "title"), r1.seq)
check("what a fact said at an earlier record is read from the log", then == "Card one, by Alex" and LOG.value_at((subj(CARD1), "title"), r1.seq - 1) == "Card one", then)

# ---- a document as blocks ---------------------------------------------------------------------------------------------
ok("alex", f"look {R.HOME} :2", f'do create {R.HOME} kind=surface title="A shared document" layout=column')
DOC = W.last_created
ok("alex", f"look {DOC} :1", f"do prop {DOC} role=doc")
blocks = []
for i, para in enumerate(("Why a log.", "What a fact is.", "What a record is.", "What stays off it.", "What comes next.")):
    ok("alex", f"look {DOC} :1", f"do create {DOC} kind=note title=p{i} text={q(para)}")
    blocks.append(W.last_created)
ok("sable", f"look {DOC} :3", f"read {blocks[1]}")
ok("juniper", f"look {DOC} :3", f"read {blocks[3]}")
a = ok("sable", f"do rewrite {blocks[1]} text={q('A fact is one thing said of one thing.')}")
b = ok("juniper", f"do rewrite {blocks[3]} text={q('What a person saw, where they stand, and what can be worked out again.')}")
check("two people in different paragraphs: neither is refused, and their records share no fact",
      not a.error and not b.error and not set(facts(a.seq)) & set(facts(b.seq)), (facts(a.seq), facts(b.seq)))
c = ok("pike", f"look {DOC} :3", f"do create {DOC} kind=note title=p1b text={q('An aspect is what is said.')}")
NEW = c.made
m = ok("pike", f"do move {NEW} after={blocks[1]}")
check("a paragraph put between two others changes what two things come after, not the paragraphs around them",
      {a_ for _t, a_ in facts(m.seq)} == {"after"} and len(facts(m.seq)) <= 3
      and [k["id"] for k in W.children(DOC)][:3] == [blocks[0], blocks[1], NEW], (facts(m.seq), [k["id"] for k in W.children(DOC)]))
s = ok("sable", f"do rewrite {blocks[1]} text={q('A fact is one thing said of one thing, at one moment.')}")
check("and the writer of the paragraph above it goes on writing: the insert did not stale their paragraph", not s.error, s.error)
cm = ok("juniper", f"read {blocks[1]}", f"do comment {blocks[1]} line={q('at one record, not one moment?')}")
mv = ok("pike", f"look {DOC} :3", f"do move {blocks[1]} after={blocks[4]}")
check("a comment stays on its paragraph when the paragraph moves (it is a fact of the paragraph, not of a place)",
      any(c_["text"].startswith("at one record") for c_ in W.subjects[subj(blocks[1])]["comments"])
      and [k["id"] for k in W.children(DOC)][-1] == blocks[1], [k["id"] for k in W.children(DOC)])

# ---- undo through the desk: `undo <event>` in a world with a log -------------------------------------------------------
def ev_of(seq, k=0):
    return rec(seq)["parts"][k]["e"]


r = ok("alex", f"look {BOARD} :3", f'do create {BOARD} kind=task title="Ship again" text="x" status=open')
SHIP2 = r.made
was = store.flatten(W)
d1 = ok("alex", f"do prop {SHIP2} status=done")
check("(a rule moved it to the Done lane)", W.nodes[SHIP2]["parent"] == DONE)
u = run("alex", f"undo {ev_of(d1.seq)}")
check("undo <event>, through the desk: the command and what its rule did are put back whole",
      not u.error and not store.diff(was, store.flatten(W)) and "rule consequence" in u.text, u.error or (u.text, store.diff(was, store.flatten(W))[:6]))
check("   the world's own events say so (each is marked undone) and the undo is itself a record of the facts it put back",
      all(W.event_by_id(p["e"]).get("undone") for p in rec(d1.seq)["parts"]) and u.seq
      and {a_ for _t, a_ in facts(u.seq)} >= {"prop:status", "in"}, (u.seq, u.seq and facts(u.seq)))
u2 = run("alex", f"undo {ev_of(d1.seq)}")
check("   a second undo of it is refused", bool(u2.error) and "already undone" in u2.error, u2.error or u2.text)

ok("alex", f"look {CARD1} :1")
t1 = ok("alex", f"do retitle {CARD1} title={q('Card one, once more')}")
ok("sable", f"look {CARD1} :1", f"do prop {CARD1} owner=juniper")
u = run("alex", f"undo {ev_of(t1.seq)}")
check("scenario 1 through the desk: Alex's retitle comes back though Sable has since set a prop on the card",
      not u.error and W.subjects[subj(CARD1)]["title"] == "Card one, by Sable" and W.subjects[subj(CARD1)]["props"]["owner"] == "juniper",
      u.error or W.subjects[subj(CARD1)]["title"])
p = ok("pike", f'do append {TALK} line="shall we paint the wall?"')
MID2 = facts(p.seq)[0][1].split(":")[1]
ok("juniper", f'do append {TALK} line="blue" reply_to={MID2}')
u = run("pike", f"undo {ev_of(p.seq)}")
check("scenario 2 through the desk: the answered line is refused, saying which command and why",
      bool(u.error) and "answers" in u.error and "shall we paint" in u.error, u.error or u.text)
b = ok("pike", f'do append {TALK} line="(never mind the wall)"')
u = run("pike", "undo")
check("a bare undo puts back my latest command", not u.error and "never mind the wall" not in W.subjects[subj(TALK)]["text"], u.error or u.text)
old_event = next(e for e in W.events if e["verb"] == "prop" and e["by"] == "jeff" and not e.get("undone") and e["target"] == R.corner["pike"]
                 and "wake" in (e.get("args") or {}))
ok("jeff", f"look {R.corner['pike']} :1")
u = run("jeff", f"undo {old_event['id']}")
check("an event older than the log has no record: it is undone the verb's own way, and that undo is recorded as facts",
      not u.error and u.seq and "wake" not in (W.nodes[R.corner["pike"]].get("props") or {}), u.error or u.text)
agrees("after undos through the desk, the log says what the world says")

# ---- two people in one text ----------------------------------------------------------------------------------------------
PLAN = "Monday: the log\nTuesday: the bridge\nWednesday: undo\nThursday: the fence\nFriday: the flip\nSaturday: rest"
r = ok("alex", f"look {BOARD} :3", f"do create {BOARD} kind=note title=Plan text={q(PLAN)}")
NOTE = r.made
ok("sable", f"read {NOTE}")
ok("juniper", f"read {NOTE}")
a = run("sable", f"do replace {NOTE} old={q('Tuesday: the bridge')} new={q('Tuesday: the bridge, slowly')}")
b = run("juniper", f"do replace {NOTE} old={q('Friday: the flip')} new={q('Friday: the flip, if the log holds')}")
text = W.subjects[subj(NOTE)]["text"]
check("Sable changes line 2; Juniper, who read it before that, changes line 5: hers is joined, not refused, and both are in the text",
      not a.error and not b.error and "the bridge, slowly" in text and "if the log holds" in text and "~ joined" in b.text, b.error or b.text)
check("   she is told so, and that she has not read Sable's line", "You have not read theirs" in b.text and "line 2" in b.text, b.text)
check("   and whose change it was and which event (Juniper and Sable, a3474: 'theirs' named no one)",
      re.search(r"by [Ss]able e" + chr(92) + "d+", b.text) is not None, b.text)
mine = PLAN.replace("Friday: the flip", "Friday: the flip, if the log holds").replace("Saturday: rest", "Saturday: rest, properly")
c = run("juniper", f"do rewrite {NOTE} text={q(mine)}")
text = W.subjects[subj(NOTE)]["text"]
check("she then rewrites the whole text from what she remembers (without Sable's line): joined again, and Sable's line is still there",
      not c.error and "the bridge, slowly" in text and "rest, properly" in text and text.count("if the log holds") == 1, c.error or text)
d = run("pike", f"read {NOTE}")
ok("sable", f"read {NOTE}", f"do replace {NOTE} old={q('Wednesday: undo')} new={q('Wednesday: undo, whole')}")
e = run("pike", f"do replace {NOTE} old={q('Wednesday: undo')} new={q('Wednesday: undo by facts')}")
check("the same line changed by both is refused as before, now naming the line",
      bool(e.error) and "stale" in e.error and "both changed line 3" in e.error and "undo by facts" not in W.subjects[subj(NOTE)]["text"], e.error or e.text)
f_ = run("pike", f"read {NOTE}", f"do replace {NOTE} old={q('Wednesday: undo, whole')} new={q('Wednesday: undo, whole, by facts')}")
check("   and after reading it again, it lands", not f_.error and "whole, by facts" in W.subjects[subj(NOTE)]["text"], f_.error)

LENS = 'root : column\n  head : text "A shared document"\n  body : column\n    of in:%s\n    each para\n  foot : text "end"\npara : column\n  t : text "$text"' % DOC
r = ok("alex", f"look {R.HOME} :2", f"do create {R.HOME} kind=note tags=lens title=doc-reader text={q(LENS)}")
LENS_ID = r.made
check("(the lens compiles)", "compiles" in r.text, r.text)
ok("sable", f"read {LENS_ID}")
ok("juniper", f"read {LENS_ID}")
a = run("sable", f"do replace {LENS_ID} old={q('head : text \"A shared document\"')} new={q('head : text \"A document, shared\"')}")
b = run("juniper", f"do replace {LENS_ID} old={q('foot : text \"end\"')} new={q('foot : text \"the end\"')}")
text = W.subjects[subj(LENS_ID)]["text"]
check("a lens, two editors, two parts: both land, and the lens still compiles",
      not a.error and not b.error and "A document, shared" in text and '"the end"' in text and "~ joined" in b.text and "compiles" in b.text and "only the scene shows" in b.text, b.error or b.text)
ok("sable", f"read {LENS_ID}")
ok("juniper", f"read {LENS_ID}")
a = run("sable", f"do replace {LENS_ID} old={q('  t : text \"$text\"')} new={q('  words : text \"$text\"')}")
b = run("juniper", f"do replace {LENS_ID} old={q('    each para')} new={q('    each para\\n    on click do read $item')}")
check("(both of those land too, on different lines)", not a.error and not b.error, (a.error, b.error))
ok("sable", f"read {LENS_ID}")
ok("juniper", f"read {LENS_ID}")
now = W.subjects[subj(LENS_ID)]["text"]
renamed = now.replace("each para", "each block").replace("para : column", "block : column")
a = run("sable", f"do rewrite {LENS_ID} text={q(renamed)}")
check("(Sable renames the part and its one caller in one rewrite: the lens compiles)", not a.error and "compiles" in a.text and "does not" not in a.text, a.error or a.text[-300:])
b = run("juniper", f"do replace {LENS_ID} old={q('  foot : text \"the end\"')} "
        f"new={q('  foot : column\\n    of in:' + DOC + '\\n    each para')}")
text = W.subjects[subj(LENS_ID)]["text"]
check("different lines, but together they do not compile (Juniper's new lines call the part by the name Sable just changed): hers is refused, and says why",
      bool(b.error) and "together the lens does not compile" in b.error and "each para" not in text, b.error or b.text[-400:])
c2 = run("juniper", f"read {LENS_ID}", f"do replace {LENS_ID} old={q('  foot : text \"the end\"')} "
         f"new={q('  foot : column\\n    of in:' + DOC + '\\n    each block')}")
check("   having read Sable's version, she calls it by its new name and it lands", not c2.error and "compiles" in c2.text and "does not" not in c2.text,
      c2.error or c2.text[-300:])
agrees("after joining texts, the log says what the world says")

# ---- found on frontier's own log, 7 Oct: a line added to a 40 KB notebook wrote the notebook again ---------------------------
BOOK = "\n".join(f"entry {i}: " + "what I did and what I found, at some length, " * 3 for i in range(300))
r = ok("juniper", f"look {BOARD} :3", f"do create {BOARD} kind=note title=Notebook text={q(BOOK)}")
NB = r.made
a = ok("juniper", f"do append {NB} line={q('entry 300: one more line')}")
b = ok("juniper", f"do replace {NB} old={q('entry 150: ')} new={q('ENTRY 150 (revised): ')}")
check(f"a line added to a {len(BOOK) // 1000} KB note is a record of under 1 KB (the change, not the note), and so is one passage replaced",
      size(a.seq) < 1000 and size(b.seq) < 1000 and "$splice" in json.dumps(rec(a.seq)), (size(a.seq), size(b.seq)))
agrees("   and the log replayed still says what the world says")
was = store.flatten(W)
c = ok("juniper", f"do append {NB} line={q('entry 301: to be taken back')}")
u = run("juniper", f"undo {ev_of(c.seq)}")
check("   a change written that way is put back like any other", not u.error and not store.diff(was, store.flatten(W)), u.error or u.text)
check("   and what the text said at an earlier record is still read from the log",
      LOG.value_at((subj(NB), "text"), a.seq).endswith("entry 300: one more line") and "ENTRY 150" not in LOG.value_at((subj(NB), "text"), a.seq))

# ---- found in the Writing room, 7 Oct (Juniper, e6201): a rewrite with no text= emptied the paragraph and said ok --------
ok("juniper", f"read {NOTE}")
had = W.subjects[subj(NOTE)]["text"]
r = run("juniper", f"do rewrite {NOTE} title={q('A plan')}")
check("a rewrite with no text= is refused and names retitle; the text is as it was, and no record is made",
      bool(r.error) and "retitle" in r.error and W.subjects[subj(NOTE)]["text"] == had and r.seq is None, r.error or r.text)
r = run("juniper", f'do rewrite {NOTE} text=""')
check('   text="" is how a text is emptied on purpose, and undo puts it back', not r.error and W.subjects[subj(NOTE)]["text"] == ""
      and not run("juniper", "undo").error and W.subjects[subj(NOTE)]["text"] == had, r.error or W.subjects[subj(NOTE)]["text"][:80])

agrees("at the end: every record replayed says what the world says; a world rebuilt from its facts says the same")
st = store.stats(LOG)
print(f"     {st['records']} records ({st['by kind']}); a command's record is {st['mean command bytes']} bytes on average; "
      f"the genesis is {st['bytes by kind'].get('genesis', 0)} bytes")
print(f"     derived, re-derived from facts: {store.derived_gap(W)}")

QUICK = "--quick" in sys.argv
if not QUICK:
    import test_store_live   # noqa: E402,F401  (the CLI and deskd parts: real processes, a throwaway world)
    fails += test_store_live.fails

import shutil  # noqa: E402
shutil.rmtree(TMP, ignore_errors=True)
print()
print("FAILED: " + "; ".join(fails) if fails else "all passed")
sys.exit(1 if fails else 0)
