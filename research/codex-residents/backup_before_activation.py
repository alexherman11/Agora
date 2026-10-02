"""Preserve a world snapshot via its locked loader and private house state."""

import hashlib
import json
import pickle
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parent / "text-desk-lab" / "notation"
sys.path.insert(0, str(LAB))
import export_docs  # noqa: E402


def main():
    backup = (
        HERE.parents[1]
        / "local"
        / "codex-residents"
        / ("before-activation-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"))
    )
    backup.mkdir(parents=True, exist_ok=False)
    # Use the desk's loader and cross-process lock, never inspect a pickle directly.
    desk = export_docs.load("frontier")
    raw = pickle.dumps(desk)
    (backup / "frontier.pickle").write_bytes(raw)
    state = LAB / "house-state" / "frontier"
    copied = []
    for source in [state / "house.json", *state.glob("*/state.json")]:
        relative = source.relative_to(state)
        target = backup / "house-state" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.append(str(relative))
    shutil.copy2(LAB / "house.py", backup / "house.py")
    shutil.copy2(LAB / "workshop.py", backup / "workshop.py")
    receipt = {
        "path": str(backup),
        "snapshot_sha256": hashlib.sha256(raw).hexdigest(),
        "state_files": copied,
    }
    (backup / "receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
