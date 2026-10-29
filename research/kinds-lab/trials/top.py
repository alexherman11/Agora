"""P4. The top of the lattice already exists: words whose usage takes any <thing> or <id>. What are they, can they be undone?"""
import re
from world import load, PATH
live, _ = load(PATH)
rows = []
for t, a in live.items():
    if a["kind"] != "word": continue
    first = (str(a.get("help") or "").splitlines() or [""])[0]
    m = re.search(r"<([a-z][a-z0-9-]*)", first)
    if m and m.group(1) in ("thing", "id", "anything"):
        rows.append((a.get("word_kind"), str(a.get("undo")), a["word"], a.get("from"), first[:110]))
for r in sorted(rows, key=lambda r: (str(r[0]), r[1], r[2])): print(" | ".join(str(x) for x in r))
print(len(rows), "words take any thing;", sum(1 for r in rows if r[0] == "do"), "are do words;",
      sum(1 for r in rows if r[0] == "do" and r[1] not in ("yes", "True")), "do words not plainly undoable")
