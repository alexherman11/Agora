"""copy_reach.py (a8911): whom a waiting card's question reached, read from a -try copy by the house's own readings.

    python research/window-lab/notice-routing/copy_reach.py <world>-try <card> [<card> ...]

Read only: loads the copy as explore.py does (explore.load_desk) and never saves it. For each card: the worker's
last mark=ask comment and whom it reaches (rooms.reached, the reading the house's knock uses), the commission=waiting
event and its task notices (task_flow.notices, the house's durable task inbox), and the notice notes about the card.
No house runs on a copy, so this is what the house WOULD knock and queue, not a delivered wake.
"""
import os
import sys
from pathlib import Path

os.environ["DESKD"] = "off"
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "text-desk-lab" / "notation"))
import explore  # noqa: E402
import rooms  # noqa: E402
import task_flow  # noqa: E402

world = sys.argv[1]
if not world.endswith("-try"):
    sys.exit("copies only: a world whose name ends in -try")
w = explore.load_desk(explore.SESSIONS / f"{world}.pickle").world
print(f"{world} at e{len(w.events)}")
for card in sys.argv[2:]:
    s = w.subjects[w.nodes[card]["subject"]]
    p = s.get("props") or {}
    sid = s["id"]

    def on_card(e):
        t = e.get("target")
        return (w.nodes.get(t) or {}).get("subject", t) == sid
    ask = next((e for e in reversed(w.events) if e.get("verb") == "comment" and on_card(e)
                and (e.get("args") or {}).get("mark") == "ask" and not e.get("undone")), None)
    wait = next((e for e in reversed(w.events) if e.get("verb") == "prop" and on_card(e)
                 and (e.get("args") or {}).get("commission") == "waiting"), None)
    notes = [(x.get("props") or {}).get("to") for x in w.subjects.values()
             if (x.get("props") or {}).get("about") == card and (x.get("props") or {}).get("role") == "notice"]
    print(f"\n{card} {s.get('title')!r}: asked_by={p.get('asked_by', '')} lead={p.get('lead', '')}")
    print(f"  question {ask['id'] if ask else None} by {ask.get('by') if ask else None}: reaches "
          f"{rooms.reached(w, ask) if ask else None}")
    print(f"  waiting {wait['id'] if wait else None}: task notices to "
          f"{[n['recipient'] for n in task_flow.notices(w, wait)] if wait else None}")
    print(f"  notice notes about it: to={notes}")
