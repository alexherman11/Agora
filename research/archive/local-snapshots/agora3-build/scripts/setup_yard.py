"""Provision a separate candidate VM and capture its clean execution baseline.

Run: uv run python scripts/setup_yard.py --world worlds/dev --port 22334
An existing valid yard configuration is inspected without resetting either VM.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from agora3.guest import Guest, GuestError
from agora3.yard import Yard


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world", type=Path, required=True)
    parser.add_argument("--yard", type=Path, help="Directory for the new candidate machine config")
    parser.add_argument("--port", type=int, default=22334)
    args = parser.parse_args()
    destination = args.world.resolve() / "yard.json"
    main = Guest(args.world.resolve() / "machine.json")
    if destination.exists():
        status = Yard(destination, main).status()
        if not status["available"]:
            raise GuestError(status["error"])
        print(json.dumps({"existing": True, "yard_config": str(destination), **status}, indent=2))
        return
    main_id = main._config(require_ssh=False)["vm_id"]
    folder = (
        args.yard.resolve()
        if args.yard
        else args.world.resolve().with_name(args.world.name + "-yard")
    )
    machine_config = folder / "machine.json"
    if machine_config.exists():
        parser.error(
            "Candidate machine config already exists without yard.json; "
            "refusing to adopt or reset it"
        )
    subprocess.run(
        [
            sys.executable,
            str(Path(__file__).with_name("setup_guest.py")),
            "--world",
            str(folder),
            "--port",
            str(args.port),
            "--start",
        ],
        check=True,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    candidate = Guest(machine_config)
    candidate_config = candidate._config()
    vm_id = candidate_config["vm_id"]
    if vm_id == main_id:
        parser.error("The candidate VM must be distinct from the live VM")
    candidate.start()
    Yard._ready(candidate)
    initialized = candidate.execute("cloud-init status --wait >/dev/null && sync", timeout=30)
    if initialized["exit_code"]:
        raise GuestError("Candidate cloud-init did not complete cleanly; no baseline was captured")
    candidate.stop()
    candidate._vbox(
        "snapshot",
        vm_id,
        "take",
        "Agora3-clean-yard",
        "--description",
        "Pristine Ubuntu; no live native token, mount or tunnel",
    )
    snapshots = candidate._vbox("snapshot", vm_id, "list", "--machinereadable")
    match = re.search(r'^CurrentSnapshotUUID="([^"]+)"$', snapshots, re.MULTILINE)
    if not match:
        raise GuestError("Could not identify the newly created yard snapshot")
    value = {"machine_config": str(candidate.config_path), "snapshot_id": match.group(1)}
    destination.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "yard_config": str(destination),
                "vm_id": vm_id,
                "snapshot_id": match.group(1),
                "state": "poweroff",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
