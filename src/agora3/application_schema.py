"""The small browser-application contract and portable source envelope.
Never execute package code or infer authority from a package declaration.
"""

import re

from agora3.schemas import check_schema, validate
from agora3.world import Refusal, encoded, identifier

PROTOCOL = "agora.application/1"
BUNDLE = "agora.application-bundle/1"


def check_application(manifest):
    app = manifest.get("application")
    if app is None:
        return
    if (
        manifest.get("runtime") != "browser-1"
        or manifest.get("ui", {}).get("mount") != "application"
    ):
        raise Refusal("Applications require browser-1 and ui.mount: application.")
    keys = {"protocol", "accepts", "read_facets", "write_facets", "size", "create", "schemas"}
    if (
        not isinstance(app, dict)
        or not keys <= set(app)
        or set(app) - keys - {"contracts", "relations"}
        or app["protocol"] != PROTOCOL
    ):
        raise Refusal(
            "Application requires protocol, accepts, read_facets, write_facets, "
            "size, create, schemas."
        )
    for key in ("accepts", "read_facets", "write_facets"):
        names = app[key]
        if (
            not isinstance(names, list)
            or not 1 <= len(names) <= 30
            or any(not isinstance(name, str) for name in names)
            or len(set(names)) != len(names)
        ):
            raise Refusal(f"application.{key} requires 1–30 distinct facet names.")
        for name in names:
            identifier(name)
            if name.startswith("agora."):
                raise Refusal("Applications cannot request protected runtime facets.")
    if not set(app["accepts"]) <= set(app["read_facets"]):
        raise Refusal("Accepted facets must also be readable.")
    if not set(app["write_facets"]) <= set(app["read_facets"]):
        raise Refusal("Writable facets must also be readable.")
    validate(
        {
            "type": "object",
            "properties": {
                "width": {"type": "integer", "minimum": 220, "maximum": 1400},
                "height": {"type": "integer", "minimum": 180, "maximum": 1200},
            },
            "required": ["width", "height"],
            "additionalProperties": False,
        },
        app["size"],
    )
    if not isinstance(app["create"], dict) or not set(app["create"]) <= set(app["write_facets"]):
        raise Refusal("Creation defaults must use the application's writable facets.")
    if not set(app["accepts"]) <= set(app["create"]):
        raise Refusal("Creation defaults must supply accepted facets.")
    if not isinstance(app["schemas"], dict) or len(app["schemas"]) > 20:
        raise Refusal("Application schemas must be a map of at most 20 definitions.")
    for name, schema in app["schemas"].items():
        identifier(name)
        if name.startswith(("agora.", "core.")):
            raise Refusal("Application bundles cannot define protected or core schemas.")
        check_schema(schema)
    contracts = app.get("contracts", {})
    if not isinstance(contracts, dict) or len(encoded(contracts)) > 10000:
        raise Refusal("Application contracts must be a bounded descriptive object.")
    relations = app.get("relations", {})
    if not isinstance(relations, dict) or len(relations) > 8:
        raise Refusal("Application relations must declare at most eight collections.")
    for name, rule in relations.items():
        identifier(name)
        if not isinstance(rule, dict) or set(rule) != {
            "facet",
            "subject_field",
            "write",
            "max_items",
        }:
            raise Refusal("A relation requires facet, subject_field, write and max_items.")
        identifier(rule["facet"])
        identifier(rule["subject_field"])
        if rule["facet"].startswith(("agora.", "core.")):
            raise Refusal("Relations cannot grant access to runtime or core facets.")
        if (
            type(rule["write"]) is not bool
            or type(rule["max_items"]) is not int
            or not 1 <= rule["max_items"] <= 100
        ):
            raise Refusal("Relation write must be boolean and max_items must be 1–100.")


def schema_changes(world, manifest):
    """Keep compatible shared definitions; refuse implicit schema migrations."""
    changes, guards = [], {}
    for name, schema in manifest.get("application", {}).get("schemas", {}).items():
        oid = "agora.schema." + name
        try:
            current = world.get(oid)
        except Refusal:
            current = None
        if current:
            guards[oid] = current["revision"]
            if encoded(current["facets"]["agora.schema"]["schema"]) != encoded(schema):
                raise Refusal(
                    f"Schema {name} already has a different definition; migrate explicitly."
                )
        else:
            changes.append(
                {
                    "id": oid,
                    "expected_revision": 0,
                    "facets": {
                        "agora.schema": {
                            "type": name,
                            "schema": schema,
                            "merge": "register",
                            "projection": "generic",
                        }
                    },
                }
            )
    return changes, guards


def check_bundle(bundle):
    if not isinstance(bundle, dict) or set(bundle) != {"format", "source", "sha256"}:
        raise Refusal("Application bundle requires format, source and sha256.")
    if bundle["format"] != BUNDLE or not re.fullmatch(r"[0-9a-f]{64}", str(bundle["sha256"])):
        raise Refusal("Unsupported application bundle format or digest.")
    source = bundle["source"]
    if not isinstance(source, dict) or set(source) != {"id", "files", "manifest"}:
        raise Refusal("Bundle source requires id, files and manifest.")
    identifier(source["id"])
    if source["id"] == "agora.shell":
        raise Refusal("An application download cannot replace the desktop shell.")
    if not isinstance(source["manifest"], dict) or not source["manifest"].get("application"):
        raise Refusal("The bundle must contain a browser application.")
