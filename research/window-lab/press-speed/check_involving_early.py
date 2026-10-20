"""check_involving_early (a6638): `sayings involving:<name>` with scene.INVOLVING_EARLY on and off must give the same rows,
field for field, for every person of a world; and how long each takes.

    python research/window-lab/press-speed/check_involving_early.py <world>

Reads a copy of the world (never written). Exits 1 on any difference.
"""
import shutil
import sys
import tempfile
import time
from pathlib import Path

NOTATION = Path(__file__).resolve().parents[3] / "research" / "text-desk-lab" / "notation"
sys.path.insert(0, str(NOTATION))

import deskd       # noqa: E402
import persons     # noqa: E402
import scene       # noqa: E402


def timed(desk, src, on):
    scene.INVOLVING_EARLY = on
    best, rows = None, None
    for _ in range(3):
        t = time.perf_counter()
        rows = scene.rows(desk, src)
        ms = (time.perf_counter() - t) * 1000
        best = ms if best is None else min(best, ms)
    return rows, best


def main(argv):
    world = argv[0]
    tmp = Path(tempfile.mkdtemp(prefix="involving-early-"))
    shutil.copyfile(NOTATION / "sessions" / f"{world}.pickle", tmp / "bench.pickle")
    deskd.SESSIONS = tmp
    bad = 0
    with deskd.Session("bench", "alex", read=True) as desk:
        w = desk.world
        names = sorted({persons.name_now(w, pid) for pid in persons.index(w).people} - {""})
        for name in names:
            src = f"sayings involving:{name}"
            off, t_off = timed(desk, src, False)
            on, t_on = timed(desk, src, True)
            same = off == on
            bad += not same
            if name in ("alex", "jeff", "pike") or not same:
                print(f"{src}: {len(on)} rows, {t_off:.1f} ms -> {t_on:.1f} ms, {'same' if same else 'DIFFERENT'}")
        print(f"{len(names)} persons, {bad} different")
    shutil.rmtree(tmp, ignore_errors=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
