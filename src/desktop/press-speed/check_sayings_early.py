"""check_sayings_early (a6153): the sayings source with its early terms gives the very rows it gave without them.

    python src/desktop/press-speed/check_sayings_early.py <world>

For several viewers and term sets, compares scene.rows(desk, "sayings ...") (early terms asked first) with the rows made
whole and filtered after (saying_rows without early, then knife.filter_rows): the same rows, in the same order, with
the same fields. The world copy is never written. Prints each case and 'all the same' or the first difference.
"""
import shutil
import sys
import tempfile
from pathlib import Path

NOTATION = Path(__file__).resolve().parents[3] / "src" / "text-desk" / "notation"
sys.path.insert(0, str(NOTATION))

import deskd       # noqa: E402
import knife       # noqa: E402
import persons     # noqa: E402
import scene       # noqa: E402


def main(argv):
    world = argv[0]
    tmp = Path(tempfile.mkdtemp(prefix="sayings-early-"))
    shutil.copyfile(NOTATION / "sessions" / f"{world}.pickle", tmp / "bench.pickle")
    deskd.SESSIONS = tmp
    bad = 0
    cases = 0
    with deskd.Session("bench", "alex", read=True) as desk:
        w = desk.world
        evs = [e["id"] for e in w.events]
        chats = [i for i, n in w.nodes.items() if n["type"] == "appearance" and w.subjects[n["subject"]]["kind"] == "chat"][:4]
        cuts = [evs[len(evs) // 2], evs[-200], evs[-20], "e9999", "e100000"]
        for who in ("alex", "jeff", "sable", "claude"):
            for own in (f"for:{who}", "", f"in:{chats[0]}" if chats else ""):
                sets = [f"eid>{c}" for c in cuts] + [f"answered=no item!={chats[0]} eid>{cuts[1]}" if chats else "",
                                                     "what=comment", "what!=line eid<=" + cuts[2], f"-item={chats[1]}" if len(chats) > 1 else "",
                                                     f"source={w.nodes[chats[0]]['subject']}" if chats else "", "eid>=" + cuts[3] + " who=Alex"]
                for terms in [s for s in sets if s]:
                    cases += 1
                    src = ("sayings " + " ".join(t for t in (own, terms) if t)).strip()
                    got = scene.rows(desk, src)
                    rest = [t for t in terms.split()]
                    whole = scene.saying_rows(desk, " " + own if own else "")
                    want = knife.filter_rows(w, whole, rest, persons.active(desk), scene.SOURCES["sayings"][0])
                    if got != want or [sorted(r) for r in got] != [sorted(r) for r in want]:
                        bad += 1
                        print(f"DIFFERENT {src}: {len(got)} rows, {len(want)} the old way")
                        for a, b in zip(got, want):
                            if a != b:
                                print("  first:", {k: (a.get(k), b.get(k)) for k in set(a) | set(b) if a.get(k) != b.get(k)})
                                break
                    elif cases <= 6 or len(got):
                        print(f"same {src}: {len(got)} rows")
    print(f"{cases} cases: " + ("all the same" if not bad else f"{bad} different"))
    shutil.rmtree(tmp, ignore_errors=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
