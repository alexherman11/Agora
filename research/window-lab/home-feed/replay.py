"""Replay a real recorded transcript as if its agent were at work now (a5988): for showing a feed on a copy, where no
house runs. It copies the first part of the transcript into a scratch house-state folder, then appends the rest one
record at a time, so feeds.py (--from that folder) sees new lines arrive. Read only on the source; it writes only the
scratch copy, and stops by itself.

    python research/window-lab/home-feed/replay.py <transcript.jsonl> <actor> [--start <records>] [--every <s>] [--for <s>]

The scratch folder is research/text-desk-lab/notation/house-state/feed-replay/<actor>/ (house-state is not in git).
--start: how many records are there at once (default: all but the last 200); --every: seconds between records (0.4);
--for: seconds before it stops (120)."""
import pathlib
import sys
import time

NOTATION = pathlib.Path(__file__).resolve().parents[2] / "text-desk-lab" / "notation"
SCRATCH = NOTATION / "house-state" / "feed-replay"


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    opt = lambda k, d: type(d)(argv[argv.index(k) + 1]) if k in argv else d       # noqa: E731
    src, actor = pathlib.Path(argv[0]), argv[1]
    lines = src.read_bytes().splitlines(keepends=True)
    start = opt("--start", max(0, len(lines) - 200))
    out = SCRATCH / actor / "transcript.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(b"".join(lines[:start]))
    print(f"replay: {start} of {len(lines)} records in {out}; the rest one every {opt('--every', 0.4)} s", flush=True)
    until = time.time() + opt("--for", 120.0)
    for raw in lines[start:]:
        if time.time() >= until:
            break
        time.sleep(opt("--every", 0.4))
        with out.open("ab") as f:
            f.write(raw)
    print("replay: done", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
