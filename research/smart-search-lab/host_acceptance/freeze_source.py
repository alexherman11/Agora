"""Re-freeze only four harness sources inside the existing explicit manifest.

No host imports, admission reads, inference, fixture execution or discovery of
another worktree. Every non-harness entry must remain byte-identical. No directory
iteration; product and dependency byte reconciliation is not independent review.
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    previous = ROOT / "research/smart-search-lab/projection-review-manifest.json"
    frozen = json.loads(previous.read_text(encoding="utf-8"))
    target = HERE / "source-manifest.json"
    old = json.loads(target.read_text(encoding="utf-8"))
    mutable = {(HERE / name).relative_to(ROOT).as_posix()
               for name in ("runner.py", "fixture.py", "freeze_source.py", "CONTRACT.md")}
    paths = set(old["sha256"])
    if not mutable.issubset(paths):
        raise RuntimeError("existing harness manifest required")
    for name, expected in old["sha256"].items():
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT):
            raise RuntimeError("manifest path escapes worktree")
        if name not in mutable and sha(path) != expected:
            raise RuntimeError("dependency freeze drift: " + name)
    for name, expected in frozen["file_sha256"].items():
        if sha(ROOT / name) != expected:
            raise RuntimeError("product freeze drift: " + name)
    manifest = {
        "schema": "search-source-only-host-acceptance-v2",
        "status": "UNEXECUTED; independent source review and separate execution authority required",
        "supersedes_manifest_sha256": "c999090362d6f6cfd6912407cd0647d8a362a3df4ac52d6d81ec10e51dfa17c3",
        "correction_for": "dk1783 static rejection; no host failures observed",
        "discovery": "reuse existing explicit manifest; no directory traversal or new dependency adoption",
        "product_manifest_sha256": sha(previous),
        "product_component_sha256": frozen["component_review_sha256"],
        "generated_widget_sha256": frozen["generated_widget_code_sha256"],
        "sha256": {name: sha(ROOT / name) for name in sorted(paths)},
        "not_bound": ["installed Python/stdlib/site-packages and Edge binary/runtime closure",
                      "authoritative House admission producer deployment and policy",
                      "external delegated engine descendants (not certified by enrolled-job closure)"],
        "authority": "Source manifest/CLI receipt are not a grant or an admission attestation",
        "host_execution_count": 0,
    }
    target.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"source_files": len(paths), "manifest_sha256": sha(target),
                      "product_freeze_preserved": True, "host_checks_executed": False}))


if __name__ == "__main__":
    main()
