"""lens_cost (a6153): a home-base build after a press, split by the lens each part belongs to (its own time, not the
lenses it places), on a scratch copy with a log and the house staged (as bench_board --stage).

    python research/window-lab/press-speed/lens_cost.py <world> [--as alex] [--lens home-base] [--line "<desk line>"]
"""
import pickle
import shutil
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

NOTATION = Path(__file__).resolve().parents[3] / "research" / "text-desk-lab" / "notation"
sys.path.insert(0, str(NOTATION))

import deskd       # noqa: E402
import lens_ir     # noqa: E402
import scene       # noqa: E402
import store       # noqa: E402


def main(argv):
    world = argv[0]
    opt = lambda k, d: argv[argv.index(k) + 1] if k in argv else d      # noqa: E731
    who, lens = opt("--as", "alex"), opt("--lens", "home-base")
    line = opt("--line", "look a5670; do prop a5670 shelf=no")
    tmp = Path(tempfile.mkdtemp(prefix="lens-cost-"))
    shutil.copyfile(NOTATION / "sessions" / f"{world}.pickle", tmp / "bench.pickle")
    deskd.SESSIONS = tmp
    import reports
    reports.ROOT = tmp / "reports"
    store.genesis(pickle.loads((tmp / "bench.pickle").read_bytes()), tmp / "bench.pickle", why="lens_cost")
    deskd.HOLD[0] = True
    own, stack = defaultdict(float), []
    real = lens_ir.compile_lens

    def compile_lens(desk, s, *a, **k):
        t = time.perf_counter()
        stack.append([s["title"], 0.0])
        try:
            return real(desk, s, *a, **k)
        finally:
            name, inner = stack.pop()
            spent = time.perf_counter() - t
            own[name] += spent - inner
            if stack:
                stack[-1][1] += spent
    lens_ir.compile_lens = compile_lens

    def build():
        with deskd.Session("bench", who, read=True) as desk:
            t = time.perf_counter()
            scene.scene_for(desk, lens, text=False)
            return (time.perf_counter() - t) * 1000
    build()
    for k in range(3):
        with deskd.Session("bench", who) as desk:
            for ln in line.split(";"):
                desk.repl(ln.strip().replace("shelf=no", "shelf=yes") if k % 2 else ln.strip())
        own.clear()
        ms = build()
        print(f"build {k + 1}: {ms:.0f} ms; by lens (own time): " + ", ".join(f"{n} {v * 1000:.0f}" for n, v in sorted(own.items(), key=lambda kv: -kv[1])[:12]))
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1:])
