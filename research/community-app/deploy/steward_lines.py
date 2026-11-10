"""Say the given lines as the steward, through steward_session.sh, printing each answer. A refused line is printed and
the next one still runs. Claude, 5 Nov 2026.

    sh steward_session.sh steward_lines.py --line "see:rows place" --line "set sb1 name=..."
A line starting `see:` is a reading.
"""
import argparse
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parents[2] / "kernel-lab"
sys.path.insert(0, str(LAB))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--door", required=True)
    ap.add_argument("--token-file", required=True)
    ap.add_argument("--line", action="append", default=[])
    a = ap.parse_args()
    from painter.install import taskboard
    door = taskboard.Door(a.door, Path(a.token_file).read_text(encoding="utf-8").strip())
    for line in a.line:
        if line.startswith("see:"):
            out = door.request("/see", dict(line=line[4:]))
        else:
            out = door.request("/do", dict(line=line))
        print(">", line, "\n ", str(out.get("text", ""))[:400].replace("\n", "\n  "))


if __name__ == "__main__":
    main()
