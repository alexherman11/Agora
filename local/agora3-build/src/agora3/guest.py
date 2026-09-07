"""Supervise one operator-configured Linux guest and transport package execution.
Never run authored source on the host, accept SSH host keys, or touch another VM.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import threading
from pathlib import Path, PurePosixPath
from uuid import UUID

MAX_OUTPUT = 4 * 1024 * 1024
OWNER_KEY = "Agora3/managed"
VBOX = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Oracle/VirtualBox/VBoxManage.exe"

# This program is sent as an SSH command. It is never evaluated by the host.
RUNNER = r"""
import contextlib, importlib.util, json, os, pathlib, sys, tempfile
request = json.load(sys.stdin)
with tempfile.TemporaryDirectory(prefix="agora-action-") as folder:
    root = pathlib.Path(folder)
    for name, source in request["source_files"].items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        if path.suffix == ".py":
            compile(source, name, "exec")
    filename, function = request["entry"].split(":", 1)
    sys.path.insert(0, str(root))
    os.chdir(root)
    with contextlib.redirect_stdout(sys.stderr):
        spec = importlib.util.spec_from_file_location("agora_action", root / filename)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = getattr(module, function)(request["arguments"], request["context"])
    print(json.dumps(result, allow_nan=False))
"""


class GuestError(RuntimeError):
    """A missing, unavailable or incorrectly configured guest; no host fallback."""


def validate_sources(source_files: dict[str, str], entry: str) -> None:
    if not isinstance(source_files, dict) or not source_files or len(source_files) > 128:
        raise GuestError("Provide 1–128 package-relative source files.")
    total = 0
    for name, source in source_files.items():
        if not isinstance(name, str) or not isinstance(source, str):
            raise GuestError("Source names and contents must be strings.")
        parts = PurePosixPath(name).parts
        if (
            not parts
            or name.startswith("/")
            or "\\" in name
            or ":" in name
            or "\x00" in name
            or any(part in (".", "..") for part in name.split("/"))
            or "//" in name
        ):
            raise GuestError("Source paths must be normalized relative paths without traversal.")
        total += len(source.encode("utf-8"))
    if total > 2 * 1024 * 1024:
        raise GuestError("Package source exceeds the 2 MiB execution limit.")
    if not isinstance(entry, str) or entry.count(":") != 1:
        raise GuestError("Entry must have the form module.py:function.")
    filename, function = entry.split(":")
    if filename not in source_files or not filename.endswith(".py") or not function.isidentifier():
        raise GuestError("Entry must name a supplied Python source and a function identifier.")


def _process(args: list[str], timeout: int, stdin: str | None = None) -> dict:
    """Bound host memory while collecting guest output; no local shell parsing."""
    try:
        process = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    except OSError as exc:
        raise GuestError(f"Guest transport could not start: {exc}") from exc
    buffers = [bytearray(), bytearray()]
    truncated = [False, False]

    def drain(stream, index):
        with stream:
            while chunk := stream.read(65536):
                remaining = MAX_OUTPUT - len(buffers[index])
                buffers[index].extend(chunk[:remaining])
                truncated[index] |= len(chunk) > remaining

    def send():
        try:
            with process.stdin:
                if stdin is not None:
                    process.stdin.write(stdin.encode("utf-8"))
        except (BrokenPipeError, OSError):
            pass

    threads = [
        threading.Thread(target=drain, args=(process.stdout, 0), daemon=True),
        threading.Thread(target=drain, args=(process.stderr, 1), daemon=True),
        threading.Thread(target=send, daemon=True),
    ]
    for thread in threads:
        thread.start()
    try:
        code = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        code = 124
    for thread in threads:
        thread.join(timeout=2)
    return {
        "stdout": buffers[0].decode("utf-8", errors="replace"),
        "stderr": buffers[1].decode("utf-8", errors="replace"),
        "exit_code": code,
        "truncated": any(truncated),
    }


class Guest:
    def __init__(self, config_path: str | Path):
        self.config_path = Path(config_path).resolve()

    def _config(self, *, require_ssh: bool = True) -> dict:
        try:
            config = json.loads(self.config_path.read_text(encoding="utf-8"))
            if config.get("backend") != "virtualbox":
                raise ValueError("Only the VirtualBox backend is implemented")
            config["vm_id"] = str(UUID(config["vm_id"]))
            if not require_ssh:
                return config
            if config.get("ssh_host") != "127.0.0.1" or config.get("ssh_user") != "jeff":
                raise ValueError("SSH must target the dedicated loopback guest as jeff")
            if type(config.get("ssh_port")) is not int or not 1024 <= config["ssh_port"] <= 65535:
                raise ValueError("SSH port must be an integer from 1024 through 65535")
            for field in ("identity_file", "known_hosts"):
                path = Path(config[field])
                if not path.is_absolute():
                    path = self.config_path.parent / path
                if not path.is_file():
                    raise ValueError(f"Missing {field}; run the guest setup recipe")
                config[field] = str(path.resolve())
            pin = f"[127.0.0.1]:{config['ssh_port']} ssh-ed25519 "
            hosts = Path(config["known_hosts"]).read_text(encoding="utf-8")
            if not any(line.startswith(pin) for line in hosts.splitlines()):
                raise ValueError("known_hosts must contain the provisioned guest's Ed25519 key")
            return config
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
            raise GuestError(f"Guest configuration unavailable or invalid: {exc}") from exc

    @staticmethod
    def _vbox(*arguments: str) -> str:
        executable = str(VBOX) if os.name == "nt" else "VBoxManage"
        result = _process([executable, *arguments], 20)
        if result["exit_code"]:
            raise GuestError(result["stderr"] or "VirtualBox did not respond successfully")
        return result["stdout"].replace("\r\n", "\n")

    def _owned(self, config: dict) -> str:
        owner = self._vbox("getextradata", config["vm_id"], OWNER_KEY).strip()
        if owner != "Value: true":
            raise GuestError("Refusing a VM without the Agora3 ownership marker.")
        info = self._vbox("showvminfo", config["vm_id"], "--machinereadable")
        name = re.search(r'^name="([^"]+)"$', info, re.MULTILINE)
        if not name or not name.group(1).startswith("Agora3-"):
            raise GuestError("Refusing a VM whose name is outside the Agora3 namespace.")
        return info

    @staticmethod
    def _state(info: str) -> str:
        match = re.search(r'^VMState="([^"]+)"$', info, re.MULTILINE)
        return match.group(1) if match else "unknown"

    @staticmethod
    def _isolation(info: str) -> None:
        for field in ("clipboard", "draganddrop"):
            if f'{field}="disabled"' not in info:
                raise GuestError(f"Guest {field} must be disabled.")
        if "SharedFolderName" in info:
            raise GuestError("Guest shared folders must be removed before execution.")

    def status(self) -> dict:
        try:
            config = self._config()
            info = self._owned(config)
            self._isolation(info)
            return {
                "available": True,
                "backend": "virtualbox",
                "vm_id": config["vm_id"],
                "state": self._state(info),
                "execution": "Linux guest root; SSH key pinned; no shared host folders",
            }
        except GuestError as exc:
            return {"available": False, "state": "unavailable", "error": str(exc)}

    def start(self) -> dict:
        config = self._config()
        info = self._owned(config)
        self._isolation(info)
        if self._state(info) != "running":
            self._vbox("startvm", config["vm_id"], "--type", "headless")
        return self.status()

    def stop(self) -> dict:
        """Protected host recovery; not an authored guest capability."""
        config = self._config(require_ssh=False)
        info = self._owned(config)
        if self._state(info) not in ("poweroff", "aborted"):
            self._vbox("controlvm", config["vm_id"], "poweroff")
        return self.status()

    def _ssh(self, command: str, timeout: int, stdin: str | None = None) -> dict:
        if type(timeout) is not int or not 1 <= timeout <= 300:
            raise GuestError("Guest timeout must be an integer from 1 through 300 seconds.")
        config = self._config()
        info = self._owned(config)
        self._isolation(info)
        if self._state(info) != "running":
            raise GuestError("The Agora3 guest is stopped. Start it through host recovery.")
        args = [
            "ssh",
            "-F",
            "none",
            "-T",
            "-p",
            str(config["ssh_port"]),
            "-i",
            config["identity_file"],
            "-o",
            "BatchMode=yes",
            "-o",
            "IdentitiesOnly=yes",
            "-o",
            "StrictHostKeyChecking=yes",
            "-o",
            f"UserKnownHostsFile={config['known_hosts']}",
            "-o",
            "GlobalKnownHostsFile=none",
            "-o",
            "ConnectTimeout=5",
            "-o",
            "ForwardAgent=no",
            "-o",
            "ClearAllForwardings=yes",
            "jeff@127.0.0.1",
            f"sudo -n timeout --signal=TERM --kill-after=2s {timeout}s "
            f"bash -lc {shlex.quote(command)}",
        ]
        return _process(args, timeout + 8, stdin)

    def execute(self, command: str, timeout: int = 30) -> dict:
        if not isinstance(command, str) or not command.strip() or len(command) > 65536:
            raise GuestError("Supply a nonempty guest command of at most 65536 characters.")
        return self._ssh(command, timeout)

    def run(
        self,
        source_files: dict[str, str],
        entry: str,
        arguments: dict,
        context: dict,
        timeout: int = 30,
    ):
        validate_sources(source_files, entry)
        if not isinstance(arguments, dict) or not isinstance(context, dict):
            raise GuestError("Action arguments and read-only host context must be objects.")
        payload = json.dumps(
            {
                "source_files": source_files,
                "entry": entry,
                "arguments": arguments,
                "context": context,
            },
            allow_nan=False,
        )
        result = self._ssh("python3 -c " + shlex.quote(RUNNER), timeout, payload)
        if result["exit_code"] or result["truncated"]:
            raise GuestError(
                f"Guest action failed (exit {result['exit_code']}): {result['stderr'][-12000:]}"
            )
        try:
            return json.loads(result["stdout"])
        except ValueError as exc:
            raise GuestError("Guest action did not return valid JSON.") from exc
