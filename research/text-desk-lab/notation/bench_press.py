"""bench_press: what one press in a lens costs, stage by stage, through deskd's own request code (a4838, 14 Oct 2026).

    python bench_press.py <world> [--as alex] [--lens design-review] [--presses 5] [--nolog] [--keep]

Copies <world>.pickle to a scratch folder (the world itself is never written), gives the copy a log as the live world
has one (store.genesis; --nolog leaves it without), serves it with deskd's Handler in this process, and does what the
painter does for each Enter in a document: POST /api/do (split), GET /api/scene (forced, the whole build), POST
/api/observe (the painter's report). Prints each request's wall time and where the time went inside it.
"""
import json
import pickle
import shutil
import sys
import tempfile
import threading
import time
import urllib.request
from collections import defaultdict
from http.server import ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import deskd       # noqa: E402
import explore     # noqa: E402
import kept        # noqa: E402
import store       # noqa: E402
import scene       # noqa: E402

SPENT = defaultdict(float)
PROFILE = [False]


def timed(mod, name, label=None):
    real = getattr(mod, name)

    def wrap(*a, **k):
        t = time.perf_counter()
        try:
            return real(*a, **k)
        finally:
            SPENT[label or name] += time.perf_counter() - t
    setattr(mod, name, wrap)


def main(argv):
    world = argv[0]
    opt = lambda k, d: argv[argv.index(k) + 1] if k in argv else d      # noqa: E731
    who, lens, n = opt("--as", "alex"), opt("--lens", "design-review"), int(opt("--presses", "5"))
    tmp = Path(tempfile.mkdtemp(prefix="bench-press-"))
    src = HERE / "sessions" / f"{world}.pickle"
    shutil.copyfile(src, tmp / "bench.pickle")
    deskd.SESSIONS = tmp
    if "--nolog" not in argv:
        t = time.perf_counter()
        store.genesis(pickle.loads((tmp / "bench.pickle").read_bytes()), tmp / "bench.pickle", why="bench")
        print(f"log begun in {time.perf_counter() - t:.2f} s ({(tmp / 'bench.log.jsonl').stat().st_size // 1024} KB)")
    print(f"world {src.stat().st_size // 1024} KB")

    real_dumps, real_loads = pickle.dumps, pickle.loads
    deskd.pickle = type("P", (), {"dumps": staticmethod(lambda *a, **k: _t("pickle.dumps", real_dumps, *a, **k)),
                                  "loads": staticmethod(lambda *a, **k: _t("pickle.loads", real_loads, *a, **k))})
    timed(explore, "save_desk", "save (write file)")
    timed(explore, "take_lock", "lock wait")
    timed(kept, "sweep", "kept.sweep")
    timed(store, "safe_begin", "log begin (flatten, digest)")
    timed(store, "safe_commit", "log commit (flatten, diff, append)")
    timed(scene, "scene_for", "lens build")
    timed(deskd, "snapshot_for")
    import desk as deskmod
    real_dispatch = deskmod.Desk.dispatch

    def dispatch(self, *a, **k):
        t = time.perf_counter()
        try:
            return real_dispatch(self, *a, **k)
        finally:
            SPENT["the command itself"] += time.perf_counter() - t
    deskmod.Desk.dispatch = dispatch

    if "--profile" in argv:          # the last Enter's requests, each profiled in the thread that served it
        import cProfile
        import pstats
        for meth in ("_get", "_post"):
            real_m = getattr(deskd.Handler, meth)

            def prof(self, _real=real_m):
                if not PROFILE[0]:
                    return _real(self)
                p = cProfile.Profile()
                try:
                    return p.runcall(_real, self)
                finally:
                    print(f"--- profile of {self.path}")
                    pstats.Stats(p).sort_stats("cumulative").print_stats(int(opt("--profile", "30")) if opt("--profile", "x").isdigit() else 30)
            setattr(deskd.Handler, meth, prof)
    srv = ThreadingHTTPServer(("127.0.0.1", 0), deskd.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"

    def call(path, body=None):
        SPENT.clear()
        t = time.perf_counter()
        req = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None)
        with urllib.request.urlopen(req) as r:
            raw = r.read()
        wall = time.perf_counter() - t
        return json.loads(raw), wall, len(raw), dict(SPENT)

    def show(what, wall, size, spent):
        parts = ", ".join(f"{k} {v * 1000:.0f}" for k, v in sorted(spent.items(), key=lambda kv: -kv[1]) if v >= 0.0005)
        print(f"  {what:<8} {wall * 1000:6.0f} ms  {size // 1024:5d} KB   [{parts}]")

    q = f"/api/scene?session=bench&as={who}&lens={lens}&view=painter"
    r, wall, size, spent = call(q)
    print("first scene (cold):")
    show("scene", wall, size, spent)

    def enters(node):
        for a in node.get("acts") or []:
            if "split" in json.dumps(a):
                yield node, a
        for k in node.get("kids") or []:
            yield from enters(k)
    found = list(enters(r["scene"]))
    if not found:
        print("no part in this lens splits on Enter")
        return
    node, act = found[len(found) // 2]
    print(f"{len(found)} parts split on Enter; pressing in {node['key']}\n  act {json.dumps(act)[:300]}")
    line0 = act.get("line") or act.get("do") or ""
    total = []
    for i in range(n):
        line = line0.replace("$head", "bench").replace("$tail", f"press {i}")
        line = line.replace('"$(head)"', '"bench"')
        print(f"Enter {i + 1}: {line[:120]}")
        PROFILE[0] = i == n - 1 and "--profile" in argv
        a, w1, s1, sp1 = call("/api/do", {"session": "bench", "as": who, "line": line,
                                           "observed": {**(node.get("fence") or {}), "at": r.get("events_total")},
                                           "gesture": f"bench-{time.time()}-{i}"})
        show("do", w1, s1, sp1)
        if a.get("error"):
            print("   refused:", a["error"][:200])
        r, w2, s2, sp2 = call(q)
        show("scene", w2, s2, sp2)
        _, w3, s3, sp3 = call("/api/observe", {"session": "bench", "as": who, "lens": lens, "at": r.get("events_total"),
                                                "facts": {"x": "1"}, "boxes": {f"k{j}": "100x20" for j in range(800)}})
        show("observe", w3, s3, sp3)
        total.append(w1 + w2 + w3)
        # the next Enter is pressed on the same paragraph as it is painted now (its fence moved with the split)
        node = next((nd for nd, _a in enters(r["scene"]) if nd["key"] == node["key"]), node) if r.get("scene") else node
    print(f"each Enter, do + scene + observe: {', '.join(f'{t * 1000:.0f}' for t in total)} ms")
    srv.shutdown()
    if "--keep" not in argv:
        shutil.rmtree(tmp, ignore_errors=True)


def _t(label, f, *a, **k):
    t = time.perf_counter()
    try:
        return f(*a, **k)
    finally:
        SPENT[label] += time.perf_counter() - t


if __name__ == "__main__":
    main(sys.argv[1:])
