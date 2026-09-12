"""Worker candidate worlds containing only their explicitly granted inputs.
Never expose a live-world token, host execution or an unchecked mutation path.
"""

import copy
from pathlib import Path

from agora3.gateway import Gateway
from agora3.schemas import validate
from agora3.work_specs import WORKER_SPECS
from agora3.world import Refusal

READ_PACKAGE = {"package.get", "package.read", "package.search"}
WRITE_PACKAGE = {"package.patch", "package.save", "package.build", "package.check"}
OPERATIONS = READ_PACKAGE | WRITE_PACKAGE | {"world.get", "world.query", "world.transact"}


class Candidate:
    def __init__(self, service, task, attempt, directory):
        self.service, self.task, self.attempt = service, task, attempt
        self.scope = copy.deepcopy(task["scope"])
        self.prefix = task["output_prefix"]
        self.read_ids = set(self.scope["read_objects"] + self.scope["write_objects"])
        self.write_ids = set(self.scope["write_objects"])
        self.read_packages = set(self.scope["read_packages"] + self.scope["write_packages"])
        self.write_packages = set(self.scope["write_packages"])
        self.baseline = {}
        self.dependencies = {}
        self.directory = Path(directory)
        self.gateway = Gateway(directory, guest=service.gateway.yard, yard=service.gateway.yard)
        self.actor = self.gateway.principal("jeff", agent_id=attempt)
        # Retain original revision numbers separately; the candidate's local history starts at 1.
        selected = {}
        live = service.gateway
        with live.lock:
            owned = live.world.query(after=self.prefix, limit=1000)
            if not owned["complete"] and owned["items"][-1]["id"].startswith(self.prefix):
                raise Refusal("Task-owned output exceeds the 1000-object candidate bound.")
            for obj in owned["items"]:
                if not obj["id"].startswith(self.prefix):
                    break
                self.baseline[obj["id"]] = {"revision": obj["revision"], "facets": obj["facets"]}
                selected[obj["id"]] = obj
            for task_id in task["depends_on"]:
                dependency = service.read(task_id)[1]
                self.dependencies[task_id] = {
                    "brief_revision": dependency["brief_revision"],
                    "attempt": (dependency.get("result") or {}).get("attempt"),
                }
            for obj_id in self.read_ids | {"agora.package." + p for p in self.read_packages}:
                try:
                    obj = live.world.get(obj_id)
                except Refusal:
                    self.baseline[obj_id] = {"revision": 0, "facets": {}}
                else:
                    self.baseline[obj_id] = {"revision": obj["revision"], "facets": obj["facets"]}
                    selected[obj_id] = obj
            # Validation schemas are data, not extra application content or execution authority.
            schemas = live.world.query(["agora.schema"], limit=1000)
            if not schemas["complete"]:
                raise Refusal("Too many validation schemas for a bounded worker candidate.")
            for obj in schemas["items"]:
                selected[obj["id"]] = obj
            for package in self.read_packages:
                installation = live.packages.installation(package)
                if installation["revision"]:
                    selected[installation["id"]] = installation
                    self.baseline[installation["id"]] = {
                        "revision": installation["revision"],
                        "facets": installation["facets"],
                    }
                    build_id = installation["facets"]["agora.installation"]["build"]
                    selected[build_id] = live.world.get(build_id)
        items = list(selected.values())
        for offset in range(0, len(items), 100):
            self.gateway.commit(
                self.actor,
                [
                    {"id": obj["id"], "expected_revision": 0, "facets": obj["facets"]}
                    for obj in items[offset : offset + 100]
                ],
                internal=True,
            )
        self.original = {obj["id"]: copy.deepcopy(obj["facets"]) for obj in items}
        self._commit = self.gateway.commit
        self.gateway.commit = self._checked_commit
        self.gateway.packages.commit = self._checked_commit
        self.gateway.packages.check_authority = self._authority

    def _authority(self, actor):
        self.service.assert_attempt(self.task["id"], self.attempt)
        self.gateway.check_authority(actor)

    def writable(self, obj_id):
        return (
            obj_id in self.write_ids
            or obj_id.startswith(self.prefix)
            or obj_id in {"agora.package." + p for p in self.write_packages}
        )

    def readable(self, obj_id):
        return (
            obj_id in self.read_ids
            or obj_id.startswith(self.prefix)
            or obj_id in {"agora.package." + p for p in self.read_packages}
        )

    def _checked_commit(self, actor, changes, **kwargs):
        with self.service.gateway.lock:
            self._authority(actor)
            for change in changes:
                obj_id = change.get("id", "")
                # These receipts are produced by trusted package operations, not world.transact.
                receipt = kwargs.get("internal") and obj_id.startswith(
                    ("agora.build.", "agora.check.")
                )
                if not self.writable(obj_id) and not receipt:
                    raise Refusal(
                        f"Worker cannot write {obj_id!r}; it is outside this task's scope."
                    )
            return self._commit(actor, changes, **kwargs)

    def describe(self):
        return [s for s in self.gateway.describe() if s["name"] in OPERATIONS] + WORKER_SPECS

    def dispatch(self, name, args):
        self._authority(self.actor)
        specs = {s["name"]: s for s in self.describe()}
        if name not in specs:
            raise Refusal(f"{name!r} is not granted to this worker. Ask JEFF for a separate task.")
        validate(specs[name]["input_schema"], args)
        if name.startswith("work."):
            return self.service.worker_command(self.task["id"], self.attempt, name, args)
        if name in READ_PACKAGE | WRITE_PACKAGE:
            allowed = self.write_packages if name in WRITE_PACKAGE else self.read_packages
            if args.get("id") not in allowed:
                raise Refusal("Package is outside this worker's granted scope.")
        if name == "world.get" and not self.readable(args.get("id", "")):
            raise Refusal("Object is outside this worker's granted read scope.")
        if name == "world.query":
            # Query only data readable by this worker; do not leak receipts or unrelated schemas.
            result = self.gateway.world.query(
                args.get("facets"),
                limit=1000,
                after=args.get("after", ""),
                reverse=args.get("reverse", False),
            )
            if not result["complete"]:
                raise Refusal("Candidate query exceeds its 1000-object bound; use a facet filter.")
            items = [obj for obj in result["items"] if self.readable(obj["id"])]
            limit = args.get("limit", 100)
            return {
                "items": items[:limit],
                "complete": len(items) <= limit,
                "watermark": result["watermark"],
                "next_after": items[limit - 1]["id"] if len(items) > limit else None,
                "scope_limited": True,
            }
        if name == "world.transact":
            for change in args["changes"]:
                if not self.writable(change["id"]) or change["id"].startswith("agora."):
                    raise Refusal("Object is outside this worker's granted write scope.")
        if name in {"package.build", "package.check"}:
            with self.service.resource(self.task["id"], self.attempt, "yard"):
                return self.gateway.dispatch(self.actor, name, args)
        return self.gateway.dispatch(self.actor, name, args)

    def changes(self):
        result = []
        snapshot = self.gateway.world.query(limit=1000)
        if not snapshot["complete"]:
            raise Refusal("Candidate exceeds its 1000-object result bound; split the task.")
        for obj in snapshot["items"]:
            obj_id, facets = obj["id"], obj["facets"]
            if not self.writable(obj_id) or facets == self.original.get(obj_id, {}):
                continue
            before = self.baseline.get(obj_id, {"revision": 0, "facets": {}})
            patch = copy.deepcopy(facets)
            patch.update({key: None for key in before["facets"] if key not in facets})
            result.append({"id": obj_id, "expected_revision": before["revision"], "facets": patch})
        return result

    def evidence(self):
        return [
            obj
            for facet in ("agora.build", "agora.check")
            for obj in self.gateway.world.query([facet], limit=1000)["items"]
            if obj["id"] not in self.original
        ]
