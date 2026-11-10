"""Say lines from a file as the steward, through steward_session.sh. Claude, 5 Nov 2026 (one-off seeding)."""
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "agora"))
ap = argparse.ArgumentParser(); ap.add_argument("--door", required=True); ap.add_argument("--token-file", required=True)
ap.add_argument("--file", default="/tmp/seed-lines.txt"); a = ap.parse_args()
from painter.install import taskboard
door = taskboard.Door(a.door, Path(a.token_file).read_text(encoding="utf-8").strip())
for line in Path(a.file).read_text(encoding="utf-8").splitlines():
    if not line.strip(): continue
    out = door.request("/see", dict(line=line[4:])) if line.startswith("see:") else door.request("/do", dict(line=line))
    print(">", line[:90]); print("  ", str(out.get("text", ""))[:700].replace("\n", "\n   "))
