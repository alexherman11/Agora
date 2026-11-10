"""Offline exact world passages; no Desk, network, session or host access."""
import difflib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = {"a5486": "home-viewer.lens", "a6194": "view.verb", "a6782": "open-found.verb"}


def patches():
    originals = json.loads((HERE / "originals.json").read_text(encoding="utf-8"))
    result = {}
    for item, file in FILES.items():
        old = originals[item]
        new = (HERE / file).read_text(encoding="utf-8").rstrip("\n")
        a, b = old.splitlines(keepends=True), new.splitlines(keepends=True)
        hunks = []
        for group in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_grouped_opcodes(3):
            hunks.append({"old": "".join(a[group[0][1]:group[-1][2]]),
                          "new": "".join(b[group[0][3]:group[-1][4]])})
        result[item] = hunks
    return result


def prepare(texts, hunks, reverse=False):
    """Return replacements only after ALL passages match uniquely.

    Caller supplies saved live text. Changes outside the hunks survive; overlapping
    drift refuses the whole plan. No live apply is implemented here.
    """
    result = dict(texts)
    for item, passages in hunks.items():
        for h in passages:
            before, after = (h["new"], h["old"]) if reverse else (h["old"], h["new"])
            if not before or result[item].count(before) != 1:
                raise ValueError(f"{item}: passage changed or ambiguous; re-read before applying")
            result[item] = result[item].replace(before, after, 1)
    return result


if __name__ == "__main__":
    print(json.dumps(patches(), ensure_ascii=False, indent=2))
