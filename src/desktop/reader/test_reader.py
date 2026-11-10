"""test_reader.py: the reader (a6460) in a world, pressed as the painter would press it. 20 Oct 2026.

    python src/desktop/reader/test_reader.py [world] [--as who]

Loads the world in memory (never saved), puts the world half in (apply.lines(): the rd roles, lens reader, a reader
note, the viewer, Writing, board and waiting-list lines), then, as Alex would:
  - opens EVERY thing waiting on him in the viewer and checks it opens in the reader (a note, a task, a design that is
    a surface of paragraphs: each kind once broke the whole viewer while building this), with Next / Previous where
    they belong and the count right;
  - Skim, then Read; Later and Not later; Send back with a note (the box, then Enter); Looks good;
    Build it and Not now on designs; and that a thing answered leaves the waiting list and offers the next;
  - presses a needs-you line's words on the board (one press opens it in the reader, Open with cleared);
  - opens a waiting note in the Writing app: it opens to Read.
"""
import re
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=DeprecationWarning)
HERE = Path(__file__).resolve().parent
NOTATION = HERE.parents[1] / "text-desk" / "notation"
sys.path.insert(0, str(NOTATION))
sys.path.insert(0, str(HERE))
import explore  # noqa: E402
import scene as S  # noqa: E402
import apply  # noqa: E402

FAILS = []


def walk(node):
    yield node
    for k in node.get("kids") or []:
        yield from walk(k)


def check(what, ok, more=""):
    print(("ok   " if ok else "FAIL ") + what + ("" if ok else f": {more}"))
    if not ok:
        FAILS.append(what)


class Desk:
    def __init__(self, world, who):
        self.d = explore.load_desk(NOTATION / "sessions" / f"{world}.pickle")
        self.who = who
        self.as_(who)

    def as_(self, who):
        self.d.world.me = who
        self.d.seen, self.d.open, self.d.last_event_seen = {}, {self.d.world.root}, len(self.d.world.events)

    def do(self, line, ok=True):
        r = self.d.dispatch("desk", {"line": line, "reply": "test-reader"})
        text = r.get("text") or "ERR " + str(r.get("error"))
        bad = text.startswith("ERR") or "\nERR" in text or "~ ! lens" in text
        if ok:
            assert not bad, f"{line[:200]}\n{text[-1500:]}"
        return text

    def scene(self, lens):
        sc, _ = S.scene_for(self.d, lens)
        root = sc["root"] if "root" in sc else sc
        return list(walk(root))

    def props(self, nid):
        w = self.d.world
        node = w.nodes.get(nid) or {}
        return {**(node.get("props") or {}), **((w.subjects.get(node.get("subject")) or w.subjects.get(nid) or {}).get("props") or {})}

    def tags(self, nid):
        w = self.d.world
        return (w.subjects.get((w.nodes.get(nid) or {}).get("subject")) or w.subjects.get(nid) or {}).get("tags") or []


def shown(nodes, part, under="lens:reader"):
    return [n for n in nodes if n.get("part") == part and not n.get("absent") and under in n.get("key", "")]


def press(desk, nodes, part, gesture="click", value=None, under="lens:reader"):
    hits = shown(nodes, part, under)
    assert hits, f"no {part} painted"
    acts = [a for a in hits[0].get("acts") or [] if (a.get("on") or "click") == gesture]
    assert len(acts) == 1, f"{part} offers {len(acts)} {gesture} lines: {hits[0].get('acts')}"
    line = acts[0].get("line")
    if value is not None:
        line = line.replace("$value", value)
    return desk.do(line)


def words(nodes, part, under="lens:reader"):
    return [n.get("text") or "" for n in shown(nodes, part, under)]


def main():
    world = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "frontier-try"
    who = sys.argv[sys.argv.index("--as") + 1] if "--as" in sys.argv else "alex"
    k = Desk(world, who)
    print(f"world: {world} at {k.d.world.events[-1]['id']} (in-memory changes only)")
    if "role rdpage" in k.do("read a5206 :3"):      # a copy the lines already ran in (explore.py saves): the lens again
        k.do("look f5204")
        k.do("read reader :3")
        k.do(f"do rewrite reader text={apply.q(apply.text('reader.lens'))}")
        # and its viewer and Writing lines as an earlier round of this file wrote them, brought up to today's
        for note, old, new in apply.UPGRADES:
            if old in k.do(f"read {note} :3"):
                k.do(f"do replace {note} old={apply.q(old)} new={apply.q(new)}")
    else:
        for line in apply.lines():
            if line.startswith("do create") and "role=reader" in line:
                line = line.replace("actor=alex", f"actor={who}")
            k.do(line)
    view = re.search(r"(a\d+) note", k.do("find prop:role=home-view,prop:actor=" + who)).group(1)
    # The universal review verb also tags designs: the reader must count those once.
    k.do("look f5204")
    made = k.do('do create f5204 kind=note title="Design with both waiting marks" '
                'design=waiting tags=ready-for-review text="Build a readable article."')
    dual = re.search(r"created (\w\d+)", made).group(1)
    tagged = [m for m in re.findall(r"\n\s+(\w\d+) ",
                                   k.do("find tag:ready-for-review,-prop:design=waiting"))]
    designs = [m for m in re.findall(r"\n\s+(\w\d+) ", k.do("find prop:design=waiting"))]
    order = tagged + designs
    print(f"waiting: {len(tagged)} tagged, {len(designs)} designs")
    check("something waits (else this proves nothing)", len(order) >= 2, order)

    def open_(nid):
        k.do(f"read {view}")
        if k.props(view).get("viewing") != nid or k.props(view).get("with"):
            k.do(f"do prop {view} viewing={nid} with=\"\"")
        return k.scene("home-viewer")

    # every waiting thing opens in the reader, its kind whatever it is; its place is 'k of n' (the selections' own
    # order, tagged first: find lists by room, so that order is read from the reader), and Next / Previous name the
    # things one place on either side
    seen = {}
    for nid in order:
        nodes = open_(nid)
        kind = k.d.world.nodes.get(nid, {}).get("type") or "?"
        check(f"{nid} ({kind}) opens in the reader", bool(shown(nodes, "title")), "no reader title")
        pos = words(nodes, "pos")
        m = re.fullmatch(r"(\d+) of (\d+)", pos[0]) if len(pos) == 1 else None
        check(f"{nid}: one place, 'k of {len(order)}'", bool(m) and int(m.group(2)) == len(order), pos)
        if "--why" in sys.argv:
            print([(n["part"], n.get("absent"), n.get("why")) for n in nodes if n.get("part") in ("fromtags", "one", "lastone", "intodesigns")][:8])
        seen[nid] = (int(m.group(1)) if m else 0, words(nodes, "nextone") + words(nodes, "firstone"),
                     words(nodes, "prevone") + words(nodes, "lastone"))
        answers = sorted(n["part"] for n in nodes if "/foot/bar/" in n.get("key", "") and not n.get("absent") and n.get("acts"))
        later = "unlater" if k.props(nid).get("review") == "later" else "later"
        want = sorted(["build", "notnow", later, "send"] if nid in designs else ["good", later, "send"])
        check(f"{nid}: the answers that fit it", answers == want, answers)
    at = {p: nid for nid, (p, _, _) in seen.items()}
    check("the places are 1..n, each once", sorted(at) == list(range(1, len(order) + 1)), sorted(at))
    check("tagged things come before designs", all(seen[t][0] < seen[d][0] for t in tagged for d in designs), seen)
    for nid, (p, nxt, prv) in seen.items():
        want_n = [f"Next: {at[p + 1]}"] if p + 1 in at else []
        want_p = [f"Previous: {at[p - 1]}"] if p - 1 in at else []
        check(f"{nid} (place {p}): Next and Previous name its neighbours", nxt == want_n and prv == want_p, (nxt, prv, want_n, want_p))
    order = [at[p] for p in sorted(at)]

    first = order[0]
    nodes = open_(first)
    reader = re.search(r"(a\d+) note", k.do(f"find prop:role=reader,prop:actor={who}")).group(1)
    # Skim, then Read
    press(k, nodes, "skimit")
    nodes = k.scene("home-viewer")
    check("Skim: the article gives way to headings and first sentences", not shown(nodes, "note") and bool(shown(nodes, "skimming")), "")
    press(k, nodes, "read")
    nodes = k.scene("home-viewer")
    check("Read: the article again", bool(shown(nodes, "note")) or bool(shown(nodes, "surface")), "")
    writer = re.search(r"(a\d+) note", k.do(f"find prop:role=writer,prop:actor={who}"))
    writer = writer.group(1) if writer else None
    if writer and shown(nodes, "article"):
        press(k, nodes, "article", "select", "A passage held for the Conversation")
        p = k.props(writer)
        check("article selection is anchored on the writer for the universal composer",
              p.get("quoting") == first and p.get("quote_in") == first
              and p.get("quote") == "A passage held for the Conversation", p)
        nodes = k.scene("home-viewer")
        check("article selection keeps its highlight",
              "A passage held for the Conversation" in str(shown(nodes, "article")[0].get("light")), "")
        k.do(f"read {writer}")
        k.do(f"do prop {writer} role=reader-fixture-no-writer")
        check("article still renders without a writer note",
              bool(shown(k.scene("home-viewer"), "plain")), "")
        k.do(f"read {writer}")
        k.do(f"do prop {writer} role=writer")
        nodes = k.scene("home-viewer")
    # Later, Not later
    press(k, nodes, "later")
    check("Later marks it review=later", k.props(first).get("review") == "later", k.props(first))
    nodes = k.scene("home-viewer")
    press(k, nodes, "unlater")
    check("Not later takes the mark off", "review" not in k.props(first), k.props(first))
    check("questions use the shared Conversation without a duplicate reader box",
          not shown(k.scene("home-viewer"), "ask"), "")
    # Send back with a note: the tag comes off, JEFF is called with the note
    if first in tagged:
        nodes = k.scene("home-viewer")
        press(k, nodes, "send")
        nodes = k.scene("home-viewer")
        before = len(k.d.world.events)
        press(k, nodes, "say", "edit", "split the section on wake cost out")
        check("Send back: it no longer waits", "ready-for-review" not in k.tags(first), k.tags(first))
        com = [e for e in k.d.world.events[before:] if e.get("verb") == "comment"]
        check("Send back: a comment calls JEFF with the note", bool(com), [e.get("verb") for e in k.d.world.events[before:]])
        nodes = k.scene("home-viewer")
        check("answered: the reader says so and offers the next", bool(shown(nodes, "done")) and bool(words(nodes, "firstone")),
              (words(nodes, "done"), words(nodes, "firstone"), words(nodes, "title"), k.tags(first),
               [(n["part"], n.get("absent")) for n in nodes if n.get("part") in ("look", "done", "onward", "stood", "mine")][:8]))
    # Looks good on the next tagged
    if len(tagged) > 1:
        nodes = open_(tagged[1])
        press(k, nodes, "good")
        check("Looks good: it no longer waits", "ready-for-review" not in k.tags(tagged[1]), k.tags(tagged[1]))
    # Build it / Not now on designs
    if designs:
        nodes = open_(designs[0])
        press(k, nodes, "build")
        p = k.props(designs[0])
        check("Build it: design=answered verdict=build", p.get("design") == "answered" and p.get("verdict") == "build", p)
    if len(designs) > 1:
        nodes = open_(designs[1])
        press(k, nodes, "notnow")
        p = k.props(designs[1])
        check("Not now: design=answered verdict=not-now", p.get("design") == "answered" and p.get("verdict") == "not-now", p)
    nodes = open_(dual)
    press(k, nodes, "build")
    check("answering a design clears both waiting marks",
          k.props(dual).get("design") == "answered" and "ready-for-review" not in k.tags(dual),
          (k.props(dual), k.tags(dual)))
    for answer in ("notnow", "send"):
        # Requeueing the same fixture within one second must not turn the
        # answer receipt into a duplicate-prop refusal at the test clock's tick.
        k.do(f"read {reader}")
        k.do(f"do prop {reader} remove=answered")
        k.do(f"look {dual}")
        k.do(f"do prop {dual} design=waiting")
        k.do(f"do tag {dual} add=ready-for-review")
        nodes = open_(dual)
        press(k, nodes, answer)
        if answer == "send":
            press(k, k.scene("home-viewer"), "say", "edit", "Please clarify the decision.")
        check(f"{answer} also clears both waiting marks",
              k.props(dual).get("design") == "answered" and "ready-for-review" not in k.tags(dual),
              (k.props(dual), k.tags(dual)))

    # the board: one press on a needs-you line's words opens it in the reader, Open with cleared
    left = re.findall(r"\n\s+(\w\d+) ", k.do("find tag:ready-for-review"))
    if left:
        k.do(f"read {view}")
        k.do(f'do prop {view} viewing={reader} with=doc-page')
        nodes = k.scene("waiting-on-me")
        hit = [n for n in nodes if n.get("part") == "head" and n.get("item") == left[0] and not n.get("absent") and n.get("acts")]
        check("waiting list: the item's header carries one press", bool(hit), "")
        if hit:
            k.do([a for a in hit[0]["acts"] if (a.get("on") or "click") == "click"][0]["line"])
            p = k.props(view)
            check("waiting list: one press opens the reader, Open with cleared",
                  p.get("viewing") == left[0] and not p.get("with") and bool(shown(k.scene("home-viewer"), "title")), p)
        k.do(f"read {view}")
        k.do(f"do prop {view} viewing={reader} with=doc-page")
        nodes = k.scene("home-board")
        hit = [n for n in nodes if n.get("part") == "what" and n.get("item") == left[0] and not n.get("absent") and n.get("acts")]
        check("the board's line words carry one press", bool(hit), "")
        if hit:
            k.do([a for a in hit[0]["acts"] if (a.get("on") or "click") == "click"][0]["line"])
            p = k.props(view)
            check("one press on the board opens it, Open with cleared", p.get("viewing") == left[0] and not p.get("with"), p)
            check("and the viewer shows the reader", bool(shown(k.scene("home-viewer"), "title")), "")

    # Writing: a waiting document opens to Read
    w = re.search(r"(a\d+) note", k.do(f"find prop:role=writer,prop:actor={who}"))
    docs = re.findall(r"\n\s+(\w\d+) ", k.do("find prop:design=waiting"))
    if w and docs:
        k.do(f"read {w.group(1)}")
        k.do(f"do prop {w.group(1)} open={docs[0]}")
        nodes = k.scene("writing")
        check("Writing: a waiting document opens to Read", bool(shown(nodes, "title")), "")
    # A section in a paragraph design can contain several paragraphs. Skim must keep only the first sentence,
    # including when that sentence is a list item, rather than showing a sentence from every paragraph.
    k.do("look f5204")
    made = k.do('do create f5204 kind=surface title="Reader skim fixture"')
    fixture = re.search(r"→ created (\w\d+)", made).group(1)
    k.do(f"look {fixture}")
    k.do(f"do prop {fixture} design=waiting owner=pike")
    for block, text in [
        ("h2", "The first choice"),
        ("text", "Keep the answer beside the article. Extra detail follows."),
        ("text", "This later paragraph must disappear in skim."),
        ("h2", "The next choice"),
        ("bullet", "Keep the first list sentence visible. More detail."),
        ("bullet", "Hide the later list item."),
    ]:
        k.do(f"look {fixture}")
        k.do(f"do create {fixture} kind=note title={apply.q(text)} block={block} text={apply.q(text)}")
    nodes = open_(fixture)
    check("a design owner is not falsely credited as its author",
          not words(nodes, "by") and words(nodes, "unknown") == ["Author not recorded"], "")
    k.do(f"look {fixture}")
    k.do(f"do prop {fixture} sent_by=jeff")
    nodes = k.scene("home-viewer")
    check("a sender is labelled separately from authorship",
          words(nodes, "sender") == ["Sent by jeff"] and not words(nodes, "by"), "")
    if k.props(reader).get("skim"):
        press(k, nodes, "read")
        nodes = k.scene("home-viewer")
    paragraph = shown(nodes, "paragraphtext")
    if writer:
        check("paragraph design offers selection anchors", bool(paragraph), "")
        if paragraph:
            press(k, nodes, "paragraphtext", "select", "The first choice")
            p = k.props(writer)
            check("paragraph selection keeps the document and paragraph separately",
                  p.get("quote_in") == fixture and p.get("quoting") != fixture
                  and p.get("quoting") in k.d.world.nodes and p.get("quote") == "The first choice", p)
        nodes = k.scene("home-viewer")
    if not k.props(reader).get("skim"):
        press(k, nodes, "skimit")
    nodes = k.scene("home-viewer")
    check("paragraph design skim: headings and only each section's first sentence",
          words(nodes, "h") == ["The first choice", "The next choice"] and
          words(nodes, "g") == ["Keep the answer beside the article.", "Keep the first list sentence visible."],
          (words(nodes, "h"), words(nodes, "g")))
    print("reader:", "ok" if not FAILS else f"{len(FAILS)} FAIL")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
