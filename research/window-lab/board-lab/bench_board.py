"""bench_board (a6010): what one press on the home base costs on the server, stage by stage, and where a build's time goes.

    python research/window-lab/board-lab/bench_board.py <world> [--as alex] [--lens home-base] [--presses 4]
                                                        [--line "do prop a5441 probe={i}"] [--profile 25]

As bench_press.py (which it borrows from), on a scratch copy of the world: serves it with deskd's own Handler in this
process, then for each press POST /api/do (the line, {i} the press's number) and GET /api/scene (the whole build, as the
painter's refresh asks it). Prints each request's wall time and size; --profile N prints the last build's top N
functions by cumulative time. The world itself is never written.
"""
import json
import shutil
import sys
import tempfile
import threading
import time
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

NOTATION = Path(__file__).resolve().parents[3] / "research" / "text-desk-lab" / "notation"
sys.path.insert(0, str(NOTATION))

import deskd       # noqa: E402
import scene       # noqa: E402


def main(argv):
    world = argv[0]
    opt = lambda k, d: argv[argv.index(k) + 1] if k in argv else d      # noqa: E731
    who, lens, n = opt("--as", "alex"), opt("--lens", "home-base"), int(opt("--presses", "4"))
    lines = [l.strip() for l in opt("--line", "").split("||")]       # several: press i uses line i (the last again)
    if "--verify" in argv:           # every build made twice, kept and whole, and any difference counted (lens_ir)
        import os
        os.environ["LENS_REUSE_VERIFY"] = "1"
    tmp = Path(tempfile.mkdtemp(prefix="bench-board-"))
    shutil.copyfile(NOTATION / "sessions" / f"{world}.pickle", tmp / "bench.pickle")
    deskd.SESSIONS, deskd.STATIC = tmp, NOTATION / "desk-shell"
    import reports
    reports.ROOT = tmp / "reports"
    import pickle
    import store                     # the live world has a log (Snappy Desk): without one every write pickles it twice
    store.genesis(pickle.loads((tmp / "bench.pickle").read_bytes()), tmp / "bench.pickle", why="bench")
    srv = ThreadingHTTPServer(("127.0.0.1", 0), deskd.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    deskd.HOLD[0], deskd.PORT[0] = True, srv.server_address[1]
    threading.Thread(target=deskd._snapshotter, daemon=True).start()
    prof = [None]
    real_scene_for = scene.scene_for

    def scene_for(*a, **k):
        if prof[0] is None or "--profile-do" in argv or "--profile-get" in argv:
            return real_scene_for(*a, **k)
        return prof[0].runcall(real_scene_for, *a, **k)
    scene.scene_for = scene_for
    real_rows, spent = scene.rows, {}

    def rows(desk, source, *a, **k):         # where the row sources' time goes, by source, in the last build
        t = time.perf_counter()
        try:
            return real_rows(desk, source, *a, **k)
        finally:
            spent[source] = spent.get(source, 0) + (time.perf_counter() - t) * 1000
    scene.rows = rows
    real_post = deskd.Handler._post

    def post(self):
        if prof[0] is None or "--profile-do" not in argv:
            return real_post(self)
        return prof[0].runcall(real_post, self)
    deskd.Handler._post = post
    real_get = deskd.Handler._get

    def get(self):                   # --profile-get: the whole scene request (build, painter view, hash, encode)
        if prof[0] is None or "--profile-get" not in argv:
            return real_get(self)
        return prof[0].runcall(real_get, self)
    deskd.Handler._get = get

    def call(path, body=None):
        t = time.perf_counter()
        req = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None)
        with urllib.request.urlopen(req) as r:
            raw = r.read()
        return json.loads(raw), (time.perf_counter() - t) * 1000, len(raw) // 1024

    q = f"/api/scene?session=bench&as={who}&lens={lens}&view=painter"
    r, ms, kb = call(q)
    print(f"first scene (cold) {ms:.0f} ms {kb} KB")
    r, ms, kb = call(q)
    print(f"again, nothing changed {ms:.0f} ms {kb} KB")
    for i in range(n):
        if i == n - 1 and "--profile-do" in argv:
            import cProfile
            prof[0] = cProfile.Profile()
        line0 = lines[min(i, len(lines) - 1)]
        if line0:
            a, ms1, _ = call("/api/do", {"session": "bench", "as": who, "line": line0.replace("{i}", str(i)),
                                         "observed": {"at": r.get("events_total")}, "gesture": f"bench-{time.time()}-{i}"})
            said = (a.get("error") or a.get("text") or "")[:100].replace("\n", " | ")
        else:
            ms1, said = 0, "(no press: a change the scene key sees is made by touching the world file)"
            (tmp / "bench.pickle").touch()
        if i == n - 1 and "--profile-do" in argv:
            pass
        elif i == n - 1 and "--profile" in argv:
            import cProfile
            prof[0] = cProfile.Profile()
        spent.clear()
        r, ms2, kb = call(q)
        if "--rows" in argv:
            print("   rows: " + ", ".join(f"{s[:40]} {v:.0f}" for s, v in sorted(spent.items(), key=lambda kv: -kv[1])[:6]))
        print(f"press {i + 1}: do {ms1:.0f} ms, scene {ms2:.0f} ms {kb} KB   [{said}]")
    import lens_ir
    print(f"instances kept {lens_ir._STATS['kept']}, made {lens_ir._STATS['made']}, builds {lens_ir._STATS['builds']}, "
          f"differed from a whole build {lens_ir._STATS['differed']} (LENS_REUSE_VERIFY=1 checks every build)")
    if prof[0] is not None:
        import pstats
        pstats.Stats(prof[0]).sort_stats("cumulative").print_stats(int(opt("--profile", "25")))
    srv.shutdown()
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1:])
