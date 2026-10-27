"""Read-only preservation check; no native imports or runtime admission."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    manifest = json.loads(
        (HERE / "OFFLINE-BINDING-a9231.manifest.json").read_text()
    )
    failures = []
    bases = 0
    for name, entry in manifest["files"].items():
        if digest((ROOT / name).read_bytes()) != entry["output_sha256"]:
            failures.append(("output", name))
        if entry["base_blob_sha256"]:
            bases += 1
            data = subprocess.check_output(
                ["git", "show", manifest["base_head"] + ":" + name], cwd=ROOT
            )
            if digest(data) != entry["base_blob_sha256"]:
                failures.append(("base", name))
    patch = digest((HERE / "OFFLINE-BINDING-a9231.patch").read_bytes())
    if patch != manifest["patch_sha256"]:
        failures.append(("patch", patch))
    print("output entries:", len(manifest["files"]), "base entries:", bases)
    print("mismatches:", failures)
    print("patch:", patch)
    print("guard:", digest(
        (ROOT / "research/text-desk-lab/notation/guard_context.py").read_bytes()
    ))
    print("parents:", subprocess.check_output(
        ["git", "show", "-s", "--format=%P", "HEAD"], cwd=ROOT
    ).decode().strip())
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
