"""Read-only coherent capture of installed definitions, never credentials or user subjects."""

import hashlib
import json
import sqlite3
from pathlib import Path

ROOT = Path("C:/Projects/Agora/local/arrangement-current-20260916")
WORLD = Path("C:/Projects/Agora/worlds/parallel-desk/world")
CODE = Path("C:/Projects/Agora4")


def main():
    target = ROOT / "definition-snapshot.json"
    if target.exists():
        raise RuntimeError("Snapshot exists; retain its identity rather than overwrite it.")
    with sqlite3.connect((WORLD / "world.db").as_uri() + "?mode=ro", uri=True) as db:
        db.execute("BEGIN")
        watermark = db.execute("select max(seq) from events").fetchone()[0]
        objects = {
            o["id"]: o for (s,) in db.execute("select body from objects") for o in [json.loads(s)]
        }
        records = {k: v for k, v in objects.items() if "agora.schema" in v["facets"]}
        inventory = []
        for obj in objects.values():
            install = obj["facets"].get("agora.installation")
            if not install or install.get("enabled") is False:
                continue
            build = objects[install["build"]]
            source = build["facets"]["agora.build"]["source"]
            package_id = "agora.package." + source["id"]
            records[package_id] = {"id": package_id, "facets": {"agora.package": source}}
            records[build["id"]] = build
            records[obj["id"]] = obj
            inventory.append(
                {
                    "package": source["id"],
                    "installation_revision": obj["revision"],
                    "source_revision": install["source_revision"],
                    "build": build["id"],
                    "digest": install["digest"],
                }
            )
    files = {
        str(p.relative_to(CODE)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (CODE / "src").rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }
    snapshot = {
        "scope": "installed package definitions with synthetic subjects; not active-world clone",
        "origin_world": str(WORLD),
        "origin_watermark": watermark,
        "inventory": inventory,
        "native_source_hashes": files,
        "records": list(records.values()),
    }
    target.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "snapshot": str(target),
                "watermark": watermark,
                "packages": inventory,
                "records": len(records),
            }
        )
    )


if __name__ == "__main__":
    main()
