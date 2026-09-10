"""Deterministic text assembly for the bounded browser-1 runtime; no host execution."""

import hashlib
import re

from agora3.world import Refusal


def validate_assets(files, ui):
    for kind, extension in [("scripts", ".js"), ("styles", ".css")]:
        paths = ui.get(kind, [])
        if (
            not isinstance(paths, list)
            or len(paths) > 32
            or any(not isinstance(p, str) for p in paths)
        ):
            raise Refusal(f"ui.{kind} requires an ordered list of at most 32 package paths.")
        if len(paths) != len(set(paths)):
            raise Refusal(f"ui.{kind} cannot repeat a path.")
        if any(p not in files or not p.endswith(extension) for p in paths):
            raise Refusal(f"ui.{kind} requires existing package-local {extension} files.")
        if paths:
            marker = "<!-- agora:" + kind + " -->"
            if files[ui["entry"]].count(marker) != 1:
                raise Refusal(f"HTML entry must contain exactly one {marker} marker.")
            tag = "script" if kind == "scripts" else "style"
            if any(re.search(r"</\s*" + tag, files[p], re.I) for p in paths):
                raise Refusal(
                    f"ui.{kind} source contains a closing {tag} tag; "
                    "escape or remove it before assembly."
                )


def assemble(source):
    ui, files = source["manifest"]["ui"], source["files"]
    validate_assets(files, ui)
    html = files[ui["entry"]]
    for kind in ["styles", "scripts"]:
        paths = ui.get(kind, [])
        if not paths:
            continue
        tag = "style" if kind == "styles" else "script"
        chunks = []
        for path in paths:
            suffix = (
                ""
                if kind == "styles"
                else "\n//# sourceURL=agora-package/" + source["id"] + "/" + path
            )
            chunks.append(
                "<"
                + tag
                + ' data-agora-source="'
                + path
                + '">\n'
                + files[path]
                + suffix
                + "\n</"
                + tag
                + ">"
            )
        html = html.replace("<!-- agora:" + kind + " -->", "\n".join(chunks))
    if len(html.encode("utf-8")) > 2_000_000:
        raise Refusal("Assembled browser HTML is limited to 2 MB.")
    return {
        "html": html,
        "sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
        "scripts": ui.get("scripts", []),
        "styles": ui.get("styles", []),
        "assembly_version": 1,
    }


def retained_html(receipt):
    artifact = receipt.get("browser_artifact")
    if artifact is None:
        source = receipt["source"]
        return source["files"][source["manifest"]["ui"]["entry"]]
    if (
        not isinstance(artifact, dict)
        or artifact.get("source_digest") != receipt["digest"]
        or not isinstance(artifact.get("html"), str)
        or hashlib.sha256(artifact["html"].encode("utf-8")).hexdigest() != artifact.get("sha256")
    ):
        raise Refusal("Not an intact retained browser artifact.")
    return artifact["html"]
