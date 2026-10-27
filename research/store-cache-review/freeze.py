"""Generate review-only patch and hashes; no Git index/object/ref writes."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE = "research/text-desk-lab/notation/store.py"
TEST = "research/text-desk-lab/notation/test_journal_cache.py"


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


base = git("rev-parse", "HEAD").decode().strip()
patch = git("diff", "--binary", "--", SOURCE).replace(b"\r\n", b"\n")
test = (ROOT / TEST).read_bytes().replace(b"\r\n", b"\n")
lines = test.splitlines(keepends=True)
patch += (f"diff --git a/{TEST} b/{TEST}\nnew file mode 100644\n"
          f"--- /dev/null\n+++ b/{TEST}\n@@ -0,0 +1,{len(lines)} @@\n").encode()
patch += b"".join(b"+" + line for line in lines)
(HERE / "candidate.patch").write_bytes(patch)
inventory = {
    "base_commit": base,
    "base_store_blob": git("rev-parse", f"{base}:{SOURCE}").decode().strip(),
    "base_store_sha256": sha(git("show", f"{base}:{SOURCE}")),
    "patch_sha256": sha(patch),
    "files": {p: {"sha256": sha((ROOT / p).read_bytes()), "bytes": len((ROOT / p).read_bytes())}
              for p in (SOURCE, TEST)},
    "status": "staged only; independent review required; no ready or landing",
}
(HERE / "inventory.json").write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
print(json.dumps(inventory, indent=2))
