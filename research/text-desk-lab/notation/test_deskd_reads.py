"""deskd, a4465 (13 Oct): a request that only reads pickles the world once and writes nothing, and a painter's report
does not make the scenes be built again.

    python test_deskd_reads.py

Everything runs in a temporary directory: no shared session is read or written.
"""
import os
import pickle
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"
sys.argv = sys.argv[:1]

import deskd      # noqa: E402

tmp = Path(tempfile.mkdtemp(prefix="deskd-reads-"))
deskd.SESSIONS = tmp
dumps, real = [0], pickle.dumps
pickle.dumps = lambda *a, **k: (dumps.__setitem__(0, dumps[0] + 1), real(*a, **k))[1]
ok = []


def check(what, good, said=""):
    ok.append(bool(good))
    print(f"{'ok  ' if good else 'FAIL'} {what}" + (f": {said}" if said else ""))


def stamp():
    st = (tmp / "w.pickle").stat()
    return st.st_mtime_ns, st.st_size


def read(actor):
    """one request that changes nothing, as that actor -> (how many times the world was pickled, whether the file moved)"""
    n, was = dumps[0], stamp()
    with deskd.Session("w", actor):
        pass
    return dumps[0] - n, stamp() != was


try:
    with deskd.Session("w", "alex") as desk:                     # the world is made and saved
        pass
    read("alex")
    n, moved = read("alex")
    check("a second read by the same actor pickles the world once and writes nothing", n == 1 and not moved, f"{n} pickle(s), file {'moved' if moved else 'still'}")
    # a line, then reads: the event keeps the actor's name, and the next request brings the name as a new string
    with deskd.Session("w", "".join(["al", "ex"])) as desk:
        r = desk.dispatch("desk", {"line": f'look; do create {desk.world.root} kind=note title="second"'})
        made = len(desk.world.events)
    check("(the line made an event by alex)", made and desk.world.events[-1]["by"] == "alex", str(r.get("error") or made))
    n, moved = read("".join(["a", "lex"]))
    check("the read after a line writes nothing (the same world pickles to the same bytes)", n == 1 and not moved, f"{n} pickle(s), file {'moved' if moved else 'still'}")
    # someone the world has not met reads: whatever that costs once, it then settles, and nothing is lost
    for _ in range(2):
        read("rowan")
        read("alex")
    a, b = read("rowan"), read("alex")
    check("two actors taking turns settle: each read pickles once and writes nothing", a == (1, False) and b == (1, False), f"rowan {a}, alex {b}")
    with deskd.Session("w", "alex") as desk:
        check("the world is whole after all of it", len(desk.world.events) == made, f"{len(desk.world.events)} events, {made} made")
    # a change is still saved, and seen by the next request
    was = stamp()
    with deskd.Session("w", "alex") as desk:
        desk._views = {"alex": {"lens": "x", "boxes": {"a": "1x1"}}}
    deskd._DESKS.clear()                                        # as another process would read it: from the file
    with deskd.Session("w", "alex") as desk:
        check("a change is saved to the file", stamp() != was and getattr(desk, "_views", {}).get("alex", {}).get("lens") == "x")
    # a painter's report: the scenes and the event count built for the file as it was stand for the file as it is now
    old, new = (1, 10), (2, 11)
    deskd._SCENES.clear()
    deskd._SCENES[("w", "alex", "board", "painter") + old + (None, 5, None)] = ("g1", b"scene of w")
    deskd._SCENES[("other", "alex", "board", "painter") + old + (None, 5, None)] = ("g2", b"scene of other")
    deskd._SCENES[("w", "alex", "older", "painter") + (0, 9) + (None, 5, None)] = ("g3", b"an older w")
    deskd._EVENTS["w"] = old + (7,)
    deskd._report_only("w", old, new)
    check("a report keeps the scenes of the world it was written into", deskd._SCENES.get(("w", "alex", "board", "painter") + new + (None, 5, None)) == ("g1", b"scene of w"))
    check("and no other: another world's scene, and one of an older file, stay where they were",
          ("other", "alex", "board", "painter") + old + (None, 5, None) in deskd._SCENES and ("w", "alex", "older", "painter") + (0, 9) + (None, 5, None) in deskd._SCENES
          and len(deskd._SCENES) == 3)
    check("the event count stands for the new file", deskd._EVENTS["w"] == new + (7,))
finally:
    pickle.dumps = real
    shutil.rmtree(tmp, ignore_errors=True)
print("all ok" if all(ok) else f"{ok.count(False)} FAILED")
sys.exit(0 if all(ok) else 1)
