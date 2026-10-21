"""routes.py (a7544): every line in the Home base's lenses and verbs that writes or reads the viewer's legacy fields
(viewing=, with=, back=) or calls view/unview, so routes that bypass `browse` can be named. Reads only.

    python research/window-lab/browsing/tabs/review/routes.py [--port 8794] [--world frontier]
"""
import argparse
import re

import tabs_world as W

NOTES = ["a5210", "a5439", "a5478", "a5480", "a5484", "a5486", "a5544", "a5548", "a5564", "a5692", "a5715", "a6194",
         "a6352", "a6782", "a6790", "a6771"]
PAT = re.compile(r"(viewing=|\bwith=|\bback=|do view\b|do unview\b|on link|open-found|do browse)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8794)
    ap.add_argument("--world", default="frontier")
    a = ap.parse_args()
    do = lambda line: W.door(f"http://127.0.0.1:{a.port}", a.world, "worker-a7544", line)  # noqa: E731
    for n in NOTES:
        said = do(f"read {n} :3")
        head = next((l for l in said.splitlines() if "appears at" in l), n)
        hits = [(i + 1, l) for i, l in enumerate(W.body(said).splitlines()) if PAT.search(l) and not l.lstrip().startswith("#")]
        print(f"{n} {head[:70]}: {len(hits)}")
        for i, l in hits:
            print(f"   {i:4} {l.strip()[:150]}")


if __name__ == "__main__":
    main()
