"""Read public lens fixtures only; never fetch/send/apply on a shared world."""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "text-desk-lab" / "notation"))
import scene
import wait_patches

bases = json.loads((HERE / "world-bases-20261022.json").read_text(encoding="utf-8"))
for name, original in bases.items():
    changed = wait_patches.apply(name, original)
    # Syntax-only fixture: the public role names are admitted here, not their
    # live style values. This is not style, world evaluation or pixel proof.
    roles = set(re.findall(r"^\s*role ([\w.-]+)", original, re.M))
    scene.parse(changed, roles=roles)
    assert changed.count("captures=current") == 2
    assert changed.count('capture_generation="$(($draft.capture_generation or "0"))"') == 2
    assert wait_patches.apply(name, changed, inverse=True) == original
    # Native document comments and original-place replies are deliberately
    # untouched: this slice opts in only the existing capture-bearing actions.
    old_other = [s for s in original.splitlines() if "on edit" in s and 'captures="$draft.context"' not in s]
    new_other = [s for s in changed.splitlines() if "on edit" in s and "captures=current" not in s]
    assert old_other == new_other
    print(f"{name}: parsed staged hunks; 2 native Send opt-ins; exact inverse; other routes unchanged")
