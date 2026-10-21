"""Parent pipe provenance and disabled host-intent interception.

No transport listener, settings flag, host API or private storage is created.
ReviewDispatcher connects the real dispatch seam to the old fake policy model
for tests/review only. It does NOT establish Windows isolation/private storage.
"""
from dataclasses import dataclass
import json
import uuid

from host_route_draft import Binding, Issuer, ReferenceModel, Refused


@dataclass(eq=False, frozen=True)
class ChildSession:
    owner: object
    process: object
    generation: str
    card: str | None


@dataclass(frozen=True)
class ChildEvent:
    source: ChildSession
    event: dict


class TurnText(str):
    """A completed turn; receipts are public results, never bearer secrets."""
    def __new__(cls, text, receipts=()):
        value = super().__new__(cls, text)
        value.host_receipts = tuple(receipts)
        return value


class ParentDispatcher:
    """Default house dispatcher: provenance active, host capability disabled. a8191: given the house, one typed action
    answers, artifact-view (artifact_view.py: a guarded test screenshot shown to a resident); every other refuses."""

    def __init__(self, house=None):
        self.sessions = {}
        self.artifact_view = None
        if house is not None:
            import artifact_view
            self.artifact_view = artifact_view.ArtifactView(house, self)

    def bind(self, owner, process):
        source = ChildSession(owner, process, uuid.uuid4().hex, getattr(owner, "cid", None))
        self.sessions[owner] = source
        return source

    def current(self, owner, source):
        return (isinstance(source, ChildSession) and source.owner is owner
                and self.sessions.get(owner) is source and owner.proc is source.process)

    def retire(self, owner):
        self.sessions.pop(owner, None)

    def handle(self, source, payload):
        if self.artifact_view is not None and payload.get("action") == "artifact-view":
            return self.artifact_view.handle(source, payload)
        return {"status": "refused", "reason": "host route disabled pending review"}

    def intercept(self, source, text):
        """Consume only reserved > host-route intents, before public Desk.

        One malformed/refused intent does not swallow adjacent Desk lines.
        Commands in arbitrary public /api/do are not routed to this method.
        """
        kept, receipts, quoted_ordinary = [], [], False
        for line in text.splitlines():
            if quoted_ordinary:
                kept.append(line)
                if line.count('"') % 2:
                    quoted_ordinary = False
                continue
            stripped = line.strip()
            # Match commands_in's marker/backtick/quoted-value conventions.
            # An example inside an ordinary multiline quoted value is data.
            if stripped.startswith("```"):
                kept.append(line)
                continue
            if len(stripped) > 1 and stripped.startswith("`") and stripped.endswith("`"):
                stripped = stripped[1:-1].strip()
            command = stripped[1:].strip().strip("`").strip() if stripped.startswith(">") else ""
            if command != "host-route" and not command.startswith("host-route "):
                kept.append(line)
                quoted_ordinary = bool(command and command.count('"') % 2)
                continue
            try:
                if len(command) > 1024:
                    raise ValueError("intent too long")
                payload = json.loads(command[len("host-route"):].strip())
                if not isinstance(payload, dict):
                    raise ValueError("intent must be an object")
                result = self.handle(source, payload)
            except (ValueError, TypeError, Refused):
                result = {"status": "refused", "reason": "invalid or unauthorised host intent"}
            receipts.append("~ host route: " + json.dumps(result, sort_keys=True))
        return TurnText("\n".join(kept), receipts)


class ReviewDispatcher(ParentDispatcher):
    """Review harness, not a deployable service.

    jeff MUST be a parent-owned resident object, never resolved from an actor
    string/world role. db/guards/inventory are fake test seams here. There is
    deliberately no house construction path for this class or enable setting.
    """

    def __init__(self, *, jeff, db, guards, inventory, clock):
        super().__init__()
        self.jeff = jeff
        self.clock = clock
        self.capabilities = {}
        self.policy = ReferenceModel(
            db, issuer_attestor=self.issuer, worker_attestor=self.worker,
            guards=guards, inventory=inventory, clock=clock)

    def issuer(self, source):
        if (isinstance(source, ChildSession) and source.owner is self.jeff
                and source.card is None and self.current(self.jeff, source)):
            return Issuer("jeff", source.generation)
        return None

    def worker(self, source):
        if (isinstance(source, ChildSession) and source.card
                and self.current(source.owner, source)):
            # Bind worker identity to the parent object, not owner.actor.
            return Binding(source.card, source.owner.rid, source.generation)
        return None

    def handle(self, source, payload):
        action = payload.get("action")
        if action in ("grant", "revoke"):
            if not self.issuer(source):
                raise Refused("only the pinned resident pipe can issue")
            if set(payload) != {"action", "card", "generation"}:
                raise Refused("exact typed grant fields required")
            targets = [s for s in self.sessions.values()
                       if s.card == payload["card"] and s.generation == payload["generation"]
                       and self.worker(s)]
            if len(targets) != 1:
                raise Refused("target session is not current")
            target = targets[0]
            key = (target.card, target.generation)
            old = self.capabilities.get(key)
            if action == "revoke":
                if old is None:
                    raise Refused("no grant to revoke")
                self.policy.revoke(source, old[0])
                return {"status": "revoked", "card": target.card}
            # Replacing a grant never leaves an earlier live handle behind.
            if old is not None:
                self.policy.revoke(source, old[0])
            handle = self.policy.issue(source, self.worker(target), expires=self.clock() + 120)
            self.capabilities[key] = (handle, source.generation)
            return {"status": "granted", "card": target.card,
                    "generation": target.generation}
        if action == "inventory":
            if set(payload) != {"action", "request"} or not self.worker(source):
                raise Refused("current worker pipe and exact request fields required")
            capability = self.capabilities.get((source.card, source.generation))
            issuer = self.sessions.get(self.jeff)
            if (not capability or not self.issuer(issuer)
                    or capability[1] != issuer.generation):
                raise Refused("grant issuer session is no longer current")
            return self.policy.request(source, capability[0], payload["request"])
        raise Refused("unknown typed operation")
