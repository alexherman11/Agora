"""Authenticated native operations and the broad local development delegation.
Never accept caller-supplied identity or let native content change protected authority.
"""

import json
import os
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from agora3.application_specs import specs as application_specs
from agora3.applications import Applications
from agora3.check_tools import SPEC as CHECK_SPEC
from agora3.check_tools import check_package
from agora3.focus import SPEC as FOCUS_SPEC
from agora3.focus import read as focus_read
from agora3.guest import Guest
from agora3.locking import ProcessLock
from agora3.package_catalog import SPEC as CATALOG_SPEC
from agora3.package_catalog import catalog
from agora3.packages import Packages
from agora3.schemas import BUILTINS, check_schema, record, validate, validate_facets
from agora3.scoped_context import assert_reads
from agora3.source_tools import dispatch_source, source_specs
from agora3.world import Refusal, World, encoded, identifier
from agora3.yard import Yard


@dataclass(frozen=True)
class Principal:
    name: str
    generation: int
    agent_id: str | None = None


class Gateway:
    def __init__(self, directory, guest=None, yard=None):
        self.world = World(directory)
        self.lock = ProcessLock(Path(directory) / ".authority.lock")
        self.keep_path = Path(directory) / "keep.json"
        with self.lock:
            if not self.keep_path.exists():
                self._save_keep(
                    {
                        "generation": 1,
                        "enabled": True,
                        "operator": secrets.token_urlsafe(32),
                        "guest": secrets.token_urlsafe(32),
                    }
                )
        self.guest = guest or Guest(Path(directory) / "machine.json")
        self.yard = yard or Yard(Path(directory) / "yard.json", self.guest)
        self.packages = Packages(
            self.world, self.guest, self.yard, self.commit, self.check_authority
        )
        self.applications = Applications(self)

    @property
    def keep(self):
        """Read current durable authority; another service may have revoked it."""
        with self.lock:
            return json.loads(self.keep_path.read_text(encoding="utf-8"))

    def _save_keep(self, keep):
        pending = self.keep_path.with_suffix(".pending")
        with pending.open("w", encoding="utf-8") as handle:
            handle.write(encoded(keep))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(pending, self.keep_path)

    def principal(self, name, *, agent_id=None):
        return Principal(name, self.keep["generation"], agent_id)

    def authenticate(self, token, *, operator=False, name="guest"):
        """Bind a verified current token to the same authority generation.

        Operator authentication stays available during a development pause so the
        independent host recovery endpoint can resume or stop the guest machine.
        Ordinary operations still call check_authority before acting.
        """
        with self.lock:
            keep = self.keep
            expected = keep["operator" if operator else "guest"]
            if not isinstance(token, str) or not secrets.compare_digest(token, expected):
                raise Refusal("A current authenticated host session is required.")
            return Principal(name, keep["generation"])

    def check_authority(self, actor):
        if not isinstance(actor, Principal) or actor.name not in {
            "human",
            "jeff",
            "guest",
            "shell",
            "bootstrap",
        }:
            raise Refusal("Authenticated local development identity required.")
        if actor.agent_id is not None:
            if actor.name != "jeff":
                raise Refusal("Only a resident agent principal carries an agent identity.")
            identifier(actor.agent_id)
        keep = self.keep
        if actor.generation != keep["generation"] or not keep["enabled"]:
            raise Refusal(
                "Development delegation has been stopped or replaced. Use host recovery to resume."
            )

    def revoke(self):
        with self.lock:
            keep = self.keep
            keep["generation"] += 1
            keep["enabled"] = False
            keep["guest"] = secrets.token_urlsafe(32)
            self._save_keep(keep)
        return {"enabled": False, "generation": keep["generation"]}

    def resume(self):
        with self.lock:
            keep = self.keep
            keep["enabled"] = True
            self._save_keep(keep)
        return {"enabled": True, "generation": keep["generation"]}

    def commit(
        self,
        actor,
        changes,
        *,
        internal=False,
        guards=None,
        watermark=None,
        read_guards=None,
        via=None,
    ):
        with self.lock:
            self.check_authority(actor)

            def validator(obj_id, old, patch, db):
                if not (internal and obj_id.startswith("agora.")):
                    validate_facets(obj_id, old, patch, db)

            attribution = actor.name + (":" + actor.agent_id if actor.agent_id else "")
            if via is not None:
                attribution += ":" + identifier(via)
            if read_guards is not None:
                assert_reads(self.world, read_guards)
            return self.world.commit(
                attribution, changes, validator, guards=guards, watermark=watermark
            )

    def define_schema(self, actor, *, type, schema, expected_revision=0):
        identifier(type)
        if type.startswith(("core.", "agora.")):
            raise Refusal(
                "Application schemas need an application namespace, such as alex.benchmark."
            )
        check_schema(schema)
        with self.lock:
            self.check_authority(actor)
            existing = self.world.query([type], 1000)
            if not existing["complete"]:
                raise Refusal(
                    "Schema evolution requires a bounded migration; more than 1000 instances exist."
                )
            for obj in existing["items"]:
                validate(schema, obj["facets"][type])
            return self.commit(
                actor,
                [
                    {
                        "id": "agora.schema." + type,
                        "expected_revision": expected_revision,
                        "facets": {
                            "agora.schema": {
                                "type": type,
                                "schema": schema,
                                "merge": "register",
                                "projection": "generic",
                            }
                        },
                    }
                ],
                internal=True,
                watermark=existing["watermark"],
            )

    def dispatch(self, actor, name, args):
        self.check_authority(actor)
        if not isinstance(args, dict):
            raise Refusal("Tool arguments must be a JSON object.")
        spec = next((s for s in self.describe() if s["name"] == name), None)
        if spec is None:
            raise Refusal("Unknown operation. Discover the current registry with tools.list.")
        validate(spec["input_schema"], args)
        if name.startswith("application."):
            return self.applications.dispatch(actor, name.split(".", 1)[1], args)
        if name == "world.get":
            return self.world.get(args["id"])
        if name == "world.query":
            return self.world.query(**args)
        if name == "world.transact":
            return self.commit(actor, args["changes"])
        if name == "world.focus":
            return focus_read(self, args)
        if name == "schema.define":
            return self.define_schema(actor, **args)
        if name == "schema.list":
            return {
                "builtins": BUILTINS,
                "applications": self.world.query(["agora.schema"], 1000)["items"],
            }
        if name == "tools.list":
            return {"operations": self.describe(), "actions": self.packages.tools()}
        if name == "skills.list":
            return self.packages.skills()
        if name == "package.list":
            return self.packages.list()
        if name == "package.catalog":
            return catalog(self)
        if name in {"package.read", "package.search", "package.patch"}:
            return dispatch_source(self, actor, name, args)
        if name == "package.check":
            return check_package(self, actor, **args)
        if name == "package.get":
            return self.packages.get(args["id"])
        if name in {"package.save", "package.build", "package.install"}:
            return getattr(self.packages, name.split(".")[1])(actor, **args)
        if name == "package.restore":
            return self.packages.install(actor, **args, restore=True)
        if name == "candidate.exercise":
            return self.packages.invoke(actor, **args, revision=0)
        if name == "action.invoke":
            return self.packages.invoke(actor, **args)
        if name == "guest.status":
            result = self.guest.status()
            result["yard"] = self.yard.status()
            bridge = getattr(self, "native_bridge", None)
            result["native_bridge"] = bridge.status() if bridge else {"connected": False}
            return result
        if name == "guest.execute":
            result = self.guest.execute(**args)
            self.check_authority(actor)
            return result
        raise Refusal("Operation is not implemented.")

    def describe(self):
        string, number = {"type": "string"}, {"type": "integer", "minimum": 0}
        obj = {"type": "object"}
        package = {"id": string, "expected_revision": number}
        action = {"package": string, "action": string, "args": obj}
        specs = [
            (
                "world.get",
                "Read an object's facets, revision and provenance by id.",
                {"id": string},
                None,
            ),
            (
                "world.query",
                "Read a coherent, paginated snapshot filtered by facet types. "
                "Ordered by id; reverse=true reads descending. Follow next_after "
                "with the same direction when incomplete.",
                {
                    "facets": {"type": "array", "items": string},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 1000},
                    "after": string,
                    "reverse": {"type": "boolean"},
                },
                [],
            ),
            (
                "world.transact",
                "Atomically patch facets with expected object revisions. 0 creates; "
                "null detaches. No direct runtime-record edits.",
                {
                    "changes": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 200,
                        "items": record({"id": string, "expected_revision": number, "facets": obj}),
                    }
                },
                None,
            ),
            (
                "schema.define",
                "Define an application's JSON facet schema; generic projection, "
                "register merge. Existing values must remain valid.",
                {"type": string, "schema": obj, "expected_revision": number},
                ["type", "schema"],
            ),
            ("schema.list", "Inspect built-in and application-defined facet schemas.", {}, None),
            (
                "tools.list",
                "Discover native operations and all installed package actions, even "
                "with views closed.",
                {},
                None,
            ),
            (
                "skills.list",
                "Read deliberately installed versioned skills; source data cannot grant authority.",
                {},
                None,
            ),
            (
                "package.list",
                "Full-source package listing. Prefer package.catalog for compact "
                "discovery and package.read/search for focused inspection.",
                {},
                None,
            ),
            (
                "package.get",
                "Read editable source files and manifest of a native package. Shell "
                "package id is agora.shell.",
                {"id": string},
                None,
            ),
            (
                "package.save",
                "Create/revise native package source. Manifest runtime python-1 or "
                "browser-1; actions map name to entry file.py:function, "
                "input_schema, description. UI accepts self-contained HTML or optional ordered "
                "ui.scripts [.js paths] and ui.styles [.css paths]; index HTML must contain "
                "exactly one <!-- agora:scripts --> / <!-- agora:styles --> marker for each "
                "nonempty list. Package-local classic scripts/styles are assembled at build, "
                "with exact bytes retained; no imports, bundler or transpiler. Skills map "
                "name to source path.",
                package
                | {"files": {"type": "object", "additionalProperties": string}, "manifest": obj},
                None,
            ),
            (
                "package.build",
                "Validate retained source, compile Python in Linux, retain an "
                "immutable build receipt. Does not install or prove UI interaction.",
                package,
                None,
            ),
            (
                "package.install",
                "Activate a build against its current source and base installation "
                "revision; actions immediately discoverable.",
                package | {"build": string},
                None,
            ),
            (
                "package.restore",
                "Restore an earlier retained build as a new installation revision, "
                "preserving current application data.",
                package | {"build": string},
                None,
            ),
            (
                "candidate.exercise",
                "Execute a built Python candidate in the separate resettable test "
                "VM, without live credentials. "
                "Validate proposed native writes against disposable native state; do "
                "not install or change live data.",
                action | {"candidate": string},
                None,
            ),
            (
                "action.invoke",
                "Run a pinned installed Python action in Linux. "
                "Function(arguments,context) sees context.objects and returns "
                "{result,changes?}; proposed writes commit atomically against the "
                "input snapshot. Optional action manifest reads selects coherent inputs: "
                "queries is an array of facet-name arrays (AND in each, union across queries), "
                "ids selects explicit native IDs including absence, arg_ids names argument fields "
                "containing one ID or a list. Empty reads means no native inputs. At most 1000 "
                "matching objects; overflow refuses, never truncates. Declared inputs validate "
                "object revisions and full query membership under the native writer lock; "
                "unrelated "
                "writes do not invalidate them. This is dependency tracking, not a sandbox for "
                "guest I/O or separate native calls. Without reads the whole-world guard remains. "
                "Use guest.execute for broader OS work.",
                action | {"revision": number},
                None,
            ),
            (
                "guest.status",
                "Observe the live VM, candidate yard and native bridge status.",
                {},
                None,
            ),
            (
                "guest.execute",
                "Run an arbitrary root shell command inside the dedicated Linux VM. "
                "Install software, inspect processes, create missing development "
                "tools. Never executes on the Windows host. Files/process effects "
                "are not native replay. When the native bridge is connected, guest Python "
                "can import agora_native and use agora_native.call(name,args) to read/write "
                "objects, revise packages or invoke installed tools.",
                {"command": string, "timeout": {"type": "integer", "minimum": 1, "maximum": 120}},
                ["command"],
            ),
        ]
        return (
            [
                {
                    "name": name,
                    "description": description,
                    "input_schema": record(properties, required)
                    if required != []
                    else {
                        "type": "object",
                        "properties": properties,
                        "additionalProperties": False,
                    },
                }
                for name, description, properties, required in specs
            ]
            + source_specs()
            + [FOCUS_SPEC, CATALOG_SPEC, CHECK_SPEC]
            + application_specs()
        )

    def seed(self):
        actor = self.principal("bootstrap")
        if self.packages.installation("agora.shell")["revision"]:
            return
        shell = (Path(__file__).parent / "builtin" / "shell" / "index.html").read_text(
            encoding="utf-8"
        )
        self.packages.save(
            actor,
            id="agora.shell",
            expected_revision=0,
            files={"index.html": shell},
            manifest={
                "name": "Agora Home",
                "description": "Your editable desk and conversation with JEFF.",
                "runtime": "browser-1",
                "ui": {"entry": "index.html", "mount": "shell"},
            },
        )
        built = self.packages.build(actor, id="agora.shell", expected_revision=1)
        self.packages.install(actor, id="agora.shell", build=built["build"], expected_revision=0)
        changes = []
        for i, (title, text) in enumerate(
            [
                (
                    "A computer you can change",
                    "Welcome to Agora. These notes, this desk, and the conversation "
                    "panel are native content. Ask JEFF to shape them with you.",
                ),
                (
                    "Start with something useful",
                    "Try: make these notes draggable. JEFF can edit the installed shell "
                    "package and build new tools inside Linux.",
                ),
            ]
        ):
            changes.append(
                {
                    "id": f"welcome-{i + 1}",
                    "expected_revision": 0,
                    "facets": {
                        "core.title": {"text": title},
                        "core.text": {"text": text},
                        "core.appearance": {
                            "x": 36 + i * 320,
                            "y": 40,
                            "width": 280,
                            "height": 220,
                            "scene": "desk",
                        },
                    },
                }
            )
        self.commit(actor, changes)

    def record_message(self, actor, role, text):
        stamp = datetime.now(UTC).isoformat()
        object_id = "message." + stamp.replace("+", "_") + "." + secrets.token_hex(4)
        return self.commit(
            actor,
            [
                {
                    "id": object_id,
                    "expected_revision": 0,
                    "facets": {"core.message": {"role": role, "text": text, "created_at": stamp}},
                }
            ],
        )
