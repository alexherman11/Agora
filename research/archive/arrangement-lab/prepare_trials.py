"""Freeze source and clone two owned, isolated VMs for authorized live comparison."""

from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess

ROOT = Path("C:/Projects/Agora/local/arrangement-trials-20260916")
SOURCE = Path("C:/Projects/Agora4")
VBOX = Path("C:/Program Files/Oracle/VirtualBox/VBoxManage.exe")
YARD = Path("C:/Projects/Agora/worlds/parallel-desk/machines/yard/machine.json")
SNAPSHOT = "385555c5-68b4-493f-b890-e1f025f8d954"


def vbox(*args):
    result = subprocess.run(
        [str(VBOX), *args],
        capture_output=True,
        text=True,
        timeout=180,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    frozen = ROOT / "baseline"
    if not frozen.exists():
        frozen.mkdir()
        for name in ("src", "scripts", "examples", "tests", "docs"):
            shutil.copytree(
                SOURCE / name, frozen / name, ignore=shutil.ignore_patterns("__pycache__")
            )
        for name in ("AGENTS.md", "pyproject.toml", "uv.lock"):
            shutil.copy2(SOURCE / name, frozen / name)
        hashes = {
            str(p.relative_to(frozen)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in frozen.rglob("*")
            if p.is_file()
        }
        (ROOT / "baseline-hashes.json").write_text(json.dumps(hashes, indent=2))
    base = json.loads(YARD.read_text())
    owner = vbox("getextradata", base["vm_id"], "Agora3/managed").strip()
    if owner != "Value: true":
        raise RuntimeError("Source is not an Agora-owned candidate VM")
    info = vbox("showvminfo", base["vm_id"], "--machinereadable")
    if 'VMState="poweroff"' not in info:
        raise RuntimeError("Source yard is active; do not disturb it")
    if SNAPSHOT not in vbox("snapshot", base["vm_id"], "list", "--machinereadable"):
        raise RuntimeError("Expected clean snapshot missing")
    report = {}
    for role, port in [("execution", 22851), ("yard", 22852)]:
        folder = ROOT / "machines" / role
        folder.mkdir(parents=True, exist_ok=True)
        destination = folder / "machine.json"
        if destination.exists():
            hosts = (
                Path(base["known_hosts"])
                .read_text()
                .replace(f"]:{base['ssh_port']} ", f"]:{port} ")
            )
            (folder / "known_hosts").write_text(hosts)
            report[role] = json.loads(destination.read_text())["vm_id"]
            continue
        name = "Agora3-Arrangement-" + role + "-20260916"
        if f'"{name}"' in vbox("list", "vms"):
            raise RuntimeError(
                "Clone exists without a completed local configuration; inspect first"
            )
        vbox(
            "clonevm",
            base["vm_id"],
            "--snapshot",
            SNAPSHOT,
            "--mode",
            "machine",
            "--options",
            "link",
            "--name",
            name,
            "--basefolder",
            str(ROOT / "vms"),
            "--register",
        )
        info = vbox("showvminfo", name, "--machinereadable")
        vm_id = re.search(r'^UUID="([^"]+)"', info, re.M)[1]
        vbox("setextradata", vm_id, "Agora3/managed", "true")
        for rule in re.findall(r'^Forwarding\(\d+\)="([^,]+),', info, re.M):
            vbox("modifyvm", vm_id, "--natpf1", "delete", rule)
        vbox("modifyvm", vm_id, "--natpf1", f"agora-ssh,tcp,127.0.0.1,{port},,22")
        hosts = (
            Path(base["known_hosts"]).read_text().replace(f"]:{base['ssh_port']} ", f"]:{port} ")
        )
        (folder / "known_hosts").write_text(hosts)
        config = {
            **base,
            "vm_id": vm_id,
            "ssh_port": port,
            "known_hosts": str(folder / "known_hosts"),
            "machine_directory": str(ROOT / "vms" / name),
        }
        destination.write_text(json.dumps(config, indent=2))
        vbox("snapshot", vm_id, "take", "trial-clean")
        listing = vbox("snapshot", vm_id, "list", "--machinereadable")
        snapshot_id = re.search(r'^SnapshotUUID="([^"]+)"', listing, re.M)[1]
        (folder / "baseline.json").write_text(
            json.dumps({"vm_id": vm_id, "snapshot_id": snapshot_id}, indent=2)
        )
        report[role] = vm_id
    yard_baseline = json.loads((ROOT / "machines/yard/baseline.json").read_text())
    (ROOT / "yard.json").write_text(
        json.dumps(
            {
                "machine_config": str(ROOT / "machines/yard/machine.json"),
                "snapshot_id": yard_baseline["snapshot_id"],
            },
            indent=2,
        )
    )
    print(
        json.dumps(
            {"root": str(ROOT), "frozen_source": str(frozen), "trial_vm_ids": report}, indent=2
        )
    )


if __name__ == "__main__":
    main()
