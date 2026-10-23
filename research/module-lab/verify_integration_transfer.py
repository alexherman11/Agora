"""Read-only verification of the exact authored integration slice."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    receipt = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    manifest = json.loads(
        (ROOT / "research/module-lab/evidence/integration-source-manifest.json")
        .read_text(encoding="utf-8")
    )
    expected = {p: h for group in manifest["groups"].values() for p, h in group.items()}
    assert receipt["phase"] == "applied"
    assert len(expected) == 21
    assert set(expected) == set(receipt["files"])
    for path, identity in expected.items():
        data = (ROOT / path).read_bytes()
        actual = dict(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
        assert actual == identity, (path, actual, identity)
        for section in ("files", "committed_files", "received_files", "received_worktree_files"):
            assert receipt[section][path] == identity, (section, path)
        for revision in (receipt["source_commit"], "HEAD"):
            blob = subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=ROOT)
            assert dict(sha256=hashlib.sha256(blob).hexdigest(), bytes=len(blob)) == identity
    print("21 files verified: author, raw receipt, committed source, received blobs and worktree")
    print("source:", receipt["source_commit"])
    print("receiver:", receipt["recipient_after"])
    sys.path.insert(0, str(ROOT / "research/text-desk-lab/notation"))
    from module_examples import registry

    # Read from the installed "Composition example known" via Desk, 22 October.
    # These are reviewed source pins, not account data or permission grants.
    installed_pins = {
        "coverage.view@1": "7f12fb573f720f522cafdab28a19dd2f8fe97aa7dc9b3bf8e093b8a395b680f8",
        "intervals.union@1": "f11cfef7c20adf21bac108d4596250c9d1a76ca2ff0328961311373645a2926b",
        "graphics.draw@1": "fdc59394ee482b3bb06ae108e08a406bf1b4961e7467e22a62d3cb621d840f20",
        "rows.frame@1": "cf82ae998a4a2b765956bff64484f51e05f70c6917addfeef8e8f395df5ce134",
    }
    actual_pins = {d["module"]: d["pin"] for d in registry().describe()}
    assert actual_pins == installed_pins, (actual_pins, installed_pins)
    print("4 registry pins match the installed example; no re-pinning")


if __name__ == "__main__":
    main()
