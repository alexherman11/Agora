"""Freeze named source directories, nonrecursively; never inspect scratch/worlds.

No host imports, admission reads, inference, fixture execution or discovery of
another worktree. Existing product manifest is verified, never regenerated.
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
    paths = set(frozen["file_sha256"])
    for name, expected in frozen["file_sha256"].items():
        if sha(ROOT / name) != expected:
            raise RuntimeError("product freeze drift: " + name)
    paths.add(previous.relative_to(ROOT).as_posix())
    # Deliberately nonrecursive and limited to source suffixes. No scratch,
    # worlds, state, session files, logs, fixture profiles or sealed evaluation.
    directories = {
        "research/kernel-lab/kernel": {".py"},
        "research/kernel-lab/painter": {".py", ".js"},
        "research/kernel-lab/theme": {".py"},
        "research/kernel-lab/hosts/web": {".py", ".js", ".css", ".html"},
        "research/kernel-lab/apps/taskboard": {".py"},
        "research/window-lab/kernel-desktop": {".py"},
        "research/window-lab/kernel-desktop/pages": {".js", ".css", ".html"},
        "research/community-app/site/agora_entry": {".py"},
        "research/community-app/site/content": {".json"},
        "research/text-desk-lab/notation": {".py"},
        "research/text-desk-lab/notation/desk-shell": {".js", ".css", ".html"},
    }
    for name, suffixes in directories.items():
        for path in (ROOT / name).iterdir():
            if path.is_file() and path.suffix in suffixes:
                paths.add(path.relative_to(ROOT).as_posix())
    for name in ("sandbox_window.py", "sandbox_job.py", "sandbox_birth.py",
                 "sandbox_owned.py", "sandbox_receipts.py", "agora_tmp.py", "screen_tools.py"):
        paths.add("research/window-lab/" + name)
    for name in ("runner.py", "fixture.py", "freeze_source.py", "CONTRACT.md"):
        paths.add((HERE / name).relative_to(ROOT).as_posix())
    manifest = {
        "schema": "search-source-only-host-acceptance-v1",
        "status": "UNEXECUTED; independent source review and separate execution authority required",
        "discovery": "explicit nonrecursive source directories; no scratch traversal",
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
    target = HERE / "source-manifest.json"
    target.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"source_files": len(paths), "manifest_sha256": sha(target),
                      "product_freeze_preserved": True, "host_checks_executed": False}))


if __name__ == "__main__":
    main()
