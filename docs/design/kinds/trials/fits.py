"""P3. The kernel's plain-verb rule (kernel.py plain_verb.fits): a family word fits a kind when its namespace is the
kind, or a hyphen part of it, or <kind> appears in its usage. List the fits the hyphen part alone makes, for judging."""
import collections
from world import load, PATH
live, _ = load(PATH)
kinds = sorted({a["kind"] for a in live.values()})
words = [(t, a) for t, a in live.items() if a["kind"] == "word" and "." in str(a.get("word"))]
by_hyphen = collections.defaultdict(list)
for t, a in words:
    ns, verb = str(a["word"]).rsplit(".", 1)
    usage = (str(a.get("help") or "").splitlines() or [""])[0]
    for kd in kinds:
        if "-" in kd and ns != kd and ns in kd.split("-") and f"<{kd}" not in usage:
            by_hyphen[kd].append(a["word"])
for kd, ws in sorted(by_hyphen.items()):
    print(f"{kd}: {len(ws)} family words fit by name part: {' '.join(sorted(ws))}")
