"""Import a selected text-source package through the normal native development operations."""

import argparse
import json
from pathlib import Path

from agora3.gateway import Gateway
from agora3.world import Refusal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument(
        "--id", required=True, help="Native package identity; agora.shell replaces the desk/chat"
    )
    parser.add_argument("--world", type=Path, default=Path("worlds/dev"))
    args = parser.parse_args()
    root = args.directory.resolve(strict=True)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    files = {}
    for path in root.rglob("*"):
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise Refusal("Package import refuses linked paths outside the selected directory.")
        if path.is_file() and path.name != "manifest.json" and "__pycache__" not in path.parts:
            files[path.relative_to(root).as_posix()] = path.read_text(encoding="utf-8")
    gateway = Gateway(args.world)
    actor = gateway.principal("human")
    try:
        revision = gateway.packages.get(args.id)["revision"]
    except Refusal:
        revision = 0
    gateway.packages.save(
        actor, id=args.id, expected_revision=revision, files=files, manifest=manifest
    )
    build = gateway.packages.build(actor, id=args.id, expected_revision=revision + 1)
    installed = gateway.packages.install(
        actor,
        id=args.id,
        build=build["build"],
        expected_revision=gateway.packages.installation(args.id)["revision"],
    )
    print(
        json.dumps(
            {
                "package": args.id,
                "source_revision": revision + 1,
                "installation_revision": installed["items"][0]["revision"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
