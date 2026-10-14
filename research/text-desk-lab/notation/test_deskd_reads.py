"""deskd, a4465 (13 Oct): a request that only reads pickles the world once and writes nothing. a4869 (14 Oct): a
painter's report is kept by the house beside the world (reports.py), never in it, and does not outlive the house.

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
import explore    # noqa: E402

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
        desk.dispatch("desk", {"line": f'look; do create {desk.world.root} kind=note title="third"'})
    deskd._DESKS.clear()                                        # as another process would read it: from the file
    with deskd.Session("w", "alex") as desk:
        check("a change is saved to the file", stamp() != was and "third" in [s["title"] for s in desk.world.subjects.values()])

    # a4869: a painter's report is kept by the house beside the world, never in it
    import json
    import threading
    import urllib.request
    from http.server import ThreadingHTTPServer
    import reports
    reports.ROOT = tmp / "reports"
    srv = ThreadingHTTPServer(("127.0.0.1", 0), deskd.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    def post(path, body):
        req = urllib.request.Request(f"http://127.0.0.1:{srv.server_address[1]}{path}", json.dumps(body).encode())
        try:
            with urllib.request.urlopen(req) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            return json.loads(e.read())

    def say(line, actor="rowan"):
        return post("/api/do", {"session": "w", "as": actor, "line": line}).get("text") or ""

    say(f'look; do create {desk.world.root} kind=note tags=lens title=boxy text="root : column\\n  a : text \\"seen\\""')
    say("scene boxy")
    deskd._DESKS.clear()
    was, n = stamp(), dumps[0]
    r = post("/api/observe", {"session": "w", "as": "Alex", "lens": "Boxy", "at": 3, "boxes": {"root": "900x40", "root/a": "900x40"},
                              "facts": {"x": "1"}, "viewport": {"w": 1000, "h": 800, "sx": 0, "sy": 0}})
    check("a report is answered as before", r == {"ok": True, "kept": 1}, str(r))
    check("a report neither loads nor writes the world", stamp() == was and dumps[0] == n, f"file {'moved' if stamp() != was else 'still'}, {dumps[0] - n} pickle(s)")
    out = say("scene boxy root")
    check("scene reads it: the viewer, what it reported, and its age", "~ alex is looking: 1000x800 at scroll 0,0" in out
          and "~ alex: 900x40px" in out and "(0 s ago)" in out, out)
    post("/api/observe", {"session": "w", "as": "alex", "lens": "boxy", "at": 3, "boxes": {"root": "700x40"}})
    out = say("scene boxy root")
    check("one per viewer, the last wins; attention not shared is said so", "700x40px" in out and "900x40px" not in out
          and out.count("~ alex ") == 1 and "attention not shared" in out, out)
    check("scene ok gives the age", "painted sizes, oldest first: alex 0 s ago" in say("scene boxy ok"))
    r = post("/api/observe", {"session": "nowhere", "as": "alex", "lens": "boxy"})
    check("a report of a world that does not exist makes no world", "error" in r and not (tmp / "nowhere.pickle").exists(), str(r))
    # a world saved before a4869 holds a report inside it: never read, and gone with the next change
    with deskd.Session("w", "alex") as desk:
        pass
    old = pickle.loads((tmp / "w.pickle").read_bytes())
    old._views = {"jeff": {"lens": "boxy", "at": 1, "time": "2026-10-13T20:00:00", "boxes": {"root": "1x1"}, "painted": None}}
    explore.save_desk(tmp / "w.pickle", old, real(old))
    deskd._DESKS.clear()
    out = say("scene boxy root")
    check("a report saved in the world before is not shown", "~ jeff" not in out, out)
    say(f'look; do create {desk.world.root} kind=note title="fourth"')
    check("and leaves the file with the next change", not hasattr(pickle.loads((tmp / "w.pickle").read_bytes()), "_views"))
    # the house starts again: a report does not outlive it
    reports.serve("another house", "2026-10-14T07:05:00")
    out = say("scene boxy root")
    check("after a restart no report from before it is shown, and scene says since when",
          "~ alex" not in out and "no viewer has reported painting this lens since the house started (" in out, out)
    check("scene ok says so too", "none reported since the house started (" in say("scene boxy ok"), say("scene boxy ok"))
    check("and its files are gone", [p.name for p in (tmp / "reports" / "w").iterdir()] == ["host.json"])
    post("/api/observe", {"session": "w", "as": "alex", "lens": "boxy", "at": 3, "boxes": {"root": "500x40"}})
    check("the next report is shown", "500x40px" in say("scene boxy root"))
    srv.shutdown()
finally:
    pickle.dumps = real
    shutil.rmtree(tmp, ignore_errors=True)
print("all ok" if all(ok) else f"{ok.count(False)} FAILED")
sys.exit(0 if all(ok) else 1)
