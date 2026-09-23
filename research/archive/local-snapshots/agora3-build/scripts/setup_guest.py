"""Provision a dedicated Ubuntu VirtualBox guest; never adopt an existing VM.

Run: uv run --with pycdlib==1.14.0 python scripts/setup_guest.py --world worlds/dev --start
Only this setup command needs pycdlib. Runtime execution uses stdlib and OpenSSH.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from uuid import uuid4

RELEASE = "https://cloud-images.ubuntu.com/releases/noble/release-20260826/"
IMAGE = "ubuntu-24.04-server-cloudimg-amd64.vmdk"
SHA256 = "fb3ba097a9013d759fa13ab22d2b4118bd55452c617ca3758a55303eea96de6e"
PROJECT = Path(__file__).resolve().parents[1]
VBOX = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Oracle/VirtualBox/VBoxManage.exe"


def run(*args: str) -> str:
    done = subprocess.run(
        list(args),
        capture_output=True,
        text=True,
        check=False,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    if done.returncode:
        raise RuntimeError(f"{args[0]} failed: {done.stderr.strip()}")
    return done.stdout


def vbox(*args: str) -> str:
    return run(str(VBOX) if os.name == "nt" else "VBoxManage", *args)


def generate_key(path: Path) -> None:
    run("ssh-keygen", "-t", "ed25519", "-N", "", "-C", "Agora3 dedicated guest", "-f", str(path))
    if os.name == "nt":
        account = run("whoami").strip()
        run("icacls", str(path), "/inheritance:r", "/grant:r", f"{account}:(F)", "SYSTEM:(F)")
    else:
        path.chmod(0o600)


def seed_iso(destination: Path, public_key: str, host_key: Path, vm_id: str) -> None:
    import pycdlib

    user_data = {
        "hostname": "agora3",
        "manage_etc_hosts": True,
        "users": [
            {
                "name": "jeff",
                "groups": "sudo",
                "shell": "/bin/bash",
                "lock_passwd": True,
                "sudo": "ALL=(ALL) NOPASSWD:ALL",
                "ssh_authorized_keys": [public_key],
            }
        ],
        "disable_root": True,
        "ssh_pwauth": False,
        "ssh_keys": {
            "ed25519_private": host_key.read_text(encoding="utf-8"),
            "ed25519_public": host_key.with_suffix(".pub").read_text(encoding="utf-8"),
        },
        "write_files": [
            {"path": "/etc/agora3-machine", "permissions": "0644", "content": vm_id},
            {
                "path": "/etc/ssh/sshd_config.d/00-agora3.conf",
                "permissions": "0644",
                "content": "PasswordAuthentication no\nPermitRootLogin no\nAllowUsers jeff\n",
            },
        ],
        "runcmd": [["mkdir", "-p", "/opt/agora"], ["systemctl", "restart", "ssh"]],
        "final_message": "Agora3 guest initialization completed.",
    }
    files = {
        "user-data": "#cloud-config\n" + json.dumps(user_data),
        "meta-data": json.dumps({"instance-id": vm_id, "local-hostname": "agora3"}),
    }
    iso = pycdlib.PyCdlib()
    iso.new(interchange_level=3, joliet=3, rock_ridge="1.09", vol_ident="CIDATA")
    buffers = []
    for index, (name, content) in enumerate(files.items()):
        stream = io.BytesIO(content.encode("utf-8"))
        buffers.append(stream)
        iso.add_fp(
            stream,
            len(stream.getvalue()),
            iso_path=f"/FILE{index}.;1",
            rr_name=name,
            joliet_path=f"/{name}",
        )
    iso.write(str(destination))
    iso.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world", type=Path, required=True)
    parser.add_argument("--directory", type=Path, default=PROJECT / "local/guest")
    parser.add_argument("--port", type=int, default=22333)
    parser.add_argument("--start", action="store_true")
    args = parser.parse_args()
    world, folder = args.world.resolve(), args.directory.resolve()
    if not 1024 <= args.port <= 65535:
        parser.error("port must be between 1024 and 65535")
    config_path = world / "machine.json"
    if config_path.exists():
        parser.error(
            "machine.json already exists; inspect/start that guest instead of reprovisioning"
        )
    folder.mkdir(parents=True, exist_ok=True)
    image = folder / IMAGE
    if not image.exists():
        print(f"Downloading pinned Ubuntu image from {RELEASE}", flush=True)
        partial = image.with_suffix(".download")
        urllib.request.urlretrieve(RELEASE + IMAGE, partial)
        partial.replace(image)
    with image.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != SHA256:
        raise RuntimeError("Ubuntu image SHA256 mismatch. Refusing to create a guest.")
    vm_id = str(uuid4())
    name = "Agora3-" + vm_id[:8]
    owned = folder / vm_id
    owned.mkdir()
    identity, host_key = owned / "id_ed25519", owned / "ssh_host_ed25519_key"
    generate_key(identity)
    generate_key(host_key)
    public_key = identity.with_suffix(".pub").read_text(encoding="utf-8").strip()
    known_hosts = owned / "known_hosts"
    host_public = host_key.with_suffix(".pub").read_text(encoding="utf-8").strip()
    known_hosts.write_text(f"[127.0.0.1]:{args.port} {host_public}\n", encoding="utf-8")
    seed = owned / "seed.iso"
    seed_iso(seed, public_key, host_key, vm_id)
    disk = owned / "system.vdi"
    print(f"Creating {name}; image hash verified. Existing VMs will not be changed.", flush=True)
    vbox("clonemedium", "disk", str(image), str(disk), "--format", "VDI")
    vbox("modifymedium", "disk", str(disk), "--resize", "16384")
    vbox(
        "createvm",
        "--name",
        name,
        "--uuid",
        vm_id,
        "--ostype",
        "Ubuntu_64",
        "--basefolder",
        str(owned),
        "--register",
    )
    vbox("setextradata", vm_id, "Agora3/managed", "true")
    vbox(
        "modifyvm",
        vm_id,
        "--memory",
        "2048",
        "--cpus",
        "1",
        "--ioapic",
        "on",
        "--graphicscontroller",
        "vmsvga",
        "--vram",
        "16",
        "--audio-enabled",
        "off",
        "--clipboard-mode",
        "disabled",
        "--drag-and-drop",
        "disabled",
        "--usb",
        "off",
        "--nic1",
        "nat",
        "--nictype1",
        "virtio",
        "--cableconnected1",
        "on",
        "--natpf1",
        f"agora3-ssh,tcp,127.0.0.1,{args.port},,22",
        "--uart1",
        "0x3F8",
        "4",
        "--uartmode1",
        "file",
        str(owned / "serial.log"),
    )
    vbox(
        "storagectl",
        vm_id,
        "--name",
        "SATA",
        "--add",
        "sata",
        "--controller",
        "IntelAhci",
        "--portcount",
        "2",
    )
    vbox(
        "storageattach",
        vm_id,
        "--storagectl",
        "SATA",
        "--port",
        "0",
        "--device",
        "0",
        "--type",
        "hdd",
        "--medium",
        str(disk),
    )
    vbox(
        "storageattach",
        vm_id,
        "--storagectl",
        "SATA",
        "--port",
        "1",
        "--device",
        "0",
        "--type",
        "dvddrive",
        "--medium",
        str(seed),
    )
    vbox(
        "modifyvm",
        vm_id,
        "--boot1",
        "disk",
        "--boot2",
        "none",
        "--boot3",
        "none",
        "--boot4",
        "none",
    )
    config = {
        "backend": "virtualbox",
        "vm_id": vm_id,
        "ssh_host": "127.0.0.1",
        "ssh_port": args.port,
        "ssh_user": "jeff",
        "identity_file": str(identity),
        "known_hosts": str(known_hosts),
        "image_url": RELEASE + IMAGE,
        "image_sha256": SHA256,
        "machine_directory": str(owned),
        "profile": "broad guest root; NAT egress; no shared folders, clipboard or host credentials",
    }
    world.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    shutil.copyfile(config_path, owned / "machine.json")
    if args.start:
        vbox("startvm", vm_id, "--type", "headless")
    print(
        json.dumps(
            {
                "created": name,
                "vm_id": vm_id,
                "config_path": str(config_path),
                "boot_requested": args.start,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
