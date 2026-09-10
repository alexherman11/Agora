"""Build self-contained application releases from shared authored source.
Never bundle a native world, a credential, or runtime application state.
"""

import json
from pathlib import Path

from agora3.application_schema import BUNDLE, PROTOCOL
from agora3.packages import check_source, source_digest
from agora3.schemas import record

ROOT = Path(__file__).resolve().parents[1] / "examples/native-applications"
TEXT = {"type": "string", "maxLength": 3000}
NUMBER = {"type": "integer", "minimum": 0}
ANCHOR = record(
    {
        "revision": {"type": "integer", "minimum": 1},
        "text_hash": {"type": "string", "minLength": 64, "maxLength": 64},
        "start": NUMBER,
        "end": NUMBER,
        "quote": {"type": "string", "minLength": 1, "maxLength": 2000},
        "prefix": TEXT,
        "suffix": TEXT,
        "occurrences": {"type": "integer", "minimum": 1},
    }
)
SCHEMAS = {
    "text.format": record({"kind": {"enum": ["plain", "markdown"]}}),
    "text.annotations": record(
        {
            "threads": {
                "type": "array",
                "maxItems": 64,
                "items": record(
                    {
                        "id": {"type": "string", "maxLength": 100},
                        "message": TEXT,
                        "status": {"enum": ["open", "resolved"]},
                        "anchor": ANCHOR,
                    }
                ),
            }
        }
    ),
}
SCHEMAS.update(json.loads((ROOT / "shared/discussion-schemas.json").read_text(encoding="utf-8")))


def bundle(variant):
    if variant not in {"notes", "documents"}:
        raise ValueError("Choose notes or documents.")
    files = {
        "index.html": (ROOT / variant / "index.html").read_text(encoding="utf-8"),
        "app.js": (ROOT / variant / "app.js").read_text(encoding="utf-8"),
    }
    shared = ["sdk.js", "editor.js", "annotations.js", "discussions.js", "style.css"]
    if variant == "documents":
        shared += ["vendor.js", "THIRD-PARTY.md"]
        for name in (
            "live-markdown.bundle.js",
            "live-markdown.js",
            "editor-build/package.json",
            "editor-build/package-lock.json",
            "editor-build/LICENSES.txt",
        ):
            files[name] = (ROOT / "documents" / name).read_text(encoding="utf-8")
    for name in shared:
        files["shared/" + name] = (ROOT / "shared" / name).read_text(encoding="utf-8")
    facets = ["core.title", "core.text", "text.format", "text.annotations"]
    manifest = {
        "name": "Notes" if variant == "notes" else "Documents",
        "description": "A compact text view"
        if variant == "notes"
        else "A Markdown editor and preview",
        "runtime": "browser-1",
        "ui": {
            "entry": "index.html",
            "mount": "application",
            "styles": ["shared/style.css"],
            "scripts": (
                ["shared/vendor.js", "live-markdown.bundle.js"] if variant == "documents" else []
            )
            + [
                "shared/sdk.js",
                "shared/editor.js",
                "shared/annotations.js",
                "shared/discussions.js",
                "app.js",
            ],
        },
        "application": {
            "protocol": PROTOCOL,
            "accepts": ["core.text"],
            "read_facets": facets + ["studio.document"],
            "write_facets": facets,
            "schemas": SCHEMAS,
            "contracts": {
                "text": {
                    "protocol": "agora.text/1",
                    "formats": ["plain", "markdown"],
                    "editing": "source",
                    "selection_offsets": "utf16-code-units",
                    "operations": ["replace-text", "set-title", "select", "annotate", "discuss"],
                    "legacy_markdown_marker": "studio.document",
                }
            },
            "relations": {
                "discussions": {
                    "facet": "studio.comment-thread",
                    "subject_field": "document_id",
                    "write": True,
                    "max_items": 16,
                }
            },
            "size": {"width": 310, "height": 360}
            if variant == "notes"
            else {"width": 650, "height": 620},
            "create": {
                "core.title": {"text": "Untitled"},
                "core.text": {"text": ""},
                "text.format": {"kind": "plain" if variant == "notes" else "markdown"},
            },
        },
    }
    source = {"id": "agora." + variant, "files": files, "manifest": manifest}
    check_source(files, manifest)
    return {"format": BUNDLE, "source": source, "sha256": source_digest(source)}


def desktop_source():
    files = {
        name: (ROOT / "desktop" / name).read_text(encoding="utf-8")
        for name in ("index.html", "desktop.js", "chat.js", "style.css", "chat.css")
    }
    files["vendor.js"] = (ROOT / "shared/vendor.js").read_text(encoding="utf-8")
    files["THIRD-PARTY.md"] = (ROOT / "shared/THIRD-PARTY.md").read_text(encoding="utf-8")
    manifest = {
        "name": "Agora Application Workspace",
        "runtime": "browser-1",
        "ui": {
            "entry": "index.html",
            "mount": "shell",
            "scripts": ["vendor.js", "desktop.js", "chat.js"],
            "styles": ["style.css", "chat.css"],
        },
    }
    return {"id": "agora.shell", "files": files, "manifest": manifest}


def install_source(gateway, actor, source):
    try:
        existing = gateway.packages.get(source["id"])
        revision = existing["revision"]
    except ValueError:
        revision = 0
    gateway.packages.save(
        actor,
        id=source["id"],
        expected_revision=revision,
        files=source["files"],
        manifest=source["manifest"],
    )
    built = gateway.packages.build(actor, id=source["id"], expected_revision=revision + 1)
    gateway.packages.install(actor, **built["install_args"])


def prepare(gateway):
    """Seed a new isolated demonstration; preserve any existing installed work."""
    if gateway.packages.installation("agora.shell")["revision"]:
        return
    actor = gateway.principal("human")
    install_source(gateway, actor, desktop_source())
    for variant in ("notes", "documents"):
        gateway.dispatch(actor, "application.import", {"bundle": bundle(variant)})
    gateway.commit(
        actor,
        [
            {
                "id": "example.shared",
                "expected_revision": 0,
                "facets": {
                    "core.title": {"text": "Application field notes"},
                    "core.text": {
                        "text": "# One object, two views\n\n"
                        "Notes and Documents are showing the same native object.\n\n"
                        "- Edit a sentence in either view.\n"
                        "- Select a phrase and attach an annotation.\n"
                        "- Close a view; the object stays in Agora.\n\n"
                        "Each application has its own saved selection, draft and appearance."
                    },
                    "text.format": {"kind": "markdown"},
                },
            },
            {
                "id": "example.scratch",
                "expected_revision": 0,
                "facets": {
                    "core.title": {"text": "Scratchpad"},
                    "core.text": {"text": "What would you like to make next?"},
                    "text.format": {"kind": "plain"},
                },
            },
        ],
    )
    for package, subject, bounds in [
        ("agora.notes", "example.shared", {"x": 24, "y": 18, "width": 310, "height": 380}),
        ("agora.documents", "example.shared", {"x": 358, "y": 18, "width": 650, "height": 680}),
        ("agora.notes", "example.scratch", {"x": 24, "y": 424, "width": 310, "height": 274}),
    ]:
        gateway.dispatch(
            actor, "application.open", {"package": package, "subject": subject, "bounds": bounds}
        )
