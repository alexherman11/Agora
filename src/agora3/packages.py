"""Versioned source, immutable build receipts, and installed capabilities.
Never execute guest-authored source on the host or bypass the native gateway.
"""

import hashlib
import re
import tempfile
import uuid
from pathlib import PurePosixPath

from agora3.application_schema import check_application, schema_changes
from agora3.browser_assembly import assemble, retained_html, validate_assets
from agora3.schemas import check_schema, validate, validate_facets
from agora3.scoped_context import assert_reads, check_reads, scoped_snapshot
from agora3.world import Refusal, World, encoded, identifier


def source_digest(source):
    return hashlib.sha256(encoded(source).encode()).hexdigest()


def check_source(files, manifest):
    if not isinstance(files, dict) or not 1 <= len(files) <= 100:
        raise Refusal("A package requires 1–100 relative source files.")
    for name, body in files.items():
        path = PurePosixPath(name)
        if (
            not name
            or not re.fullmatch(r"[A-Za-z0-9_./-]+", name)
            or path.is_absolute()
            or any(p in ("", ".", "..") for p in name.split("/"))
            or not isinstance(body, str)
        ):
            raise Refusal("Source paths must be safe relative paths; source content must be text.")
        if len(body.encode()) > 1_000_000:
            raise Refusal("A source file is limited to 1 MB.")
    if len(encoded(files).encode()) > 2_000_000:
        raise Refusal("A package is limited to 2 MB of source.")
    if not isinstance(manifest, dict) or set(manifest) - {
        "name",
        "description",
        "runtime",
        "actions",
        "ui",
        "skills",
        "application",
    }:
        raise Refusal(
            "Manifest supports name, description, runtime, actions, ui, skills, application. "
            "Dependencies are not implemented."
        )
    if manifest.get("runtime") not in ("python-1", "browser-1"):
        raise Refusal("runtime must be python-1 (Linux Python) or browser-1 (sandboxed HTML).")
    actions = manifest.get("actions", {})
    if not isinstance(actions, dict) or len(actions) > 50:
        raise Refusal("actions must be a map of up to 50 named actions.")
    for name, action in actions.items():
        identifier(name)
        if manifest["runtime"] != "python-1" or not isinstance(action, dict):
            raise Refusal("Headless actions use the python-1 runtime.")
        if set(action) - {"entry", "description", "input_schema", "output_schema", "reads"}:
            raise Refusal(
                "An action accepts entry, description, input_schema, output_schema, "
                "and optional reads."
            )
        if "reads" in action:
            check_reads(action["reads"])
        entry = action.get("entry", "")
        if (
            ":" not in entry
            or entry.split(":")[0] not in files
            or not entry.split(":")[0].endswith(".py")
        ):
            raise Refusal("Action entry must be an existing Python file:function.")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", entry.split(":", 1)[1]):
            raise Refusal("Action entry function must be a Python identifier.")
        check_schema(action.get("input_schema", {}))
        if "output_schema" in action:
            check_schema(action["output_schema"])
    if "ui" in manifest:
        ui = manifest["ui"]
        if (
            not isinstance(ui, dict)
            or set(ui) - {"entry", "mount", "scripts", "styles"}
            or ui.get("entry") not in files
        ):
            raise Refusal("ui requires a source entry and optional shell mount.")
        if manifest["runtime"] != "browser-1" or not ui["entry"].endswith(".html"):
            raise Refusal("This browser runtime requires a self-contained HTML entry.")
        validate_assets(files, ui)
    skills = manifest.get("skills", {})
    if not isinstance(skills, dict) or not all(
        isinstance(v, str) and v in files for v in skills.values()
    ):
        raise Refusal("skills maps skill names to retained instruction files.")
    check_application(manifest)


class Packages:
    def __init__(self, world, guest, yard, commit, check_authority):
        self.world, self.guest = world, guest
        self.yard = yard
        self.commit, self.check_authority = commit, check_authority

    def get(self, package_id):
        return self.world.get("agora.package." + identifier(package_id))

    def save(self, actor, *, id, expected_revision, files, manifest):
        identifier(id)
        check_source(files, manifest)
        return self.commit(
            actor,
            [
                {
                    "id": "agora.package." + id,
                    "expected_revision": expected_revision,
                    "facets": {"agora.package": {"id": id, "files": files, "manifest": manifest}},
                }
            ],
            internal=True,
        )

    def list(self):
        return {
            "packages": self.world.query(["agora.package"], 1000)["items"],
            "installations": self.world.query(["agora.installation"], 1000)["items"],
        }

    def installation(self, package_id):
        try:
            return self.world.get("agora.installation." + identifier(package_id))
        except Refusal:
            return {"id": "agora.installation." + package_id, "revision": 0, "facets": {}}

    def build(self, actor, *, id, expected_revision):
        obj = self.get(id)
        if obj["revision"] != expected_revision:
            raise Refusal("Source revision changed; read it before building.")
        source = obj["facets"]["agora.package"]
        base_installation = self.installation(id)
        browser_artifact = (
            assemble(source)
            if source["manifest"]["runtime"] == "browser-1" and "ui" in source["manifest"]
            else None
        )
        check_source(source["files"], source["manifest"])
        diagnostics = {
            "check": "HTML entry and manifest admitted; browser interaction not yet tested"
        }
        if source["manifest"]["runtime"] == "python-1":
            files = dict(source["files"])
            if "__agora_check.py" in files:
                raise Refusal("__agora_check.py is reserved for build validation.")
            files["__agora_check.py"] = (
                "def main(arguments, context):\n    return {'compiled': True}\n"
            )
            self.check_authority(actor)
            diagnostics = self.yard.run(files, "__agora_check.py:main", {}, {}, timeout=30)
            self.check_authority(actor)
        build_id = "agora.build." + uuid.uuid4().hex
        receipt = {
            "package": id,
            "source_revision": expected_revision,
            "digest": source_digest(source),
            "source": source,
            "diagnostics": diagnostics,
            "runtime_contract": source["manifest"]["runtime"],
            "base_installation_revision": base_installation["revision"],
            "environment": "browser"
            if source["manifest"]["runtime"] == "browser-1"
            else self.yard.status(),
        }
        if browser_artifact is not None:
            receipt["browser_artifact"] = dict(browser_artifact, source_digest=receipt["digest"])
            diagnostics.update(
                assembled_html_sha256=browser_artifact["sha256"],
                assembled_bytes=len(browser_artifact["html"].encode("utf-8")),
            )
        self.commit(
            actor,
            [{"id": build_id, "expected_revision": 0, "facets": {"agora.build": receipt}}],
            internal=True,
            guards={
                obj["id"]: expected_revision,
                base_installation["id"]: base_installation["revision"],
            },
        )
        return {
            "build": build_id,
            "digest": receipt["digest"],
            "diagnostics": diagnostics,
            "package_id": id,
            "source_revision": expected_revision,
            "base_installation_revision": base_installation["revision"],
            "install_args": {
                "id": id,
                "build": build_id,
                "expected_revision": base_installation["revision"],
            },
            "installed": False,
        }

    def receipt(self, build):
        obj = self.world.get(build)
        receipt = obj["facets"].get("agora.build")
        if receipt is None or source_digest(receipt["source"]) != receipt["digest"]:
            raise Refusal("Not an intact native build receipt.")
        if "browser_artifact" in receipt:
            retained_html(receipt)
        return receipt

    def install(self, actor, *, id, build, expected_revision, restore=False):
        receipt = self.receipt(build)
        if receipt["package"] != id:
            raise Refusal("Build belongs to another package.")
        guards = {} if restore else {"agora.package." + id: receipt["source_revision"]}
        if not restore and receipt["base_installation_revision"] != expected_revision:
            raise Refusal(
                "Installation changed since this build; rebuild against the current installation."
            )
        value = {
            "package": id,
            "build": build,
            "digest": receipt["digest"],
            "source_revision": receipt["source_revision"],
        }
        definitions, schema_guards = schema_changes(self.world, receipt["source"]["manifest"])
        guards.update(schema_guards)
        return self.commit(
            actor,
            definitions
            + [
                {
                    "id": "agora.installation." + id,
                    "expected_revision": expected_revision,
                    "facets": {"agora.installation": value},
                }
            ],
            internal=True,
            guards=guards,
        )

    def tools(self):
        result = []
        for obj in self.world.query(["agora.installation"], 1000)["items"]:
            installation = obj["facets"]["agora.installation"]
            if installation.get("enabled") is False:
                continue
            source = self.receipt(installation["build"])["source"]
            for name, action in source["manifest"].get("actions", {}).items():
                result.append(
                    {
                        "package": installation["package"],
                        "revision": obj["revision"],
                        "action": name,
                        **action,
                    }
                )
        return result

    def skills(self):
        result = []
        for obj in self.world.query(["agora.installation"], 1000)["items"]:
            installation = obj["facets"]["agora.installation"]
            if installation.get("enabled") is False:
                continue
            source = self.receipt(installation["build"])["source"]
            for name, path in source["manifest"].get("skills", {}).items():
                result.append(
                    {
                        "package": installation["package"],
                        "revision": obj["revision"],
                        "name": name,
                        "instructions": source["files"][path],
                    }
                )
        return {"skills": result}

    def invoke(self, actor, *, package, revision, action, args, candidate=None):
        installation = self.installation(package)
        if candidate:
            receipt = self.receipt(candidate)
            if receipt["package"] != package:
                raise Refusal("Candidate belongs to another package.")
        else:
            if installation.get("facets", {}).get("agora.installation", {}).get("enabled") is False:
                raise Refusal(
                    "This package has been disabled; install it before invoking its actions."
                )
            if installation["revision"] != revision or revision == 0:
                raise Refusal("Installed action changed; discover current tools before invoking.")
            receipt = self.receipt(installation["facets"]["agora.installation"]["build"])
        source = receipt["source"]
        spec = source["manifest"].get("actions", {}).get(action)
        if spec is None:
            raise Refusal("This action is not exported by the selected package version.")
        validate(spec.get("input_schema", {}), args)
        scoped = "reads" in spec
        snapshot = (
            scoped_snapshot(self.world, spec["reads"], args)
            if scoped
            else self.world.query(limit=1000)
        )
        if not snapshot["complete"]:
            raise Refusal("This runtime supports at most 1000 objects per action snapshot.")
        self.check_authority(actor)
        runner = self.yard if candidate else self.guest
        output = runner.run(
            source["files"],
            spec["entry"],
            args,
            {
                "objects": snapshot["items"],
                "watermark": snapshot["watermark"],
                "candidate": bool(candidate),
                **(
                    {"missing_ids": snapshot["missing_ids"], "declared_reads": spec["reads"]}
                    if scoped
                    else {}
                ),
            },
            timeout=30,
        )
        self.check_authority(actor)
        if not isinstance(output, dict):
            raise Refusal(
                "An action must return an object: {result: JSON, changes: [...] optional}."
            )
        result = output.get("result", output)
        if "output_schema" in spec:
            validate(spec["output_schema"], result)
        changes = output.get("changes", [])
        if candidate:
            with tempfile.TemporaryDirectory(prefix="agora-candidate-") as directory:
                disposable = World(directory)
                with self.world.connection() as source_db, disposable.connection() as target_db:
                    source_db.backup(target_db)
                if changes:
                    if scoped:
                        assert_reads(disposable, snapshot["read_guards"])
                    disposable.commit(
                        actor.name,
                        changes,
                        validate_facets,
                        watermark=None if scoped else snapshot["watermark"],
                    )
            return {
                "result": result,
                "proposed_changes": changes,
                "candidate": True,
                "native_writes": 0,
                "guest_isolation": "separate resettable candidate VM, no live world token",
            }
        committed = None
        if changes:
            committed = self.commit(
                actor,
                changes,
                watermark=None if scoped else snapshot["watermark"],
                read_guards=snapshot["read_guards"] if scoped else None,
                guards={installation["id"]: revision},
            )
        return {
            "result": result,
            "transaction": committed,
            "package": package,
            "revision": revision,
        }

    def shell(self):
        installation = self.installation("agora.shell")
        if installation["revision"] == 0:
            raise Refusal("The shell has not been installed; use host recovery to restore it.")
        receipt = self.receipt(installation["facets"]["agora.installation"]["build"])
        return retained_html(receipt), installation["revision"]

    def browser_html(self, build):
        return retained_html(self.receipt(build))
