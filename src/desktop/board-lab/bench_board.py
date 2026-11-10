"""bench_board (a6010): what one press on the home base costs on the server, stage by stage, and where a build's time goes.

    python src/desktop/board-lab/bench_board.py <world> [--as alex] [--lens home-base] [--presses 4]
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

NOTATION = Path(__file__).resolve().parents[3] / "src" / "text-desk" / "notation"
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
    staged = None
    if "--stage" in argv:
        # a6153: the house and the host as the home base meets them (hud_playtest.py's staging): residents at work, six
        # windows, and the host's verbs, as witnessed rows. Without them the bench builds a quieter home base than Alex's
        import os
        import witnessed
        sys.path.insert(0, str(NOTATION.parents[1] / "desktop"))
        import host_verbs
        staged = NOTATION / "house-state" / "bench"
        staged.mkdir(parents=True, exist_ok=True)
        wins = [("Visual Studio Code", "Code.exe"), ("Inbox - Mail", "olk.exe"), ("Music", "Spotify.exe"),
                ("Agora notation - Terminal", "WindowsTerminal.exe"), ("Docs - Edge", "msedge.exe"), ("Files", "explorer.exe")]
        witnessed.write("bench", "desktop", [{"name": str(1000000 + i), "title": t, "program": p, "front": "yes" if i == 0 else "no"}
                                             for i, (t, p) in enumerate(wins)], by="bench")
        witnessed.write("bench", "host", host_verbs.rows(), by="hud")
        doing = {"f5189": ("jeff", "working"), "f571": ("sable", "working"), "f576": ("pike", "resting")}
        (staged / "house.json").write_text(json.dumps({"pid": os.getpid(), "beat": time.time() + 3600, "world": "bench", "workers": {},
                                                       "residents": {c: {"actor": a, "alive": True, "doing": d, "turns": 3, "last_turn": time.time()}
                                                                     for c, (a, d) in doing.items()}}), encoding="utf-8")
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
    import knife                     # --sel (a6153): where the selections' time goes, by selection, in the last build
    real_sel = knife.parse_selection

    def parse_selection(w, token, *a, **k):
        t = time.perf_counter()
        try:
            return real_sel(w, token, *a, **k)
        finally:
            spent["sel " + token] = spent.get("sel " + token, 0) + (time.perf_counter() - t) * 1000
    knife.parse_selection = parse_selection
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

    q = f"/api/scene?session=bench&as={who}&lens={lens}&view=painter" + ("" if "--text" in argv else "&text=0")
    if "--why" in argv:
        import lens_ir
        lens_ir._WHY_ON[0] = True
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
        import lens_ir
        k0, m0 = lens_ir._STATS["kept"], lens_ir._STATS["made"]
        r, ms2, kb = call(q)
        if "--rows" in argv or "--sel" in argv:
            print(f"   rows and selections, {sum(spent.values()):.0f} ms in all: " + ", ".join(
                f"{s[:60]} {v:.1f}" for s, v in sorted(spent.items(), key=lambda kv: -kv[1])[:int(opt("--sel", "8"))]))
        print(f"press {i + 1}: do {ms1:.0f} ms, scene {ms2:.0f} ms {kb} KB, kept {lens_ir._STATS['kept'] - k0} made "
              f"{lens_ir._STATS['made'] - m0}   [{said}]")
        if "--why" in argv:           # a6153: why instances were made, not kept (lens_ir._WHY)
            print("   made because: " + "; ".join(f"{k} x{v}" for k, v in lens_ir._WHY.most_common(6)))
            lens_ir._WHY.clear()
        if "--wait" in argv:          # a6153: seconds between presses, as a person leaves them (witnessed rows age)
            time.sleep(float(opt("--wait", "1")))
    import lens_ir
    print(f"instances kept {lens_ir._STATS['kept']}, made {lens_ir._STATS['made']}, builds {lens_ir._STATS['builds']}, "
          f"differed from a whole build {lens_ir._STATS['differed']} (LENS_REUSE_VERIFY=1 checks every build)")
    if prof[0] is not None:
        import pstats
        pstats.Stats(prof[0]).sort_stats(opt("--sort", "cumulative")).print_stats(int(opt("--profile", "25")))
    srv.shutdown()
    shutil.rmtree(tmp, ignore_errors=True)
    if staged is not None:
        shutil.rmtree(staged, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1:])
