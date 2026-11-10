"""Exact source integration for a7045's unlanded adapter. Pure transform.

No script writes another worktree. --diff FILE prints a reviewable patch only.
The house/builder integrates this after checking its old passages.
"""
from pathlib import Path
import difflib
import sys

HUNKS = [
    ('a.ghost?.remove(); a.preview?.remove();',
     'a.ghost?.remove(); a.preview?.remove();\n      if (cancel) a.external?.cancel();'),
    ('      if (!cancel && a.next) {',
     '''      if (!cancel && a.external?.target) {
        pending = true;
        a.external.release().finally(() => { pending = false; api.refresh(); });
        render(a.g);
      } else if (!cancel && a.next) {
        a.external?.cancel();'''),
    ('      } else { render(a.g); api.refresh(); }\n    }\n    function carry',
     '      } else { a.external?.cancel(); render(a.g); api.refresh(); }\n    }\n    function carry'),
    ('          active = { kind: "carry", g, ghost, preview, whole, next: null };',
     '''          active = { kind: "carry", g, ghost, preview, whole, next: null,
            external: host.CarryTargets?.session(paint, { el: grip, n: grip._n }, api.send, g.el) };'''),
    ('        const target = P.hit(rect(g.el), g.geometry.boxes, pagePoint(g, m), id);',
     '''        if (active.external?.move(m)) {
          active.next = null; active.preview.hidden = true; return;
        }
        const target = P.hit(rect(g.el), g.geometry.boxes, pagePoint(g, m), id);'''),
]


def patched(text):
    # Preflight ALL anchors before changing any source.
    for old, _ in HUNKS:
        if text.count(old) != 1:
            raise ValueError("partition hook passage moved: " + old[:90])
    for old, new in HUNKS:
        text = text.replace(old, new, 1)
    return text


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] != "--diff":
        raise SystemExit("usage: partition_hook.py --diff <partition-ui.js>; prints only")
    source = Path(sys.argv[2]).read_text(encoding="utf-8")
    print("".join(difflib.unified_diff(source.splitlines(True), patched(source).splitlines(True),
                                    "a/partition-ui.js", "b/partition-ui.js")))
