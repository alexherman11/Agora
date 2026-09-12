"""Durable task commitments, scoped candidates, messages and explicit adoption.
Never treat a worker report as authority or confuse a saved result with installation.
"""

import copy
import hashlib
import json
import time
import uuid

from agora3.work_specs import SPECS
from agora3.world import Refusal, identifier

FACET = "agora.work"
ATTEMPT = "agora.work-attempt"
ACTIVE = {"starting", "running", "waiting_resource"}
TERMINAL = {"ready", "adopted", "failed", "blocked", "interrupted", "cancelled"}


class WorkRecords:
    def __init__(self, gateway):
        self.gateway = gateway
        self.actor = gateway.principal("jeff", agent_id="work-manager")
        self.directory = gateway.world.directory / "work"
        self.directory.mkdir(exist_ok=True)
        gateway.work = self

    def read(self, task_id):
        identifier(task_id)
        obj = self.gateway.world.get(task_id)
        if FACET not in obj["facets"]:
            raise Refusal("This object is not a worker task.")
        return obj, copy.deepcopy(obj["facets"][FACET])

    def tasks(self):
        return [
            copy.deepcopy(o["facets"][FACET])
            for o in self.gateway.world.query([FACET], limit=1000)["items"]
        ]

    def save(self, obj, task, actor=None):
        task["updated_at"] = time.time()
        self.gateway.commit(
            actor or self.actor,
            [
                {
                    "id": task["id"],
                    "expected_revision": obj["revision"] if obj else 0,
                    "facets": {FACET: task},
                }
            ],
            internal=True,
        )

    def update(self, task_id, change, actor=None):
        with self.gateway.lock:
            obj, task = self.read(task_id)
            change(task)
            self.save(obj, task, actor)
            return task

    def assert_attempt(self, task_id, attempt):
        self.gateway.check_authority(self.actor)
        _, task = self.read(task_id)
        if task.get("attempt") != attempt or task["state"] not in ACTIVE:
            raise Refusal("This worker attempt is no longer active; no new action was admitted.")
        return task

    def summary(self, task):
        keys = (
            "id",
            "title",
            "brief_revision",
            "state",
            "detail",
            "attempt",
            "resources",
            "depends_on",
            "collaborators",
            "updated_at",
            "progress",
            "output_prefix",
        )
        return {key: task.get(key) for key in keys}

    @staticmethod
    def current_messages(task):
        return [m for m in task["messages"] if m.get("brief_revision", 1) == task["brief_revision"]]

    def create(self, actor, args):
        with self.gateway.lock:
            if sum(t["state"] not in TERMINAL for t in self.tasks()) >= 24:
                raise Refusal("There are already 24 unfinished tasks; finish or cancel some first.")
            scope = {
                key: args["scope"].get(key, [])
                for key in ("read_objects", "write_objects", "read_packages", "write_packages")
            }
            for key, values in scope.items():
                for value in values:
                    identifier(value)
                    if key.endswith("objects") and value.startswith("agora."):
                        raise Refusal("Protected runtime objects cannot be granted as worker data.")
            dependencies = args.get("depends_on", [])
            collaborators = args.get("collaborators", [])
            for task_id in dependencies + collaborators:
                self.read(task_id)
            for resource in args.get("resources", []):
                identifier(resource)
            task_id = "agora.work." + uuid.uuid4().hex[:12]
            task = {
                "id": task_id,
                "title": args["title"],
                "brief": args["brief"],
                "brief_revision": 1,
                "scope": scope,
                "state": "queued",
                "detail": "Queued",
                "resources": sorted(set(args.get("resources", []))),
                "depends_on": dependencies,
                "collaborators": collaborators,
                "priority": args.get("priority", 1),
                "max_calls": args.get("max_calls", 40),
                "timeout_seconds": args.get("timeout_seconds", 600),
                "notify": args.get("notify", True),
                "created_at": time.time(),
                "attempt": None,
                "attempts": [],
                "progress": "",
                "messages": [],
                "updates": [],
                "result": None,
                "output_prefix": "work." + task_id.rsplit(".", 1)[1] + ".",
            }
            self.save(None, task, actor)
            for peer in collaborators:
                self.update(peer, lambda t: t["collaborators"].append(task_id), actor)
        self.poke()
        return self.summary(task)

    def dispatch(self, actor, name, args):
        self.gateway.check_authority(actor)
        if name == "work.create":
            return self.create(actor, args)
        if name == "work.list":
            return {"tasks": [self.summary(t) for t in self.tasks()], "scheduler": self.resources()}
        if name == "work.resources":
            return self.resources()
        if name == "work.link":
            left, right = args["left"], args["right"]
            with self.gateway.lock:
                self.read(left)
                self.read(right)
                for task_id, peer in ((left, right), (right, left)):
                    self.update(
                        task_id,
                        lambda t, p=peer: (
                            t["collaborators"].append(p) if p not in t["collaborators"] else None
                        ),
                        actor,
                    )
            return {"linked": [left, right]}
        obj, task = self.read(args["id"])
        if name == "work.inspect":
            attempts = [self.gateway.world.get(a)["facets"][ATTEMPT] for a in task["attempts"]]
            return {**task, "attempt_history": attempts}
        if name == "work.diff":
            return self.diff(task)
        if name == "work.message":
            return self.message(task["id"], args["text"], actor, sender=actor.name)
        if name == "work.adopt":
            return self.adopt(actor, task["id"], args["expected_brief_revision"])
        if name not in {"work.cancel", "work.retry", "work.revise"}:
            raise Refusal("Unknown work operation.")
        with self.gateway.lock:
            obj, task = self.read(task["id"])
            old_attempt = task["attempt"]
            if name == "work.retry":
                if task["state"] not in {"failed", "blocked", "interrupted", "cancelled"}:
                    raise Refusal(
                        "Only a failed, blocked, interrupted or cancelled task can retry."
                    )
                task.update(
                    state="queued", detail="Explicit retry queued", attempt=None, result=None
                )
            elif name == "work.revise":
                if task["brief_revision"] != args["expected_brief_revision"]:
                    raise Refusal("The task brief changed; inspect it before revising.")
                task["brief_revision"] += 1
                task.update(
                    brief=args["brief"],
                    state="queued",
                    detail="Revised brief queued",
                    attempt=None,
                    result=None,
                )
            else:
                task.update(
                    state="cancelled",
                    detail="Cancelled; prior candidate work is retained",
                    attempt=None,
                )
            if name in {"work.retry", "work.revise"}:
                task.pop("blocker", None)
                task["progress"] = ""
            self.save(obj, task, actor)
        self.stop_attempt(old_attempt)
        self.poke()
        return self.summary(task)

    def message(self, task_id, text, actor, sender, *, deliver=True):
        row = {
            "id": uuid.uuid4().hex,
            "sender": sender,
            "text": text,
            "created_at": time.time(),
            "delivery": "queued",
        }

        def append(task):
            if len(task["messages"]) >= 100:
                raise Refusal("Task message limit reached; start a bounded follow-up task.")
            row["brief_revision"] = task["brief_revision"]
            task["messages"].append(row)

        self.update(task_id, append, actor)
        if deliver:
            self.deliver(task_id)
        self.poke()
        _, task = self.read(task_id)
        return next(m for m in task["messages"] if m["id"] == row["id"])

    def public_update(self, task_id, text, kind="progress", actor=None):
        def change(task):
            task["progress"] = text[:1600]
            if kind == "blocked":
                task["blocker"] = text[:1600]
            if kind != "progress":
                task["updates"].append(
                    {
                        "id": uuid.uuid4().hex,
                        "kind": kind,
                        "brief_revision": task["brief_revision"],
                        "text": text[:6000],
                        "created_at": time.time(),
                        "delivered": False,
                    }
                )
                task["updates"] = task["updates"][-40:]

        self.update(task_id, change, actor)
        self.poke()

    def worker_command(self, task_id, attempt, name, args):
        if name == "work.wait_messages":
            deadline = time.monotonic() + args.get("timeout_seconds", 20)
            while True:
                task = self.assert_attempt(task_id, attempt)
                current = self.current_messages(task)
                messages = current[args.get("after_count", 0) :]
                if messages or time.monotonic() >= deadline:
                    return {"messages": messages, "count": len(current)}
                time.sleep(0.1)
        if name in {"work.report", "work.send"}:
            with self.gateway.lock:
                return self._worker_command(task_id, attempt, name, args)
        return self._worker_command(task_id, attempt, name, args)

    def _worker_command(self, task_id, attempt, name, args):
        task = self.assert_attempt(task_id, attempt)
        task["messages"] = self.current_messages(task)
        actor = self.gateway.principal("jeff", agent_id=attempt)
        if name == "work.self":
            return {
                key: task[key]
                for key in (
                    "id",
                    "title",
                    "brief",
                    "brief_revision",
                    "scope",
                    "resources",
                    "depends_on",
                    "collaborators",
                    "messages",
                    "output_prefix",
                )
            }
        if name == "work.report":
            self.public_update(task_id, args["text"], args.get("kind", "progress"), actor)
            return {"recorded": True}
        if name == "work.messages":
            return {"messages": task["messages"]}
        if name == "work.resources":
            return self.resources()
        if name == "work.send" and args["id"] == "jeff":
            self.public_update(task_id, args["text"], "question", actor)
            return {"recorded": True, "recipient": "jeff"}
        peer_id = args.get("id")
        if peer_id not in task["collaborators"] + task["depends_on"]:
            raise Refusal("This task is not a linked collaborator; ask JEFF to link it.")
        _, peer = self.read(peer_id)
        if name == "work.inspect":
            return {**self.summary(peer), "result": peer.get("result")}
        if name == "work.send":
            return self.message(peer_id, args["text"], actor, sender=task_id, deliver=False)
        raise Refusal("Unknown worker operation.")

    def diff(self, task):
        if not task.get("result"):
            raise Refusal("This task has no finished candidate yet.")
        path = self.directory / task["result"]["attempt"] / "result.json"
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != task["result"]["sha256"]:
            raise Refusal("The retained candidate result is not intact; do not adopt it.")
        data = json.loads(raw)
        return {
            "id": task["id"],
            "brief_revision": data["brief_revision"],
            "changes": data["changes"],
            "baseline": data["baseline"],
            "dependencies": data.get("dependencies", {}),
            "evidence": data["evidence"],
            "installed": False,
        }

    def adopt(self, actor, task_id, expected):
        with self.gateway.lock:
            obj, task = self.read(task_id)
            if task["state"] != "ready" or task["brief_revision"] != expected:
                raise Refusal("Only a ready result for the current brief can be adopted.")
            diff = self.diff(task)
            if diff["brief_revision"] != expected:
                raise Refusal("The result belongs to an earlier brief; it cannot be adopted.")
            for task_id, expected_dependency in diff["dependencies"].items():
                dependency = self.read(task_id)[1]
                actual = {
                    "brief_revision": dependency["brief_revision"],
                    "attempt": (dependency.get("result") or {}).get("attempt"),
                }
                if actual != expected_dependency or dependency["state"] not in {"ready", "adopted"}:
                    raise Refusal("A prerequisite task changed; revise this task before adopting.")
            changes = diff["changes"]
            if len(changes) > 199:
                raise Refusal("Candidate exceeds the 199-object adoption bound; split the task.")
            guards = {key: value["revision"] for key, value in diff["baseline"].items()}
            task.update(
                state="adopted",
                detail="Candidate changes adopted; package installation is separate",
                updated_at=time.time(),
            )
            result = self.gateway.commit(
                actor,
                changes
                + [{"id": task_id, "expected_revision": obj["revision"], "facets": {FACET: task}}],
                internal=True,
                guards=guards,
            )
            return {
                "adopted": True,
                "changes": len(changes),
                "transaction": result,
                "packages_to_build_install": [
                    c["id"].removeprefix("agora.package.")
                    for c in changes
                    if c["id"].startswith("agora.package.")
                ],
                "installed": False,
            }


def specs():
    return SPECS
