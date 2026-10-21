"""store_size (a6153): how many stores of kept instances (lens_ir._REUSE) one page leaves, and about how big they are.

    python research/window-lab/press-speed/store_size.py <world> [--as alex] [--lens home-base]

Builds the lens twice on a scratch copy (never written) and prints the number of stores, the instances in them, and
their pickled size (a measure of what they hold, not of Python's memory, which is a few times more).
"""
import pickle
import shutil
import sys
import tempfile
from pathlib import Path

NOTATION = Path(__file__).resolve().parents[3] / "research" / "text-desk-lab" / "notation"
sys.path.insert(0, str(NOTATION))

import deskd       # noqa: E402
import lens_ir     # noqa: E402
import scene       # noqa: E402


def main(argv):
    world = argv[0]
    opt = lambda k, d: argv[argv.index(k) + 1] if k in argv else d      # noqa: E731
    tmp = Path(tempfile.mkdtemp(prefix="store-size-"))
    shutil.copyfile(NOTATION / "sessions" / f"{world}.pickle", tmp / "bench.pickle")
    deskd.SESSIONS = tmp
    for _ in range(2):
        with deskd.Session("bench", opt("--as", "alex"), read=True) as desk:
            sc, _t = scene.scene_for(desk, opt("--lens", "home-base"), text=False)
    stores = lens_ir._REUSE
    n = sum(len(v) for v in stores.values())
    size = len(pickle.dumps(dict(stores), protocol=pickle.HIGHEST_PROTOCOL))
    whole = len(pickle.dumps(sc, protocol=pickle.HIGHEST_PROTOCOL))
    print(f"{len(stores)} stores, {n} instances, {size // 1024} KB pickled (the scene itself: {whole // 1024} KB)")
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1:])
