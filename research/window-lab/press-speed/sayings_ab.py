"""sayings_ab (a6153): saying_rows for one viewer made whole, then with early terms; each timed (median of 7).

    python research/window-lab/press-speed/sayings_ab.py <world> [for:alex] ["item!=a5080 eid>e10993"]
"""
import shutil
import statistics
import sys
import tempfile
import time
from pathlib import Path

NOTATION = Path(__file__).resolve().parents[3] / "research" / "text-desk-lab" / "notation"
sys.path.insert(0, str(NOTATION))

import deskd       # noqa: E402
import persons     # noqa: E402
import scene       # noqa: E402


def main(argv):
    world = argv[0]
    own = argv[1] if len(argv) > 1 else "for:alex"
    pre = (argv[2] if len(argv) > 2 else "item!=a5080 eid>e10993").split()
    tmp = Path(tempfile.mkdtemp(prefix="sayings-ab-"))
    shutil.copyfile(NOTATION / "sessions" / f"{world}.pickle", tmp / "bench.pickle")
    deskd.SESSIONS = tmp
    with deskd.Session("bench", "alex", read=True) as desk:
        for name, early in (("whole", None), ("early", (pre, persons.active(desk)))):
            ts = []
            for _ in range(7):
                t = time.perf_counter()
                rs = scene.saying_rows(desk, " " + own, early=early)
                ts.append((time.perf_counter() - t) * 1000)
            print(f"{name}: {len(rs)} rows, {statistics.median(ts):.1f} ms (median of 7)")
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1:])
