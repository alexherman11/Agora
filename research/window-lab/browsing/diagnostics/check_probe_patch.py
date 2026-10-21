"""Verify/render staged source edits OFFLINE. Never imports or runs a probe.

Usage: python check_probe_patch.py --source <directory containing owner's two .py files>
No files are changed. An owner integrates reviewed hunks separately.
"""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def check(source):
    contract = json.loads((HERE / "probe-diagnostics.json").read_text(encoding="utf-8"))
    results = []
    for entry in contract["documents"]:
        name = entry["path"]
        if name not in ("native_engine_probe.py", "probe_hidden.py"):
            raise ValueError("unreviewed source target")
        before = (source / name).read_text(encoding="utf-8")
        if hashlib.sha256(before.encode()).hexdigest() != entry["sha256"]:
            raise ValueError(name + ": source changed; owner must re-review exact hunks")
        after = before
        for edit in entry["edits"]:
            if after.count(edit["old"]) != 1:
                raise ValueError(name + ": ambiguous/missing old text")
            after = after.replace(edit["old"], edit["new"], 1)
        compile(after, name, "exec")  # does NOT exec/import the compiled source
        if name == "native_engine_probe.py":
            assert "deadline.Interval = 15000" in after
            assert "diagnostics.deadline()" in after
            assert after.index("diagnostics.deadline()") < after.index('result["stage"] = "deadline_fired"')
            for hook in ("BrowserProcessExited +=", "ProcessFailed +=", "diagnostics.navigation(",
                         "diagnostics.child_ready(", "e.source===f.contentWindow"):
                assert hook in after
        else:
            assert 'not cleanup_receipt.get("ok")' in after
            assert "remaining is None" in after
        results.append({"file": name, "base_sha256": entry["sha256"],
                        "staged_sha256": hashlib.sha256(after.encode()).hexdigest()})
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps({"offline_only": True, "compiled_not_executed": check(args.source)}, indent=2))
