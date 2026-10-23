"""a11200 audit: does the house's checkpoint c8c03e1 hold exactly what prepare receipt a8420-e25392 recorded?

    python research/delivery-audit-a11200/check_a8420_receipt.py

Read-only: git show of blobs and the receipt JSON. For each recorded file, tries the committed blob as stored (LF),
converted to CRLF, and with one trailing newline added or removed, and says which (if any) matches the receipt's
sha256 and byte count. Changes nothing.
"""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECEIPT = Path("C:/Projects/Agora4/research/text-desk-lab/notation/house-state/frontier/prepares/a8420-e25392.json")
CHECKPOINT = "c8c03e1"


def blob(rev, path):
    r = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT, capture_output=True)
    return r.stdout if r.returncode == 0 else None


def variants(b):
    crlf = b.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    yield "as committed (LF)", b
    yield "CRLF", crlf
    yield "LF + trailing \\n", b + b"\n"
    yield "LF minus trailing \\n", b[:-1] if b.endswith(b"\n") else b
    yield "CRLF + trailing \\r\\n", crlf + b"\r\n"
    yield "CRLF minus trailing \\r\\n", crlf[:-2] if crlf.endswith(b"\r\n") else crlf
    yield "LF with a final \\r", b[:-1] + b"\r\n" if b.endswith(b"\n") else b


rec = json.loads(RECEIPT.read_text(encoding="utf-8"))
print(f"receipt {rec['request']} phase={rec['phase']} before={rec['before'][:8]} main={rec['main'][:8]}")
for path, want in rec["receiver_checkpoint"]["files"].items():
    b = blob(CHECKPOINT, path)
    if b is None:
        print(f"MISSING in {CHECKPOINT}: {path}")
        continue
    hit = [name for name, v in variants(b) if hashlib.sha256(v).hexdigest() == want["sha256"] and len(v) == want["bytes"]]
    crlf_lines = b.count(b"\r\n")
    print(f"{'MATCH' if hit else 'DIFF '} {path.rsplit('/', 1)[-1]}: receipt {want['bytes']} B, blob {len(b)} B, "
          f"blob CRLF lines {crlf_lines}, LF lines {b.count(b'\n')}" + (f" -> {hit[0]}" if hit else ""))
    if not hit and want["bytes"] == len(b) + 1:     # one byte more: a single CRLF line in a mixed-ending working file?
        at = [i for i in range(len(b)) if b[i:i + 1] == b"\n"]
        one = [i for i in at if hashlib.sha256(b[:i] + b"\r" + b[i:]).hexdigest() == want["sha256"]]
        if one:
            ln = b[:one[0]].count(b"\n") + 1
            print(f"      -> matches with a single CR before the newline of line {ln}: "
                  f"{b[b.rfind(b'\n', 0, one[0]) + 1:one[0]][:100]!r}")
        else:
            print("      -> no single-CR placement matches; the working file's content differs from the commit")
