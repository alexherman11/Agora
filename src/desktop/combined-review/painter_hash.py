"""a7925: deskd's painter_version() for a desk-shell folder (same algorithm: sha1 over relative path and bytes of every
file, first 12 hex), plus whether it carries the a7045 partition painter. Reads only.

    python src/desktop/combined-review/painter_hash.py <desk-shell dir> [...]
"""
import hashlib
import sys
from pathlib import Path

for d in map(Path, sys.argv[1:]):
    files = sorted(p for p in d.rglob("*") if p.is_file())
    h = hashlib.sha1()
    for p in files:
        h.update(str(p.relative_to(d)).encode() + b"\0" + p.read_bytes() + b"\0")
    lens = (d / "lens.js").read_text(encoding="utf-8")
    print(d, h.hexdigest()[:12], f"{len(files)} files", "partition painter:",
          "data-partition" in lens or "Partition" in lens)
