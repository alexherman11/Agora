"""roomworld (a1190): the small world the rooms tests build for themselves, so a result depends on the code and not on
what the residents did today.

    import roomworld
    D, R = roomworld.build()        # a fresh desk (explore.fresh), in memory, never saved; R names what was made

Until a1190, test_room_verbs, test_room_look, test_room_reads and test_blanks read a copy of the live world, and they
failed more as it changed (16 failures in test_room_verbs on a1062's copy: the Desktop already said verbs=layout, the
residents had rewritten their wake lines, Pike had months of reading in the Lounge). Everything here is made through
ordinary desk lines, as a person would make it, so the build itself is a small test of create, prop and append.

The shape follows the live world's (rooms inside Home, corners on a Corners surface that is not a room):

  Home (room, describe)
    Board    (room, describe, talk "Board talk", two cards)
    Lounge   (room, describe, talk "Lounge talk" with three short lines, a note, a surface "Shelf", a note holding $)
    Desktop  (room, describe; verbs=layout is NOT set: test_room_verbs sets it and takes it away)
    Archive  (room, describe, no talk: a quiet room)
    Corners  (a plain surface)
      Juniper's corner, Pike's corner, Sable's corner   (role=resident, actor=, describe, wake="read <describe> :3; look")
    say      (a house verb: do append $here.talk line="$*")
"""
import os
import re
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

RESIDENTS = ("juniper", "pike", "sable")


def build(say=True):
    """-> (desk, R). say=False leaves the house verb out (for a test that makes its own)."""
    import explore
    d = explore.fresh()
    d._session = "roomworld-inmemory"
    w = d.world
    slots = {}

    def run(me, *lines):
        slots[w.me] = (d.seen, d.open, d.last_event_seen)
        d.seen, d.open, d.last_event_seen = slots.get(me) or ({}, {w.root}, len(w.events))
        w.me = me
        token, made = uuid.uuid4().hex, None
        for line in lines:
            r = d.dispatch("desk", {"line": line, "whole": True, "reply": token})
            if r.get("error") or "ERR" in (r.get("text") or "")[:4]:
                raise RuntimeError(f"roomworld could not build: {line!r} -> {r.get('error') or r.get('text')}")
            m = re.search(r"created ([af]\d+)", r.get("text") or "")
            made = m.group(1) if m else made
        return made

    def make(parent, how, me="jeff"):
        return run(me, f"look {parent} :1", f"do create {parent} {how}")

    def room(parent, title, describe, talk=None, role="room", **props):
        fid = make(parent, f'kind=surface title="{title}"')
        desc = make(fid, f'kind=note title="About {title}" text="{describe}"')
        tid = make(fid, f'kind=chat title="{title} talk" members=all') if talk else None
        extra = " ".join(f'{k}="{v}"' for k, v in props.items())
        run("jeff", f"look {fid} :1", f"do prop {fid} role={role} describe={desc}" + (f" talk={tid}" if tid else "")
            + (f" {extra}" if extra else ""))
        return fid, desc, tid

    root = w.root
    run("jeff", "clock follow")         # as the live world: $today is the wall date (a fresh desk has no clock)
    home, home_desc, _ = room(root, "Home", "The house: every room is inside it.")
    board, board_desc, board_talk = room(home, "Board", "Cards on a wall.", talk=True)
    cards = [make(board, f'kind=note title="{t}" text="{t}, to do"') for t in ("Card one", "Card two")]
    lounge, lounge_desc, lounge_talk = room(home, "Lounge", "Low couches around a table.", talk=True)
    note = make(lounge, 'kind=note title="A letter" text="Dear all, a short letter."')
    shelf = make(lounge, 'kind=surface title="Shelf"')
    prices = make(lounge, 'kind=note title="Prices" text="a coffee is \\$5; say \\$here to mean the room"')
    desktop, desktop_desc, _ = room(home, "Desktop", "Alex's screen.")
    archive, archive_desc, _ = room(home, "Archive", "Old things, kept.")
    corners_surface = make(home, 'kind=surface title="Corners"')
    corners, corner_desc = {}, {}
    for a in RESIDENTS:
        name = a.capitalize()
        fid, desc, _ = room(corners_surface, f"{name}'s corner", f"{name}'s own place.", role="resident", actor=a)
        run("jeff", f"look {fid} :1", f'do prop {fid} wake="read {desc} :3; look"')
        corners[a], corner_desc[a] = fid, desc
    for who, line in (("sable", "the couches are new"), ("juniper", "they are soft"), ("sable", "good for thinking")):
        run(who, f'do append {lounge_talk} line="{line}"')
    run("pike", f'do append {board_talk} line="two cards up"')
    say_id = None
    if say:
        say_id = make(home, 'kind=note title=say tags=verb on=house text="# say something in the room you are in: '
                            'say <words>\\ndo append $here.talk line=\\"$*\\""')
    w.me = "jeff"
    d.seen, d.open, d.last_event_seen = {}, {root}, len(w.events)
    d._per = {}
    R = SimpleNamespace(HOME=home, BOARD=board, LOUNGE=lounge, DESKTOP=desktop, ARCHIVE=archive, CORNERS=corners_surface,
                        corner=corners, corner_desc=corner_desc, NOTE=note, SHELF=shelf, PRICES=prices, CARDS=cards,
                        TALK={board: board_talk, lounge: lounge_talk}, describe={home: home_desc, board: board_desc,
                        lounge: lounge_desc, desktop: desktop_desc, archive: archive_desc}, SAY=say_id)
    return d, R


if __name__ == "__main__":
    D, R = build()
    W = D.world
    import rooms
    for f in rooms.all_rooms(W):
        print(f, W.nodes[f]["title"], W.nodes[f]["props"])
    print(vars(R))
