"""revise.py (a8911, round 2 of the copy check): put the revised verb's text into the copy's verb note and make
three fresh cards, as JEFF, on a -try copy only.    python .../run/revise.py <verb note id in the copy>"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
verb = (HERE.parent / "notify-question-owner.verb").read_text(encoding="utf-8").rstrip("\n")
lines = [f"read {sys.argv[1]}", f"do rewrite {sys.argv[1]} text={json.dumps(verb, ensure_ascii=False)}", "look f5189 :1"]
for what, asker in (("JEFF-asked card", "jeff"), ("Alex-asked card", "alex"), ("permission card", "jeff")):
    lines.append(f'do create f5189 kind=task title="Copy check a8911 r2: {what}" asked_by={asker} commission=working')
(HERE / "revise.desk").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("wrote revise.desk")
