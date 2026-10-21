"""sayings_cost (a6153): what one `sayings` row source costs, and where its time goes.

    python research/window-lab/press-speed/sayings_cost.py <world> ["for:alex answered=no item!=a5080 eid>e10993"] [--as alex] [--profile 25]

Reads the world copy once (never written), then asks the source as a lens build would (scene.rows) five times and
prints each time, the row count, and with --profile the top functions of the last ask.
"""
import shutil
import sys
import tempfile
import time
from pathlib import Path

NOTATION = Path(__file__).resolve().parents[3] / "research" / "text-desk-lab" / "notation"
sys.path.insert(0, str(NOTATION))

import deskd       # noqa: E402
import scene       # noqa: E402


def main(argv):
    world = argv[0]
    opt = lambda k, d: argv[argv.index(k) + 1] if k in argv else d      # noqa: E731
    terms = argv[1] if len(argv) > 1 and not argv[1].startswith("--") else "for:alex answered=no item!=a5080 eid>e10993"
    tmp = Path(tempfile.mkdtemp(prefix="sayings-cost-"))
    shutil.copyfile(NOTATION / "sessions" / f"{world}.pickle", tmp / "bench.pickle")
    deskd.SESSIONS = tmp
    with deskd.Session("bench", opt("--as", "alex"), read=True) as desk:
        for k in range(5):
            t = time.perf_counter()
            if k == 4 and "--profile" in argv:
                import cProfile
                import pstats
                pr = cProfile.Profile()
                rs = pr.runcall(scene.rows, desk, "sayings " + terms)
                pstats.Stats(pr).sort_stats("cumulative").print_stats(int(opt("--profile", "25")))
            else:
                rs = scene.rows(desk, "sayings " + terms)
            print(f"sayings {terms}: {len(rs)} rows in {(time.perf_counter() - t) * 1000:.1f} ms")
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1:])
