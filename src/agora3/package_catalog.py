"""A compact development catalog. Source bodies remain available through focused source tools."""

from agora3.schemas import ALLOWED


def catalog(gateway):
    packages = []
    with gateway.lock:
        rows = gateway.packages.list()
        installs = {o["facets"]["agora.installation"]["package"]: o for o in rows["installations"]}
        for obj in rows["packages"]:
            source = obj["facets"]["agora.package"]
            manifest = source["manifest"]
            installation = installs.get(source["id"])
            current = installation["facets"]["agora.installation"] if installation else {}
            packages.append(
                {
                    "package_id": source["id"],
                    "source_object_id": obj["id"],
                    "source_revision": obj["revision"],
                    "installation_revision": installation["revision"] if installation else 0,
                    "installed_source_revision": current.get("source_revision"),
                    "installed_build": current.get("build"),
                    "name": manifest.get("name", source["id"]),
                    "runtime": manifest["runtime"],
                    "actions": list(manifest.get("actions", {})),
                    "skills": list(manifest.get("skills", {})),
                    "ui_entry": manifest.get("ui", {}).get("entry"),
                    "files": [
                        {"path": path, "bytes": len(body.encode())}
                        for path, body in source["files"].items()
                    ],
                }
            )
    return {
        "packages": packages,
        "source_included": False,
        "schema_keywords": sorted(ALLOWED),
        "revision_help": {
            "package_id": "Use this with package operations; source_object_id is for world.get.",
            "source_revision": "Expected revision for source save, patch and build.",
            "installation_revision": (
                "Expected revision for install/restore and installed action invocation."
            ),
            "installed_source_revision": "May differ from the latest saved source revision.",
        },
    }


SPEC = {
    "name": "package.catalog",
    "description": (
        "Compact package discovery without source bodies: distinct package IDs, source object IDs, "
        "source/install revisions, action names and file sizes. Also lists supported JSON schema "
        "keywords. Start here, then read only the package/files you need."
    ),
    "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
}
