"""Focused native source access; edits remain atomic revision-checked package saves."""

import hashlib

from agora3.world import Refusal


def source_specs():
    string = {"type": "string"}
    specs = [
        (
            "package.read",
            "Read package manifest and file inventory without whole source. With path, read "
            "bounded "
            "lines (1-based); content is capped at 16000 characters and explicitly marked when "
            "truncated. Returns source revision and file digest.",
            {
                "id": string,
                "path": string,
                "start_line": {"type": "integer", "minimum": 1},
                "line_count": {"type": "integer", "minimum": 1, "maximum": 400},
            },
            ["id"],
        ),
        (
            "package.search",
            "Find literal source text and bounded snippets in one package. No regex or execution. "
            "Returns source revision for subsequent exact edits.",
            {
                "id": string,
                "text": {"type": "string", "minLength": 1},
                "path": string,
                "limit": {"type": "integer", "minimum": 1, "maximum": 50},
            },
            ["id", "text"],
        ),
        (
            "package.patch",
            "Atomically edit retained source at expected_revision. Each edit is "
            "{path,old,new,count?:1} for exact replacements; "
            "{path,content} to create/replace a file; "
            "or {path,delete:true}. All edits must succeed and the final package must validate. "
            "Unmatched or ambiguous old text refuses the entire batch. Optional manifest replaces "
            "the manifest. This saves source only; build and install remain explicit.",
            {
                "id": string,
                "expected_revision": {"type": "integer", "minimum": 1},
                "edits": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 100,
                    "items": {"type": "object"},
                },
                "manifest": {"type": "object"},
            },
            ["id", "expected_revision", "edits"],
        ),
    ]
    return [
        {
            "name": name,
            "description": description,
            "input_schema": {
                "type": "object",
                "properties": props,
                "required": required,
                "additionalProperties": False,
            },
        }
        for name, description, props, required in specs
    ]


def dispatch_source(gateway, actor, name, args):
    obj = gateway.packages.get(args["id"])
    source = obj["facets"]["agora.package"]
    files = source["files"]
    result = {
        "id": args["id"],
        "revision": obj["revision"],
        "source_revision": obj["revision"],
        "installation_revision": gateway.packages.installation(args["id"])["revision"],
    }
    if name == "package.read":
        result["manifest"] = source["manifest"]
        result["files"] = [
            {
                "path": path,
                "bytes": len(text.encode()),
                "lines": len(text.splitlines()),
                "sha256": hashlib.sha256(text.encode()).hexdigest(),
            }
            for path, text in files.items()
        ]
        if "path" in args:
            path = args["path"]
            if path not in files:
                raise Refusal("Source path not found.")
            start = args.get("start_line", 1)
            lines = files[path].splitlines(keepends=True)
            selected = "".join(lines[start - 1 : start - 1 + args.get("line_count", 100)])
            result.update(
                path=path,
                start_line=start,
                content=selected[:16000],
                truncated=len(selected) > 16000,
                more_lines=start - 1 + args.get("line_count", 100) < len(lines),
            )
        return result
    if name == "package.search":
        path = args.get("path")
        if path is not None and path not in files:
            raise Refusal("Source path not found.")
        matches = []
        for file, body in files.items():
            if path is not None and path != file:
                continue
            for number, line in enumerate(body.splitlines(), 1):
                column = line.find(args["text"])
                if column >= 0:
                    matches.append(
                        {
                            "path": file,
                            "line": number,
                            "column": column + 1,
                            "snippet": line[max(0, column - 80) : column + 240],
                        }
                    )
        limit = args.get("limit", 20)
        return result | {
            "matches": matches[:limit],
            "total_matching_lines": len(matches),
            "truncated": len(matches) > limit,
        }
    if name != "package.patch":
        raise Refusal("Unknown source operation.")
    if obj["revision"] != args["expected_revision"]:
        raise Refusal("Source revision changed; read the current source before patching.")
    updated = dict(files)
    for edit in args["edits"]:
        path = edit.get("path")
        if not isinstance(path, str):
            raise Refusal("Each source edit requires a path.")
        keys = set(edit)
        if keys == {"path", "content"} and isinstance(edit["content"], str):
            updated[path] = edit["content"]
        elif keys == {"path", "delete"} and edit["delete"] is True:
            if path not in updated:
                raise Refusal("Cannot delete a missing source path.")
            del updated[path]
        elif {"path", "old", "new"} <= keys <= {"path", "old", "new", "count"}:
            old, new, count = edit["old"], edit["new"], edit.get("count", 1)
            if (
                path not in updated
                or not isinstance(old, str)
                or not old
                or not isinstance(new, str)
                or type(count) is not int
                or not 1 <= count <= 100
            ):
                raise Refusal(
                    "Exact replacements require an existing path, nonempty old text, "
                    "new text and count 1-100."
                )
            actual = updated[path].count(old)
            if actual != count:
                raise Refusal(
                    f"Exact replacement expected {count} occurrence(s) in {path}; "
                    f"found {actual}. No edits saved."
                )
            updated[path] = updated[path].replace(old, new, count)
        else:
            raise Refusal("Invalid source edit form.")
    transaction = gateway.packages.save(
        actor,
        id=args["id"],
        expected_revision=obj["revision"],
        files=updated,
        manifest=args.get("manifest", source["manifest"]),
    )
    return {
        "id": args["id"],
        "revision": obj["revision"] + 1,
        "source_revision": obj["revision"] + 1,
        "installation_revision": gateway.packages.installation(args["id"])["revision"],
        "changed_paths": sorted({edit["path"] for edit in args["edits"]}),
        "transaction": {
            "watermark": transaction["watermark"],
            "items": [
                {"id": item["id"], "revision": item["revision"]} for item in transaction["items"]
            ],
        },
        "installed": False,
    }
