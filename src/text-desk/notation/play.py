"""Drive a desk by hand: python play.py <task> [variant] then type commands, or pipe a script.
Each line is one tool call. Lines starting with '#' are comments. A line 'assess' prints the checks.
Multi-line apply bodies: use '\\n' inside the line to separate lines.
"""

import json
import sys

from tasks import assess, build

task = sys.argv[1] if len(sys.argv) > 1 else "harbor"
variant = sys.argv[2] if len(sys.argv) > 2 else "outline"
desk = build(task, variant)
print(f"# task {task} / variant {variant}\n# prompt: {__import__('tasks').TASKS[task]}\n")
for raw in sys.stdin:
    line = raw.rstrip("\n").replace("\\n", "\n")
    if not line.strip() or line.startswith("#"):
        continue
    if line.strip() == "assess":
        print(json.dumps(assess(task, desk), indent=1))
        continue
    print(f"> {line}")
    r = desk.dispatch("desk", {"line": line})
    print(r.get("text") or ("ERR " + r["error"]))
    print()
