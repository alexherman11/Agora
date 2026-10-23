"""a11200 audit: are a11242's 18 brought paths already committed on worker/a8420, byte-for-byte as hashed in c11259?

    python research/delivery-audit-a11200/check_a11242_paths.py

Read-only git show. c11259 lists each path's working-file SHA256 prefix in a8420's worktree; a committed blob
matches if its bytes, or its bytes with LF converted to CRLF (the checkout of a CRLF working file under
.gitattributes eol=lf), or with one CR placed before a single newline (mixed endings), hash to that prefix.
"""
import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REV = "worker/a8420"
N, W = "research/text-desk-lab/notation/", "research/window-lab/selection-menu/"
WANT = {N + "desk-shell/lens.js": "E3F63F12", N + "deskd.py": "1707E2E0", N + "lens_ir.py": "D5A84381",
        N + "scene.py": "672B790C", N + "verbs.py": "D67111CB", N + "selection_snapshot.py": "8B34DA1B",
        N + "test_selection_snapshot.py": "72E48C11", W + "explicit_acceptance.py": "D4C38C4C",
        W + "world-menu-fixtures.json": "96A30A5E", W + "test_composer_quote.cjs": "6447DD71",
        W + "test_send_receipts.cjs": "B9F441F3", W + "inspect_paired_copy.py": "E0BC6BA3",
        W + "PAIRED-COPY.json": "9F2ED455", W + "PAIRED-WORLD-EXAMPLE.txt": "6CA929B2",
        W + "EXPLICIT-HANDOFF.md": "DD4EE928", W + "PAIRED-MENU-COPY.json": "43EF519A",
        W + "FINAL-COPY-HANDOFF.md": "2DFC0A0C", W + "results/20261021-130228/report.json": "811F92D6"}


def h(b):
    return hashlib.sha256(b).hexdigest().upper()


tip = subprocess.run(["git", "rev-parse", REV], cwd=ROOT, capture_output=True, text=True).stdout.strip()
print(f"{REV} = {tip}")
ok = 0
for path, want in WANT.items():
    r = subprocess.run(["git", "show", f"{REV}:{path}"], cwd=ROOT, capture_output=True)
    if r.returncode:
        print(f"ABSENT  {path}")
        continue
    b = r.stdout
    crlf = b.replace(b"\n", b"\r\n")
    how = ("as committed" if h(b).startswith(want) else "CRLF checkout" if h(crlf).startswith(want) else None)
    if how is None:
        for i in (i for i in range(len(b)) if b[i:i + 1] == b"\n"):
            if h(b[:i] + b"\r" + b[i:]).startswith(want):
                how = f"one CR at line {b[:i].count(b'\n') + 1}"
                break
    ok += bool(how)
    print(f"{'MATCH' if how else 'DIFF '}   {path} ({want}) {how or ''}")
print(f"{ok}/{len(WANT)} committed on {REV} as hashed")
