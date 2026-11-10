"""test_reaching (a736): how the house reads a resident's reply. Only > lines act; one > line is one command; a > line
that is no command is a miss, logged, and stops nothing; a reply with unmarked command words gets one notice. A
refused line refuses only itself (a6437): the lines after it run, one that depends on it is skipped, and the receipt
ends saying which ran, which were refused and why, and which were skipped.

    python test_reaching.py [world]      default frontier-try; it CHANGES the world it is given, so give it a copy

It drives House.after_turn, the house's own path, with a stand-in resident that keeps what the house would send
instead of writing to a claude process. No model is called. DESKD is off, so each act is one explore.py process;
--deskd http://127.0.0.1:<port> sends them through a deskd serving the same sessions instead.
"""
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = sys.argv[sys.argv.index("--deskd") + 1] if "--deskd" in sys.argv[:-1] else "off"
os.environ.setdefault("HOUSE_CLAUDE", "claude")     # the house looks for a claude binary; none is started here
import house   # noqa: E402

WORLD = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "frontier-try"
if not WORLD.endswith("-try") and "--yes" not in sys.argv:
    sys.exit(f"test_reaching changes the world it runs on; {WORLD} is not a -try copy (add --yes to insist)")
ME = "reach-test"


class Stand(house.Resident):
    def __init__(self, h, rid):
        super().__init__(h, rid)
        self.sent = []
        self.state["turns"] = self.state.get("turns", 0) + 1

    def send(self, text, kind="news", carry=None):
        self.sent.append((kind, text))


H = house.House(WORLD)
w = H.load()
RID = sorted(H.corners(w))[0]
CHAT = next(a["id"] for a in w.nodes.values() if a["type"] == "appearance"
            and (w.subjects.get(a.get("subject")) or {}).get("kind") == "chat")
NOTE = next(a["id"] for a in w.nodes.values() if a["type"] == "appearance"
            and (w.subjects.get(a.get("subject")) or {}).get("kind") == "note")
fails = []


def turn(reply):
    """-> (what the house sent back, the events it made, as the resident)"""
    r = Stand(H, RID)
    n0 = len(H.load().events)
    H.after_turn(H.load(), r, H.load().nodes[RID], ME, reply)
    evs = H.load().events[n0:]
    return "\n".join(t for _, t in r.sent), evs


def check(name, ok, detail=""):
    ok = ok and "the desk process failed" not in detail          # a crash never passes a check
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {detail[:1500]}"))
    if not ok:
        fails.append(name)


def mine(evs):
    return [e for e in evs if e.get("by") == ME and e["verb"] not in ("go",)]


def chat_lines():
    w = H.load()
    return (w.subjects[w.nodes[CHAT]["subject"]]["text"] or "").splitlines()


t0 = time.time()
# 1. prose runs nothing, whatever its first word
got, evs = turn("Remove the old notes later\nWhere things stand: the board is long.\nHistory says it changed\nMove on to the next card.")
check("prose runs nothing", not mine(evs) and "\n> " not in got and not got.startswith("> "), f"{got}\n{[(e['verb'], e['target']) for e in mine(evs)]}")
check("prose with command words gets the notice",
      "nothing ran: only lines beginning with > act (2 lines looked like commands)" in got, got)

# 2. two > lines both run, in order
got, evs = turn(f"Let me look.\n> read {NOTE}\n> look {RID} :1")
check("> read then > look both run", f"> read {NOTE}" in got and f"> look {RID} :1" in got
      and got.index(f"> read {NOTE}") < got.index(f"> look {RID} :1") and "ERR" not in got, got)

# 3. a ; on a > line is words
got, evs = turn(f"> look {CHAT} :1\n> do append {CHAT} line=\"a; b\"")
check('line="a; b" appends one line a; b', chat_lines()[-1].endswith("a; b") and len(mine(evs)) == 1, f"{got}\n{chat_lines()[-1:]}")
got, evs = turn(f"> look {CHAT} :1\n> do append {CHAT} line=one; two")
check("unquoted line=one; two is one command: refused whole, nothing split, nothing appended",
      not mine(evs) and "unexpected words" in got and "stopped" not in got, got)
got, evs = turn(f"> look {RID} :1; do prop {RID} reachtest=1")
check("> look X; do prop ... is one command, so the prop is never set", not mine(evs)
      and "reachtest" not in str((H.load().nodes[RID].get("props") or {})), got)

# 4. only an unmarked command: nothing runs, one notice
got, evs = turn("look Home")
check("'look Home' without > runs nothing and gets the notice",
      not mine(evs) and got.strip() == "nothing ran: only lines beginning with > act (1 line looked like command)", got)

# 5. a wake string keeps ; as a separator
out = H.act(ME, f"look {RID} :1; read {NOTE}")
check("a wake string with ; runs all its parts", "[1]" in out and "[2]" in out and "ERR" not in out, out)

# 6. a quote between two commands: both commands run, the quote is a miss, logged
def miss_log():
    w = H.load()
    return next((s["text"] for s in w.subjects.values() if (s.get("props") or {}).get("role") == "misses"), "")


before = miss_log()
got, evs = turn(f"> look {RID} :1\n> I think i want a door that opens both ways\n> read {NOTE}")
w = H.load()
log = next((s for s in w.subjects.values() if (s.get("props") or {}).get("role") == "misses"), None)
check("a quoted > line between two commands: both run", f"> look {RID} :1" in got and f"> read {NOTE}" in got, got)
check("the quote is logged as a miss with actor, time, reply and the whole line",
      log is not None and len(log["text"].splitlines()) == len(before.splitlines()) + 1
      and f"{ME}, " in log["text"].splitlines()[-1] and "reply " in log["text"].splitlines()[-1]
      and log["text"].splitlines()[-1].endswith(f"in {RID}: > I think i want a door that opens both ways"),
      (log or {}).get("text", "no misses chat")[-600:])
check("the resident is told of the miss, and where it is logged", "MISS unknown command 'i'" in got
      and "1 line after > that nothing answered, logged in" in got, got)

# 6b. prose with an apostrophe after > is a miss too, not a parse refusal that stops the rest
got, evs = turn(f"> I don't think so, said Juniper\n> look {RID} :1")
check("> I don't ... is a miss and the next line runs", "MISS" in got and "stopped" not in got
      and f"> look {RID} :1\n" in got and "ERR" not in got, got)

# 6c. a verb made in the world answers a > line: it is no miss
w = H.load()
import verbs  # noqa: E402
house_verbs = [s for s in verbs.all_verbs(w) if verbs.where(w, s)[0] == "house" and "$" not in s["text"]]
if house_verbs:
    word = verbs._names(house_verbs[0]["title"])[0]
    got, evs = turn(f"> {word}")
    check(f"> {word} (a verb in the world) runs and is no miss", "MISS" not in got and f"> {word}" in got, got)
else:
    print("skip no house verb without arguments in this world")

# 6d. a refused line with a ; says why
got, evs = turn(f"> read {NOTE}; read {NOTE}")
check("a refused > line with a ; says one > line is one command", "put each command on its own > line" in got, got)

# 7. a refused line refuses only itself (a6437, Alex 17 Oct: "keep going if something gets refused"); a later line that
# depends on it is skipped, and the receipt ends saying what ran, what was refused (why) and what was skipped
T = str(int(time.time()))        # this run's values, so a second run on the same copy sets no prop to what it has


def tail(got):
    return got[got.index("~ this reply:"):] if "~ this reply:" in got else ""


def answer(got, line):
    """What the desk said to one > line of the receipt."""
    i = got.index(f"> {line}\n") + len(line) + 3
    return got[i:].split("\n> ", 1)[0].split("\n~ ", 1)[0]


# 7a. independent refusal: the lines after it run
got, evs = turn(f"> read zz999\n> look {RID} :1\n> read {NOTE}")
check("7a. a refused line refuses only itself: the two after it run", "stopped" not in got
      and answer(got, "read zz999").startswith("ERR") and not answer(got, f"look {RID} :1").startswith("ERR")
      and not answer(got, f"read {NOTE}").startswith("ERR"), got)
check("7a. the receipt ends with what ran and what was refused, with its reason",
      tail(got).startswith("~ this reply: 3 lines; 2 ran, 1 refused.") and "refused: read zz999  (no such id 'zz999')" in tail(got)
      and f"ran: look {RID} :1 | read {NOTE}" in tail(got), tail(got))

# 7b. dependent skip: $new and the title of a refused create are skipped; an independent line between them runs
got, evs = turn(f"> look {RID} :1\n> do create zz998 kind=note title=\"Reach dep\" text=x\n> do prop $new reachdep=1\n"
                f"> read {NOTE}\n> do comment \"Reach dep\" line=\"for the note\"\n> do prop {RID} reachdep=2{T}")
check("7b. $new after a refused create is skipped, saying why",
      answer(got, "do prop $new reachdep=1").startswith("skipped: depends on the refused line (> do create zz998")
      and "$new here would name an older thing" in answer(got, "do prop $new reachdep=1"), got)
check("7b. a line naming the title the refused line was to give is skipped",
      answer(got, 'do comment "Reach dep" line="for the note"').startswith("skipped: depends on the refused line")
      and '"Reach dep" is the title it was to give' in got, got)
check("7b. the lines that do not depend on it run (the read, and a prop on the corner)",
      not answer(got, f"read {NOTE}").startswith(("ERR", "skipped")) and answer(got, f"do prop {RID} reachdep=2{T}").startswith("ok")
      and [e["verb"] for e in mine(evs)] == ["prop"], f"{got}\n{[(e['verb'], e['target']) for e in mine(evs)]}")
check("7b. the receipt counts them apart, so no skipped line reads as one that ran",
      tail(got).startswith("~ this reply: 6 lines; 3 ran, 1 refused, 2 skipped.")
      and "skipped: do prop $new reachdep=1  (depends on the refused line)" in tail(got)
      and "do prop $new" not in tail(got).split("ran: ")[-1], tail(got))

# 7b'. a $new made by a line that ran AFTER the refusal names that line's thing: it is not skipped
got, evs = turn(f"> look {RID} :1\n> do create zz998 kind=note title=\"Reach dep2\" text=x\n"
                f"> do create {RID} kind=note title=\"Reach dep3\" text=y\n> do prop $new reachdep=3")
made = [e for e in mine(evs) if e["verb"] == "create"]
check("7b'. a create that runs after the refused one gives $new back: its prop runs, on the new thing",
      answer(got, "do prop $new reachdep=3").startswith("ok") and len(made) == 1, got)

# 7c. a stale refusal in the middle refuses only itself
turn(f"> read {NOTE}")
H.act("reach-other", f"read {NOTE}\ndo prop {NOTE} reachstale=theirs{T}", whole=True)
got, evs = turn(f"> look {RID} :1\n> do prop {NOTE} reachstale=mine{T}\n> do prop {RID} reachstale=after{T}")
w = H.load()
note_props = w.subjects[w.nodes[NOTE]["subject"]].get("props") or {}
check("7c. a line refused as stale refuses only itself; the line after it runs",
      answer(got, f"do prop {NOTE} reachstale=mine{T}").startswith("ERR") and note_props.get("reachstale") == f"theirs{T}"
      and answer(got, f"do prop {RID} reachstale=after{T}").startswith("ok") and "1 refused" in tail(got), got)

# 7d. a crossing chat line lands and shows the missed words; the rest run
turn(f"> read {CHAT}")
H.act("reach-other", f"look {CHAT} :1\ndo append {CHAT} line=\"reach-other: wait, do not merge\"", whole=True)
got, evs = turn(f"> look {RID} :1\n> do append {CHAT} line=\"merging now\"\n> read {NOTE}")
check("7d. the crossing chat line lands with the missed words, and the line after it runs",
      answer(got, f"do append {CHAT} line=\"merging now\"").startswith("ok")
      and chat_lines()[-1].endswith("merging now") and not answer(got, f"read {NOTE}").startswith("ERR")
      and "wait, do not merge" in answer(got, f"do append {CHAT} line=\"merging now\"")
      and "held, not sent" not in tail(got), got)

# 7e. three refusals in a row: each refuses only itself, and the last line still runs
got, evs = turn(f"> read zz991\n> do prop zz992 x=1\n> read zz993\n> look {RID} :1")
check("7e. three refusals in a row, then a line that runs",
      tail(got).startswith("~ this reply: 4 lines; 1 ran, 3 refused.") and tail(got).count("  refused: ") == 3
      and not answer(got, f"look {RID} :1").startswith("ERR") and f"ran: look {RID} :1" in tail(got), got)

# 7f. a reply with no refusal gets no summary: nothing new to read
got, evs = turn(f"> look {RID} :1\n> read {NOTE}")
check("7f. a reply where everything ran has no summary", "~ this reply:" not in got, got)

# 8. a > line with an open quote goes on to the next lines, as one command
got, evs = turn(f"> look {CHAT} :1\n> do append {CHAT} line=\"first; line\nsecond line\"")
check("a quoted value over two lines is one command", len(mine(evs)) == 1 and "first; line" in "\n".join(chat_lines()[-2:])
      and chat_lines()[-1].endswith("second line"), f"{got}\n{chat_lines()[-2:]}")

print(f"{len(fails)} failed" if fails else "all passed", f"({time.time() - t0:.0f} s, world {WORLD}, corner {RID}, chat {CHAT})")
sys.exit(1 if fails else 0)
