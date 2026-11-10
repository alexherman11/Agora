"""overlay.py (a7466): put the preserved integrated partition/dock source (worktree a7045, uncommitted on base
c5c988c) into THIS worktree's files, over current main (landed harness c3ad04e, tabs 3cc2796), for a disposable
guarded review. Reads a7045 only; never writes there, never touches git's index or any world.

    python src/desktop/combined-review/overlay.py plan      what a7045 changed and how each file composes
    python src/desktop/combined-review/overlay.py apply     write the composed files here (manifest.json)
    python src/desktop/combined-review/overlay.py restore   put every overlaid file back as HEAD has it

Per file: base = c5c988c, theirs = a7045's file, ours = HEAD. theirs == base: skipped. ours == base: theirs taken.
Both changed: git merge-file on scratch copies; a conflict is reported and the file is NOT overlaid (apply refuses
the whole overlay, so nothing half-composed is reviewed).
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
THEIRS = ROOT.parent / "a7045"
BASE = "c5c988c"
SKIP_DIRS = {".git", "sessions", ".tmp-agora", "demos", "__pycache__", "node_modules", ".venv", "house-state",
             "state", ".worktrees"}
MANIFEST = HERE / "manifest.json"
SCRATCH = ROOT / "src" / "desktop" / ".tmp-agora" / "overlay"


def git(*a, binary=False):
    r = subprocess.run(["git", *a], cwd=ROOT, capture_output=True)
    if r.returncode:
        raise SystemExit(f"git {' '.join(a)}: {r.stderr.decode(errors='replace')}")
    return r.stdout if binary else r.stdout.decode("utf-8", errors="replace")


def tree(rev):
    out = {}
    for line in git("ls-tree", "-r", rev).splitlines():
        meta, path = line.split("\t", 1)
        out[path] = meta.split()[2]
    return out


def norm(b):
    return b.replace(b"\r\n", b"\n")


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def theirs_files():
    for p in THEIRS.rglob("*"):
        rel = p.relative_to(THEIRS)
        if any(part in SKIP_DIRS for part in rel.parts) or not p.is_file() or p.suffix in (".pyc", ".png", ".mp4", ".pickle"):
            continue
        yield rel.as_posix(), p


def blob(rev, path):
    return git("show", f"{rev}:{path}", binary=True)


def plan():
    base, ours = tree(BASE), tree("HEAD")
    rows = []
    for rel, p in sorted(theirs_files()):
        t = norm(p.read_bytes())
        b = norm(blob(BASE, rel)) if rel in base else None
        if b is not None and t == b:
            continue
        o = norm(blob("HEAD", rel)) if rel in ours else None
        if o == b:
            how, out = ("new" if b is None else "theirs"), t
        elif o == t:
            how, out = "same-on-main", t
        elif b is None:
            how, out = "CONFLICT (new in both, differ)", None
        else:
            SCRATCH.mkdir(parents=True, exist_ok=True)
            fo, fb, ft = SCRATCH / "ours", SCRATCH / "base", SCRATCH / "theirs"
            fo.write_bytes(o), fb.write_bytes(b), ft.write_bytes(t)
            r = subprocess.run(["git", "merge-file", "-p", str(fo), str(fb), str(ft)], capture_output=True)
            how, out = ("merged" if r.returncode == 0 else f"CONFLICT ({r.returncode} blocks)"), (r.stdout if r.returncode == 0 else None)
            if r.returncode:                       # kept for reading, and for a recorded resolution (resolved/)
                c = SCRATCH / "conflicts" / rel
                c.parent.mkdir(parents=True, exist_ok=True)
                c.write_bytes(r.stdout)
                # the recorded resolution is the conflict block's replacement only (resolved/<path>.block), so
                # no copy of unlanded source is kept here
                res = HERE / "resolved" / (rel + ".block")
                blocks = re.findall(rb"<<<<<<< [^\n]*\n.*?=======\n.*?>>>>>>> [^\n]*\n", r.stdout, re.S)
                if res.exists() and len(blocks) == 1:
                    out = norm(r.stdout.replace(blocks[0], res.read_bytes()))
                    how = f"resolved by hand (1 block; resolved/{rel}.block)"
        rows.append({"path": rel, "how": how, "theirs_sha256": sha(t), "base_sha256": sha(b) if b is not None else None,
                     "main_sha256": sha(o) if o is not None else None, "composed_sha256": sha(out) if out is not None else None,
                     "_out": out})
    return rows


def main(argv):
    verb = argv[0] if argv else "plan"
    if verb == "restore":
        m = json.loads(MANIFEST.read_text(encoding="utf-8"))
        ours = tree("HEAD")
        for r in m["files"]:
            f = ROOT / r["path"]
            if r["path"] in ours:
                f.write_bytes(blob("HEAD", r["path"]).replace(b"\n", b"\r\n") if b"\r\n" in f.read_bytes() else blob("HEAD", r["path"]))
            else:
                f.unlink(missing_ok=True)
        print(f"restored {len(m['files'])} files as HEAD has them (new ones removed)")
        return
    rows = plan()
    for r in rows:
        print(f"{r['how']:<32} {r['path']}")
    bad = [r for r in rows if r["how"].startswith("CONFLICT")]
    print(f"{len(rows)} files differ from base {BASE}; {len(bad)} conflict")
    if verb == "apply":
        if bad:
            raise SystemExit("refused: a conflict would leave a half-composed source; nothing written")
        for r in rows:
            f = ROOT / r["path"]
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(r["_out"])
        head = git("rev-parse", "--short", "HEAD").strip()
        MANIFEST.write_text(json.dumps({"base": BASE, "main": head, "theirs": str(THEIRS),
                                        "files": [{k: v for k, v in r.items() if k != "_out"} for r in rows]}, indent=1),
                            encoding="utf-8")
        print(f"applied {len(rows)} files over HEAD {head}; manifest {MANIFEST}")


if __name__ == "__main__":
    main(sys.argv[1:])
