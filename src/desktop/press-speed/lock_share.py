"""lock_share (a6153): who holds a world's lock, from deskd's trace (house-state/deskd-trace.log): per kind of request,
how many, the time held in all, and its share of the wall clock; and how long Alex's requests waited for it.

    python src/desktop/press-speed/lock_share.py [--world frontier] [--minutes 30] [--trace <path>]

Reads timing lines only (time, world, who, what, wait, held); the trace names no words of anyone's.
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

LINE = re.compile(r"^(\d\d):(\d\d):(\d\d) (\S+) (\S+) (\S+)(?: .*?)? wait=(\d+) held=(\d+)")


def main(argv):
    opt = lambda k, d: argv[argv.index(k) + 1] if k in argv else d      # noqa: E731
    world, minutes = opt("--world", "frontier"), float(opt("--minutes", "30"))
    trace = Path(opt("--trace", str(Path(__file__).resolve().parents[3] / "src" / "text-desk" / "notation"
                                   / "house-state" / "deskd-trace.log")))
    rows = []
    for ln in trace.read_text(encoding="utf-8", errors="replace").splitlines():
        m = LINE.match(ln)
        if m and m.group(4) == world:
            t = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
            rows.append((t, m.group(5), m.group(6), int(m.group(7)), int(m.group(8))))
    if not rows:
        return print("no lines for", world)
    end = rows[-1][0]
    rows = [r for r in rows if 0 <= end - r[0] <= minutes * 60]
    span = max(1, rows[-1][0] - rows[0][0])
    by = defaultdict(lambda: [0, 0])
    for _t, who, what, _w, held in rows:
        kind = what.split(":")[0] + (":" + what.split(":")[1] if what.startswith("scene:") else "")
        k = ("alex " if who == "alex" else "others ") + kind if who != "-" else "snapshot"
        by[k][0] += 1
        by[k][1] += held
    print(f"{world}: the last {minutes:g} min of the trace ({len(rows)} requests over {span} s)")
    for k, (n, held) in sorted(by.items(), key=lambda kv: -kv[1][1])[:14]:
        print(f"  {k:40s} {n:5d} requests, held {held / 1000:7.1f} s, {held / 10 / span:5.1f} % of the time")
    waits = sorted(w for _t, who, _what, w, _h in rows if who == "alex")
    if waits:
        q = lambda p: waits[min(len(waits) - 1, int(p * len(waits)))]      # noqa: E731
        print(f"  alex's requests waited for the lock: median {q(0.5)} ms, 90th {q(0.9)} ms, most {waits[-1]} ms ({len(waits)} requests)")


if __name__ == "__main__":
    main(sys.argv[1:])
