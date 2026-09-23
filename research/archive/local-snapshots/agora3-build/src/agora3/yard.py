"""Run candidate source in a separate VM reset to an operator-created baseline.
Never run a candidate in the live credentialed guest or fall back to host execution.
"""

import json
import time
from pathlib import Path
from uuid import UUID

from agora3.guest import Guest, GuestError, validate_sources
from agora3.locking import ProcessLock


class Yard:
    def __init__(self, config_path, main_guest):
        self.config_path = Path(config_path).resolve()
        self.main_guest = main_guest
        self.lock = ProcessLock(self.config_path.with_suffix(".lock"), timeout=300)

    def _configured(self):
        try:
            config = json.loads(self.config_path.read_text(encoding="utf-8"))
            snapshot = str(UUID(config["snapshot_id"]))
            path = Path(config["machine_config"])
            if not path.is_absolute():
                path = self.config_path.parent / path
            machine = Guest(path)
            candidate = machine._config()
            main = self.main_guest._config(require_ssh=False)
            if candidate["vm_id"] == main["vm_id"]:
                raise ValueError("Candidate yard must be a different VM from the live guest")
            info = machine._owned(candidate)
            machine._isolation(info)
            snapshots = machine._vbox("snapshot", candidate["vm_id"], "list", "--machinereadable")
            if f'="{snapshot}"' not in snapshots:
                raise ValueError("Configured clean snapshot does not exist on the yard VM")
            return machine, snapshot
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise GuestError(f"Candidate yard is not configured: {exc}") from exc

    def status(self):
        try:
            machine, snapshot = self._configured()
            result = machine.status()
            result.update(
                {"snapshot_id": snapshot, "isolation": "separate VM reset per invocation"}
            )
            return result
        except GuestError as exc:
            return {"available": False, "state": "unavailable", "error": str(exc)}

    @staticmethod
    def _ready(machine, timeout=60):
        deadline = time.monotonic() + timeout
        error = "SSH has not become ready"
        while time.monotonic() < deadline:
            result = machine.execute(
                "test ! -e /run/agora/config.json && printf 'yard-ready'", timeout=5
            )
            if result["exit_code"] == 0 and result["stdout"] == "yard-ready":
                return
            error = (
                result["stderr"] or "Clean yard unexpectedly contains a live bridge configuration"
            )
            if result["exit_code"] == 1:
                raise GuestError(error)
            time.sleep(1)
        raise GuestError(f"Candidate yard did not become ready within {timeout}s: {error}")

    def run(self, source_files, entry, arguments, context, timeout=30):
        validate_sources(source_files, entry)
        with self.lock:
            machine, snapshot = self._configured()
            # Also serialize aliases from different native worlds using this VM.
            with ProcessLock(machine.config_path.with_suffix(".yard.lock"), timeout=300):
                config = machine._config()
                machine.stop()
                machine._vbox("snapshot", config["vm_id"], "restore", snapshot)
                try:
                    machine.start()
                    self._ready(machine)
                    return machine.run(source_files, entry, arguments, context, timeout)
                finally:
                    # Candidate root cannot keep processes running beyond this boundary.
                    machine.stop()
