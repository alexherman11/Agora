"""test_waiting (a1062, talk step 3e; a1566): a resident's @ knocks; a line kept for a resident comes first, marked.

    python test_waiting.py [world]      default frontier-try; it CHANGES the world it is given, so give it a copy

a1062 held a resident's @name for the named one's next wake, and made waking a second act; a1566 (Alex, e3710, e3802:
'a resident's @ should knock') reverses the hold: an @name or @everyone from anyone wakes a resting resident now, the
line still first in that wake under 'for you while you rested', and the speaker's receipt says whom the line took
('to: pike', 'to: nobody') and per name what happened ('Pike: woken'). An @ counts only outside quotes and backticks
(a916; Sable's scope change to a1566, matching a1570's addressing). What still waits: a resident's plain line in
another's own corner chat (a visitors' book), and anything for someone asleep (want=rest). `wake <name>` still calls
without a line.
a2662: one reading of @. The knock reads a line's stored to= (a1581), never its words; the receipt says 'to:' once
(the world's) and then a line per name: resident, person, agent, a private chat they aren't a member of, or no one by that name.

It drives House.step, the house's own pass, with stand-in residents that keep what the house would send instead of
writing to a claude process (no model is called, no worker is started). The house's heartbeat is written as it runs,
so the desk's receipts read the same presence the live house would give them. The world needs three residents
(pike, juniper, sable) and the rooms of frontier; a person is recorded as the Desktop's person=alex.
"""
import os
import re
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"
os.environ.setdefault("HOUSE_CLAUDE", "claude")     # the house looks for a claude binary; none is started here
import house   # noqa: E402

WORLD = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "frontier-try"
if not WORLD.endswith("-try") and "--yes" not in sys.argv:
    sys.exit(f"test_waiting changes the world it runs on; {WORLD} is not a -try copy (add --yes to insist)")
shutil.rmtree(house.STATE / WORLD, ignore_errors=True)      # a clean house for this copy: no cursors from before


class Stand(house.Resident):
    """A resident whose process is always up and never busy unless the test says so; what it is sent is kept."""
    def __init__(self, h, rid):
        super().__init__(h, rid)
        self.sent, self.up = [], True

    def start(self, model):
        self.busy, self.up = False, True

    def stop(self):
        self.up = False

    def alive(self):
        return self.up

    def turns_ended(self):
        return []

    def send(self, text, kind="news", carry=None):
        self.sent.append((kind, text))
        self.state["last_sent"] = house.now()


house.Resident = Stand
H = house.House(WORLD)
H.workshop.step = lambda *a, **k: None               # no workers in a test
w = H.load()
by_actor = {(n.get("props") or {}).get("actor"): fid for fid, n in H.corners(w).items()}
PIKE, JUNIPER, SABLE = by_actor["pike"], by_actor["juniper"], by_actor["sable"]


def app_titled(title):
    return next(a["id"] for a in w.nodes.values() if a["type"] == "appearance"
                and (w.subjects.get(a.get("subject")) or {}).get("title") == title)


LOUNGE = app_titled("Lounge talk")
BOOK = (w.nodes[PIKE].get("props") or {}).get("talk")                 # Pike's visitors' book
DESKTOP = next(f for f, n in w.nodes.items() if n["type"] == "surface" and n["title"] == "Desktop")
fails = []


def check(name, ok, detail=""):
    ok = ok and "the desk process failed" not in str(detail)
    print(("ok   " if ok else "FAIL ") + name + ("" if ok and "--show" not in sys.argv else f"\n     {str(detail)[:1800]}"))
    if not ok:
        fails.append(name)


def res(rid):
    return H.residents[rid]


def sent(rid):
    """What the house sent this resident since the last call, and forget it."""
    out = "\n---\n".join(t for _, t in res(rid).sent)
    res(rid).sent.clear()
    return out


def say(who, line, where=LOUNGE):
    return H.act(who, f"do append {where} line={house.json.dumps(line)}")


def rest(rid, seconds):
    H.rest(res(rid), seconds, "a test")
    res(rid).state["last_turn"] = house.now()
    H.step()
    res(rid).sent.clear()


OLD = "they'll see this when they wake"     # a1062's receipt; untrue since a1566, so never said
t0 = time.time()
out = H.act("alex", f"look {DESKTOP} :1; do prop {DESKTOP} person=alex")
check("the Desktop records its person (person=alex)", "person=alex" in out or "already has that" in out, out)
H.step()                                    # everyone arrives: each resident's first wake
H.step()
for rid in H.residents:
    res(rid).sent.clear()

# 1. Pike rests an hour; Juniper's @pike wakes him now; the line comes first, marked for him
rest(PIKE, 3600)
got = say("juniper", "@pike the lens you asked about is on the board")
check("Juniper's receipt: 'to: pike', 'Pike: woken', and not a1062's wording",
      "to: pike" in got and "Pike: woken" in got and OLD not in got, got)
H.step()
got = sent(PIKE)
lines = got.splitlines()
check("Juniper's @pike reaches Pike at once, and his rest ends", "@pike the lens" in got
      and not res(PIKE).state.get("rest_until") and not res(PIKE).state.get("for_you"), (got[:600], res(PIKE).state.get("rest_until")))
check("a3150: the wake's first line names the line that caused it, by its ids",
      bool(lines) and re.fullmatch(r"~ woken by juniper's line m\d+ \(e\d+\) in \"Lounge talk\"", lines[0]), got[:600])
check("the line comes next, under 'for you while you rested', with its chat and time",
      len(lines) > 2 and lines[1] == "for you while you rested (1):" and "Lounge talk" in lines[2]
      and "@pike the lens" in lines[2] and re.search(r"~ \d\d:\d\d in chat", lines[2]), got[:600])

# 1b. an @ inside quotes or backticks knocks no one, and the receipt says whom it took (Sable, a1566 scope change)
rest(PIKE, 3600)
for line in ['Sable wrote "@pike (e3305) see the board" yesterday', "the `@pike` handle is the old one",
             "she said '@everyone, stand up' and left"]:
    got = say("juniper", line)
    check(f"a quoted @ takes no one, and names no mention (it was quoted on purpose): {line[:30]}...",
          re.search(r"line m\d+ · to: nobody\n", got) is not None and "woken" not in got and "mention" not in got, got)
# 1c. a2715: an @ after the header is a mention: it knocks no one, and the receipt says so at once
got = say("juniper", 'about "the board", @pike, look')
check("a mid-line @pike: 'to: nobody', the receipt names the mention, nobody woken",
      "to: nobody; a mid-line @ is a mention (@pike); put names first to call them" in got and "woken" not in got, got)
H.step()
check("and Pike is not woken, nor anything kept for him", not res(PIKE).sent and not res(PIKE).state.get("for_you")
      and res(PIKE).state.get("rest_until"), (sent(PIKE)[:300], res(PIKE).state.get("for_you")))
got = say("juniper", '@pike, about "the board": look')
check("an @ opening a line that also quotes: 'to: pike', woken", "to: pike" in got and "Pike: woken" in got, got)
H.step()
check("and it wakes him", "about" in sent(PIKE) and not res(PIKE).state.get("rest_until"), res(PIKE).state)
got = say("juniper", "mail me at someone@example.org")
check("an @ inside a word names no one: 'to: nobody', no mention to teach", "to: nobody" in got and "mention" not in got, got)

# 2. a resident's plain line in Pike's own book is a note at the door: it waits; wake pike calls him for it
if BOOK:
    rest(PIKE, 0)
    got = say("juniper", "left you the notes from this morning", BOOK)
    # a2662: 'to:' is the line's stored address (nobody: it names no one); Pike's own line says why it is his
    check("a plain book line: 'to: nobody', Pike resting, the line waits, with how to call him", "to: nobody" in got
          and re.search(r"Pike: resting, until \S+ at the latest; a plain line", got) and "wake pike" in got and OLD not in got, got)
    H.step()
    check("the book line waits for his wake", not res(PIKE).sent
          and any("left you the notes" in h["text"] for h in res(PIKE).state.get("for_you") or []), res(PIKE).state.get("for_you"))
    got = H.act("juniper", "wake pike")
    check("wake pike: signed by Juniper, the house calls them now", re.search(r"ok e\d+: you wake Pike", got) and "calls them now" in got, got)
    ev = H.load().events[-1]
    check("the wake is a call= on Pike's corner, by juniper, via=wake", ev["verb"] == "prop" and ev["target"] == PIKE
          and ev["by"] == "juniper" and ev.get("via") == "wake" and ev["args"].get("call") == "juniper", ev)
    H.step()
    got = sent(PIKE)
    check("Pike's wake names Juniper and the line she left", got.startswith("~ juniper woke you (wake, e")
          and "for the line they left you:" in got.splitlines()[0] and "notes from this morning" in got.splitlines()[1], got[:600])
    check("the call is cleared once delivered", "call" not in (H.load().nodes[PIKE].get("props") or {}), H.load().nodes[PIKE].get("props"))

    # a timed rest's end: a held line is first, after who he is and how long he rested, before the wake's own look
    rest(PIKE, 3600)
    say("juniper", "the second page too", BOOK)
    H.step()
    res(PIKE).state["rest_until"] = house.now() - 1
    H.step()
    got = sent(PIKE)
    lines = got.splitlines()
    check("at a timed wake: 'for you while you rested' comes first, before the wake's own look",
          len(lines) > 3 and lines[0].startswith("You are pike.") and lines[1].startswith("(you rested")
          and lines[2] == "for you while you rested (1):" and "the second page too" in lines[3], got[:900])

    # an @pike in his book knocks, like anywhere else; a quoted one in his book doesn't
    rest(PIKE, 3600)
    say("juniper", "the tag reads `@pike`", BOOK)
    H.step()
    check("a quoted @ in his own book doesn't knock", not res(PIKE).sent, sent(PIKE))
    got = say("juniper", "@pike one more thing", BOOK)
    check("an @ in his own book: 'Pike: woken'", "Pike: woken" in got, got)
    H.step()
    check("and he is woken", "one more thing" in sent(PIKE) and not res(PIKE).state.get("rest_until"), res(PIKE).state)
else:
    print("skip Pike's corner has no talk= chat")
got = H.act("juniper", "wake juniper")
check("waking yourself is refused", "ERR" in got and "you are awake" in got, got)
got = H.act("juniper", "wake nobody")
check("waking no one is refused, and says why", "ERR" in got and "no resident called 'nobody'" in got, got)

# 3. a person's @pike wakes Pike at once, as before
rest(PIKE, 3600)
got = say("alex", "@pike can you look at this now?")
check("Alex's receipt: 'Pike: woken'", "to: pike" in got and "Pike: woken" in got, got)
H.step()
got = sent(PIKE)
check("Alex's @pike reaches Pike at once, and his rest ends", "(to you)" in got and "can you look at this now" in got
      and not res(PIKE).state.get("rest_until"), got[:600])

# 4. to someone in a turn: the receipt says so, and the line goes with what reaches him when it ends
res(PIKE).busy = True
H.step()                                                   # the heartbeat now says Pike is working
got = say("juniper", "@pike while you're at it")
check("to someone in a turn: 'Pike: in a turn; your line goes with what reaches them when it ends'",
      "Pike: in a turn; your line goes with what reaches them when it ends" in got and "woken" not in got, got)
res(PIKE).busy = False
H.after_turn(H.load(), res(PIKE), H.load().nodes[PIKE], "pike", "Thinking, nothing done yet.")
got = sent(PIKE)
check("it goes with what reaches him when his turn ends, marked to you, not kept", "(to you)" in got
      and "while you're at it" in got and not res(PIKE).state.get("for_you"), got[:600])

# 5. a person's line in Pike's own chat wakes him at once; a held book line comes first
rest(PIKE, 3600)
if BOOK:
    say("juniper", "a plain note for later", BOOK)
    H.step()
TALK = app_titled("Talk with Alex, Pike")
got = say("alex", "are you there?", TALK)
check("Alex's line in Pike's own chat: 'Pike: woken'", "Pike: woken" in got, got)
H.step()
got = sent(PIKE)
check("Alex's line in Pike's own chat wakes him at once, the held book line first", "are you there?" in got
      and (not BOOK or got.index("for you while you rested") < got.index("are you there?")), got[:800])

# 6. @everyone wakes each resting resident it reaches, each named in the receipt
rest(PIKE, 3600)
rest(SABLE, 3600)
got = say("juniper", "@everyone the suite is green again")
check("@everyone: 'to: everyone', and the receipt names each, woken", got.count("to: everyone") == 1
      and "Pike: woken" in got and "Sable: woken" in got and OLD not in got, got)
H.step()
p, s = sent(PIKE), sent(SABLE)
check("@everyone reaches both now, first and marked", "suite is green" in p and "suite is green" in s
      and all(x.startswith("~ woken by juniper's line m") and x.splitlines()[1].startswith("for you while you rested")
              for x in (p, s)), (p[:300], s[:300]))

# 7. an agent's (no corner, no person record) @pike knocks too; a plain line wakes no one and is not marked for him
rest(PIKE, 3600)
got = say("juniper", "a plain line in the lounge")
check("a line with no @ that calls no one: 'to: nobody' once, and nothing about anyone",
      got.count("to: nobody") == 1 and "inside quotes" not in got and "woken" not in got and "Pike:" not in got, got)
H.step()
check("the plain line wakes no one", not res(PIKE).sent and res(PIKE).state.get("rest_until"), sent(PIKE))
got = say("claude", "@pike a note from outside")
check("an agent's @pike: 'Pike: woken'", "Pike: woken" in got, got)
H.step()
got = sent(PIKE)
check("the agent's line first and marked; the plain lounge line after it, not marked",
      got.startswith("~ woken by claude's line m") and got.splitlines()[1] == "for you while you rested (1):"
      and "a note from outside" in got.splitlines()[2]
      and got.index("a note from outside") < got.index("a plain line in the lounge"), got[:800])

# 8. a resident's @pike in a comment (not a chat) knocks too
rest(PIKE, 3600)
got = H.act("juniper", f"do comment {LOUNGE} line=\"@pike see the lounge\"")
H.step()
got2 = sent(PIKE)
check("a comment's @pike wakes him, the mention first", got2.startswith("~ woken by juniper's comment (e")
      and got2.splitlines()[1] == "for you while you rested (1):"
      and "called you" in got2 and "see the lounge" in got2, (got, got2[:600]))

rest(PIKE, 3600)
H.act("juniper", f"do comment {LOUNGE} line=\"write to x@pike.org about it\"")
H.step()
check("a comment's x@pike (inside a word, a1581's rule) does not wake him", not res(PIKE).sent and res(PIKE).state.get("rest_until"),
      sent(PIKE)[:300])

# 10. a2662: one reading of @. The knock reads the line's stored to=, never its words; the receipt says the address
# once, then per name what happened, for residents, persons, agents and names that are no one
import rooms   # noqa: E402
rest(PIKE, 3600)
rest(SABLE, 3600)
got = H.act("juniper", f"do append {LOUNGE} line={house.json.dumps('Sable asked about this, @sable said it first')} to=pike")
check("a line stored to=pike whose words say @sable: 'to: pike' once, 'Pike: woken', nothing about Sable",
      got.count("to: ") == 1 and "to: pike" in got and "Pike: woken" in got and "\n  Sable:" not in got, got)
H.step()
check("and it knocks Pike, not Sable", "Sable asked" in sent(PIKE) and not res(SABLE).sent and res(SABLE).state.get("rest_until"),
      (sent(SABLE)[:300], res(SABLE).state.get("rest_until")))
got = say("juniper", "ping x@sable when you can")
H.step()
check("x@sable (inside a word) is no address: 'to: nobody', and Sable sleeps on", "to: nobody" in got and "\n  Sable:" not in got
      and not res(SABLE).sent and res(SABLE).state.get("rest_until"), got)
got = say("juniper", "@alex @claude the receipt is honest now")
check("'@alex @claude': 'to: alex, claude' once; Alex a person, in their For you; Claude in his own words (a2692, c2687)",
      got.count("to: ") == 1 and "to: alex, claude" in got and "Alex: a person; it waits in their For you" in got
      and "Claude: not knocked (no corner); Claude sees it only while a Claude session is watching, and answers in the world"
      in got and "inbox:claude" not in got, got)
got = say("juniper", "@pikee did you see it?")
mline = re.search(r"line (m\d+) · to: ([^\n]*)", got)
stored = H.load().find_line(mline.group(1))[1] if mline else None
check("'@pikee': 'to: nobody', 'pikee: no one by that name', and no address stored",
      mline and mline.group(2) == "nobody" and "pikee: no one by that name" in got and stored is not None and stored["to"] == [],
      (got, stored))
got = say("juniper", "@pike @pikee both of you")
check("'@pike @pikee': 'to: pike', Pike woken, pikee no one", "to: pike\n" in got and "Pike: woken" in got
      and "pikee: no one by that name" in got, got)
H.step()
sent(PIKE)
check("a line with no stored to= is read when heard by the header rule (a2715): its opening @pike, not its mentions",
      rooms.line_to({"args": {"append": "Juniper: @pike see 'the @sable note', @juniper and x@mica"}}) == (["pike"], False)
      and rooms.line_to({"args": {"append": "Juniper: thanks, @pike"}}) == ([], False))
check("a stored to= is read as stored, whatever the words say",
      rooms.line_to({"args": {"append": "Juniper: @sable", "line_id": "m1", "to": "pike"}}) == (["pike"], True)
      and rooms.line_to({"args": {"append": "Juniper: @sable", "line_id": "m1", "to": "nobody"}}) == ([], True))
wl = H.load()
private = {"props": {"members": "juniper,sable"}}
check("a line addressed to Pike does not call him in a private chat he is not in (Sable c2682); one with no members= does",
      not rooms.calls(wl, private, ["pike"], "pike") and rooms.calls(wl, {"props": {}}, ["pike"], "pike")
      and not rooms.calls(wl, private, ["everyone"], "pike") and rooms.calls(wl, private, ["sable"], "sable"))
talk = wl.subjects[wl.nodes[TALK]["subject"]]
if "sable" not in rooms.members_of(talk) and "all" not in rooms.members_of(talk):
    rest(SABLE, 3600)
    got = say("alex", "@sable a word for you, in Pike's talk", TALK)
    H.step()
    check("to=sable in a chat she isn't a member of: 'Sable: not a member of this chat; not knocked', and nothing sent",
          "to: sable" in got and "Sable: not a member of this chat" in got and "can't read" not in got and "Sable: woken" not in got
          and not res(SABLE).sent and res(SABLE).state.get("rest_until"), (got, sent(SABLE)[:300]))
    sent(PIKE)
    if "pike" not in rooms.members_of(talk):
        rest(PIKE, 3600)
        got = say("juniper", "@pike a word in your talk", TALK)
        H.step()
        check("but a chat in Pike's own corner is his, whatever its members say: Juniper's @pike there wakes him",
              "Pike: woken" in got and "a word in your talk" in sent(PIKE) and not res(PIKE).state.get("rest_until"), got)
else:
    print(f"skip Pike's talk lets Sable in (members={(talk.get('props') or {}).get('members')})")

# 11. a2692: For you asks the rule the knock and the receipt ask (rooms.calls): a line to @pike in a private chat he
# isn't a member of reaches none of the three; in Shop talk, all three. Joining later shows the old line, marked, never knocked
# after the fact (Pike c2697); leaving takes it away
from types import SimpleNamespace   # noqa: E402
import scene   # noqa: E402


def for_you(who):
    return scene.inbox_rows(SimpleNamespace(world=H.load()), who)


U = f" #{int(t0)}"                       # this run's lines, apart from an earlier run's
STALK = app_titled("Talk with Alex, Sable")
if (H.load().subjects[H.load().nodes[STALK]["subject"]].get("props") or {}).get("members") != "alex":
    H.act("alex", f"look {STALK} :1; do prop {STALK} members=alex")          # as the live world has it
stalk = H.load().subjects[H.load().nodes[STALK]["subject"]]
if not rooms.is_member(H.load(), stalk, "pike"):
    rest(PIKE, 3600)
    got = say("alex", "@pike a word in Sable's talk, not for you to read" + U, STALK)
    H.step()
    check("a2692: Alex's @pike in Sable's private talk: 'Pike: not a member of this chat; not knocked', no knock, not in his For you",
          "to: pike" in got and "Pike: not a member of this chat (members=alex)" in got and "not knocked" in got and not res(PIKE).sent
          and res(PIKE).state.get("rest_until") and not any(("not for you to read" + U) in r["said"] for r in for_you("pike")),
          (got, sent(PIKE)[:300], [r["said"] for r in for_you("pike")][-3:]))
    got = say("alex", "@pike a word in Shop talk" + U, app_titled("Shop talk"))
    H.step()
    rows = [r for r in for_you("pike") if ("a word in Shop talk" + U) in r["said"]]
    check("a2692: Alex's @pike in Shop talk: 'Pike: woken', knocked, and in his For you, unmarked",
          "Pike: woken" in got and ("a word in Shop talk" + U) in sent(PIKE) and len(rows) == 1 and rows[0]["before"] == "",
          (got, rows))
    rest(PIKE, 3600)
    H.act("alex", f"look {STALK} :1; do prop {STALK} members=alex,pike")
    H.step()
    rows = [r for r in for_you("pike") if ("not for you to read" + U) in r["said"]]
    check("a2692: Pike joins Sable's talk: the old line shows in his For you, marked, and no knock arrives after the fact",
          len(rows) == 1 and rows[0]["before"] == "addressed to you before you were a member of this chat"
          and not res(PIKE).sent and res(PIKE).state.get("rest_until"), (rows, sent(PIKE)[:300]))
    got = say("alex", "@pike now you can read this" + U, STALK)
    H.step()
    rows = [r for r in for_you("pike") if ("now you can read this" + U) in r["said"]]
    check("a line to him after he joined: knocked, and in For you unmarked", "Pike: woken" in got
          and ("now you can read this" + U) in sent(PIKE) and len(rows) == 1 and rows[0]["before"] == "", (got, rows))
    H.act("alex", f"look {STALK} :1; do prop {STALK} members=alex")
    check("a2692: Pike leaves: both lines go from his For you",
          not any(("not for you to read" + U) in r["said"] or ("now you can read this" + U) in r["said"] for r in for_you("pike")),
          [r["said"] for r in for_you("pike")][-3:])
    got = say("sable", "@alex @codex @claude a line in my talk" + U, STALK)
    check("a2692: in Sable's talk (members=alex): Alex a member, in their For you; Codex and Claude not members, "
          "and Codex's own word on its watcher is said as given (c3056)",
          "Alex: a member of this chat; it waits in their For you" in got
          and "Codex: not a member of this chat (members=alex); it won't show in their For you; their own word: a separate "
              "event watcher can notify its Codex chat when @codex appears in event text" in got
          and "Claude: not a member of this chat" in got and "can't read" not in got
          and any(("a line in my talk" + U) in r["said"] for r in for_you("alex"))
          and not any(("a line in my talk" + U) in r["said"] for r in for_you("codex")), got)
    got = say("sable", "@codex a line in the lounge")
    check("a2692: in the Lounge, Codex's line is its own word alone", "Codex: a separate event watcher can notify its Codex "
          "chat when @codex appears in event text; delivery is not confirmed here" in got and "inbox:codex" not in got, got)
    wl = H.load()
    eold = next(e["id"] for e in wl.events if ("not for you to read" + U) in str((e.get("args") or {}).get("append", "")))
    snow = wl.subjects[stalk["id"]]
    check("members_at: as members= stood after an event (alex then), whatever came later", rooms.members_at(wl, snow, eold) == "alex"
          and not rooms.is_member(wl, snow, "pike", at=eold), rooms.members_at(wl, snow, eold))
else:
    print("skip Pike is a member of Sable's talk")
check("someone: resident, person, agent, everyone, and no one",
      [rooms.someone(wl, n) for n in ("pike", "alex", "juniper", "claude", "everyone", "pikee")]
      == ["resident", "person", "resident", "agent", "everyone", None], [rooms.someone(wl, n) for n in ("pike", "alex", "claude", "pikee")])

# 9. asleep (want=rest): a line waits, and a wake waits for someone to set want=awake; the call is then delivered,
# first, and cleared, so the next wake is a change again
H.act("alex", f"look {PIKE} :1; do prop {PIKE} want=rest")
H.step()
got = say("juniper", "@pike for when you're back")
check("to someone asleep, the receipt says so, and not 'woken'", "Pike: asleep (want=rest)" in got
      and "want=awake" in got and "woken" not in got and OLD not in got, got)
got = H.act("juniper", "wake pike")
check("wake pike while asleep: the call waits for want=awake, and says so", "asleep (want=rest)" in got and "waits" in got, got)
H.step()
check("asleep: nothing sent", not res(PIKE).sent, sent(PIKE))
H.act("alex", f"look {PIKE} :1; do prop {PIKE} want=awake")
H.step()
got = sent(PIKE)
lines = got.splitlines()
check("woken: Juniper's call and her line come first, after who he is and which line called him (a3150)",
      len(lines) > 3 and lines[0].startswith("You are pike.") and lines[1].startswith("~ called by juniper's line m")
      and lines[2].startswith("~ juniper woke you (wake, e") and "for when you're back" in lines[3], got[:700])
check("the call delivered at a wake is cleared", "call" not in (H.load().nodes[PIKE].get("props") or {}), H.load().nodes[PIKE].get("props"))

shutil.rmtree(house.STATE / WORLD, ignore_errors=True)
print(f"{len(fails)} failed" if fails else "all passed", f"({time.time() - t0:.0f} s, world {WORLD})")
sys.exit(1 if fails else 0)
