"""scene_cost (a6153): where one scene request's time goes after the build, and what its bytes are made of.

    python research/window-lab/press-speed/scene_cost.py <world> [--as alex] [--lens home-base] [--line "<desk line>"]

On a scratch copy with a log (as bench_board.py): builds the scene once cold, makes the change (--line, or a touch),
then times each stage of deskd's /api/scene answer separately (the build, the painter view, the text, the hash's
encoding, the body's encoding) and says which fields of the painter view hold the bytes. The world is never written.
"""
import json
import pickle
import shutil
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

NOTATION = Path(__file__).resolve().parents[3] / "research" / "text-desk-lab" / "notation"
sys.path.insert(0, str(NOTATION))

import deskd       # noqa: E402
import scene       # noqa: E402
import store       # noqa: E402


def main(argv):
    world = argv[0]
    opt = lambda k, d: argv[argv.index(k) + 1] if k in argv else d      # noqa: E731
    who, lens, line = opt("--as", "alex"), opt("--lens", "home-base"), opt("--line", "")
    tmp = Path(tempfile.mkdtemp(prefix="scene-cost-"))
    shutil.copyfile(NOTATION / "sessions" / f"{world}.pickle", tmp / "bench.pickle")
    deskd.SESSIONS = tmp
    import reports
    reports.ROOT = tmp / "reports"
    store.genesis(pickle.loads((tmp / "bench.pickle").read_bytes()), tmp / "bench.pickle", why="scene_cost")
    deskd.HOLD[0] = True

    def build():
        t = {}
        with deskd.Session("bench", who, read=True) as desk:
            t0 = time.perf_counter()
            sc, text = scene.scene_for(desk, lens)
            t["build+text"] = time.perf_counter() - t0
            t1 = time.perf_counter()
            pv = dict(scene.painter_view(sc), **{"def": sc.get("def")})
            t["painter_view"] = time.perf_counter() - t1
            out = {"scene": pv, "text": text, "events_total": len(desk.world.events)}
        t2 = time.perf_counter()
        json.dumps(out, ensure_ascii=False, sort_keys=True).encode("utf-8")
        t["hash dumps"] = time.perf_counter() - t2
        t3 = time.perf_counter()
        body = json.dumps(out, ensure_ascii=False).encode("utf-8")
        t["body dumps"] = time.perf_counter() - t3
        return t, out, body, sc
    build()
    if line:
        with deskd.Session("bench", who) as desk:
            for ln in line.split(";"):
                print(desk.repl(ln.strip())[:120].replace("\n", " | "))
    else:
        (tmp / "bench.pickle").touch()
    for _ in range(2):
        t, out, body, sc = build()
        print("  ".join(f"{k} {v * 1000:.0f} ms" for k, v in t.items()), f"| body {len(body) // 1024} KB, text {len(out['text']) // 1024} KB")
    sizes = Counter()
    nodes = [0]

    def walk(n):
        nodes[0] += 1
        for k, v in n.items():
            if k == "kids":
                continue
            sizes[k] += len(json.dumps(v, ensure_ascii=False))
        for k in n.get("kids") or []:
            walk(k)
    walk(out["scene"])
    print(f"{nodes[0]} painted nodes; bytes by field: " + ", ".join(f"{k} {v // 1024} KB" for k, v in sizes.most_common(12)))
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1:])
