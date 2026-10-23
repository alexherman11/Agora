"""Record this card's source/evidence bytes; never include world/session files."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


paths = set(git("diff", "main", "--name-only").splitlines())
paths.add(Path(__file__).relative_to(ROOT).as_posix())
out = Path(__file__).with_name("LANDING-HASHES-20261022.json")
paths.discard(out.relative_to(ROOT).as_posix())
assert all("sessions/" not in p and "cache" not in p.lower()
           and not p.endswith(".env") for p in paths)
data = {
    "head": git("rev-parse", "HEAD"),
    "main": git("rev-parse", "main"),
    "scope": "source-only; four world hunks unapplied; no browser proof",
    "files": {
        p: {"bytes": len((ROOT / p).read_bytes()),
            "sha256": hashlib.sha256((ROOT / p).read_bytes()).hexdigest()}
        for p in sorted(paths)
    },
}
out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print(f"{len(paths)} source/evidence files; manifest SHA256 "
      f"{hashlib.sha256(out.read_bytes()).hexdigest()}")
