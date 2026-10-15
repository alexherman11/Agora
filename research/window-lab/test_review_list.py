"""test_review_list.py: the home base's 'Waiting on you' list and its review buttons (a5390). 15 Oct 2026.

    python test_review_list.py [world] [--as who]

The list is world only: lens waiting-on-me (placed in home-base), roles wait* and review* in home-style, and one note
per viewer (role=home-review, actor=<them>) holding what they have open. This loads the world in memory (never saved),
makes a note and tags it ready-for-review, then presses the parts as the painter would send them: the item's click,
then Later, the item again, then Seen / Done, reading the scene after each. screen.py pressed the same in a painted
copy by hand (shots screen-2..6 on a5390); this is the check that stays.
"""
import re
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=DeprecationWarning)
NOTATION = Path(__file__).resolve().parents[1] / "text-desk-lab" / "notation"
sys.path.insert(0, str(NOTATION))
import explore  # noqa: E402
import scene as S  # noqa: E402


def walk(node):
    yield node
    for k in node.get("kids") or []:
        yield from walk(k)


class Viewer:
    def __init__(self, world, who):
        self.d = explore.load_desk(NOTATION / "sessions" / f"{world}.pickle")
        self.d.world.me = who
        self.d.seen, self.d.open, self.d.last_event_seen = {}, {self.d.world.root}, len(self.d.world.events)

    def do(self, line):
        r = self.d.dispatch("desk", {"line": line, "reply": "test-review-list"})
        text = r.get("text") or "ERR " + str(r.get("error"))
        assert not text.startswith("ERR") and "\nERR" not in text, f"{line}\n{text}"
        return text

    def scene(self):
        sc, _ = S.scene_for(self.d, "waiting-on-me")
        return list(walk(sc["root"] if "root" in sc else sc))

    def shown(self, nodes, where):
        """The items painted in the list `where` (now | later), in order."""
        return [n.get("item") for n in nodes if n.get("part") == "item" and not n.get("absent")
                and f"/{where}/" in n.get("key", "")]

    def press(self, nodes, item, part):
        """Send the line the painter would send for a click on `part` of `item`, as deskd runs it."""
        hits = [n for n in nodes if n.get("item") == item and n.get("part") == part and not n.get("absent")]
        assert hits, f"no {part} painted for {item}"
        lines = [a.get("line") or a.get("command") or a.get("do") for a in hits[0].get("acts") or []
                 if (a.get("on") or a.get("gesture") or "click") == "click"]
        lines = [l for l in lines if l]
        assert len(lines) == 1, f"{part} on {item} offers {len(lines)} click lines: {hits[0].get('acts')}"
        return self.do(lines[0])


def main():
    world = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "frontier-try"
    who = sys.argv[sys.argv.index("--as") + 1] if "--as" in sys.argv else "review-tester"
    v = Viewer(world, who)
    v.do("look desk :1")
    v.do(f"do create desk kind=note title='Review list test {who}' role=home-review actor={who} reviewing= full=no")
    made = v.do("do create desk kind=note title='A demo to look at' text='Something for Alex to try.'")
    demo = re.search(r"created (a\d+)", made).group(1)
    before = v.shown(v.scene(), "now")
    assert demo not in before, "the untagged note is listed"
    v.do(f"look {demo}")
    v.do(f"do tag {demo} add=ready-for-review")
    nodes = v.scene()
    assert demo in v.shown(nodes, "now"), "tagging it did not list it"
    print("tagged: listed with", len(v.shown(nodes, "now")) - 1, "others")
    v.press(nodes, demo, "item")
    nodes = v.scene()
    assert any(n.get("part") == "review" and n.get("item") == demo and not n.get("absent") for n in nodes), "the click opened nothing"
    print("click: the review opened")
    v.press(nodes, demo, "later")
    nodes = v.scene()
    assert demo not in v.shown(nodes, "now") and v.shown(nodes, "later") [-1:] == [demo], "Later did not move it below"
    print("Later: moved below, under Later")
    v.press(nodes, demo, "item")
    v.press(v.scene(), demo, "done")
    nodes = v.scene()
    assert demo not in v.shown(nodes, "now") + v.shown(nodes, "later"), "Done left it listed"
    props = v.d.world.subjects[v.d.world.nodes[demo]["subject"]].get("props") or {}
    assert "review" not in props, f"Done left review={props.get('review')}"
    print("Done: the tag and the Later mark are off; it is gone from the list")
    print("review list: ok")


if __name__ == "__main__":
    main()
