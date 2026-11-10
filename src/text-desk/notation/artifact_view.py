"""artifact_view: a resident's own turn asks the house to show one guarded test screenshot to another resident (a8191).

The one typed host-route action besides the review harness's. A resident (JEFF, Rowan, Pike: no host shell) writes, in
its reply, one line

    > host-route {"action": "artifact-view", "request": "<its id>", "artifact": "<RUN>/<SHOT>.png",
                  "sha256": "<the PNG's 64 hex>", "recipient": "<a resident>", "target": "a<note or card>",
                  "prompt": "<what to look at>"}

and the house, which reads that line from the resident's own process (host_route_parent: the parent-bound child, never
a world prop, an actor string or a queue entry), answers it with one receipt in the resident's next message:
delivered (one addressed image comment, signed as the issuer, the recipient's next turn carries the pixels), refused
(why; nothing sent) or unknown (the door did not answer; repeat the same request id to settle it).

What may be shown is guarded_artifacts.prepare's alone (a7940): a named combined-review RUN/SHOT listed once in a passed
journey of a report with a successful hidden-desktop Guard receipt, the exact PNG SHA256, one static PNG within the
transport limit, a recipient whose model takes images. Nothing here widens it: no paths, URLs, captures, other roots.

Who: the issuer is a resident the house serves, read from its current bound child; a builder's card session is refused.
It is signed as that resident's own actor, as its > lines are. The recipient must be a resident the house serves.

Once: each (issuer corner, request) is kept in house-state/artifact-views/ with its outcome. The same request again
returns the kept outcome; the same id with other words is refused. The send carries a gesture id made from it, so the
door itself refuses a second comment even if the house died between sending and keeping (then: unknown, and the next
repeat asks the door, which answers 'already done' or does it now). Nothing is retried on its own.
Through the door only (DESKD): with no door nothing is sent.
"""
import hashlib
import json
import os
import re
from pathlib import Path
from urllib.parse import urlencode

import guarded_artifacts

KEYS = {"action", "request", "artifact", "sha256", "recipient", "target", "prompt"}
REQUEST = re.compile(r"[A-Za-z0-9_-]{1,40}")
NAME = guarded_artifacts.NAME
LIMIT = 64 * 1024 * 1024


class Refused(Exception):
    pass


def door_post(path, body=None, *, door=None):
    """The local desk door, and nothing else: no proxy, no redirect, bounded answer."""
    from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
    door = door or os.environ.get("DESKD", "")
    if door not in ("http://127.0.0.1:8780", "http://127.0.0.1:8794"):
        raise Refused("no local desk door (DESKD); nothing sent")

    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, *a, **kw):
            raise Refused("the desk door redirected; nothing sent")

    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = Request(door + path, data=data, headers={"Content-Type": "application/json"})
    with build_opener(ProxyHandler({}), NoRedirect()).open(req, timeout=30) as reply:
        raw = reply.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise Refused("desk answer exceeds limit")
    return json.loads(raw)


class ArtifactView:
    def __init__(self, house, route, *, door=door_post, root=None, store=None):
        self.house, self.route, self.door = house, route, door
        self.root = root or guarded_artifacts.DEMO_ROOT
        self.store = Path(store) if store else Path(house.dir) / "artifact-views"

    # ---- who ------------------------------------------------------------------------------------------------
    def _actor(self, corners, rid):
        actor = ((corners.get(rid) or {}).get("props") or {}).get("actor")
        return actor if isinstance(actor, str) and NAME.fullmatch(actor) else None

    def issuer(self, source):
        """(rid, actor) of the resident whose current bound child wrote the line, or Refused."""
        owner = getattr(source, "owner", None)
        if source is None or not self.route.current(owner, source):
            raise Refused("not from a current resident turn")
        if getattr(source, "card", None) is not None or getattr(owner, "cid", None) is not None:
            raise Refused("a builder's card session cannot ask for an artifact view")
        residents = getattr(self.house, "residents", {}) or {}
        if residents.get(getattr(owner, "rid", None)) is not owner:
            raise Refused("not a resident this house serves")
        corners = self.house.corners(self.house.load())
        actor = self._actor(corners, owner.rid)
        if not actor:
            raise Refused("this resident has no name to sign with; nothing sent")
        # signed as its > lines are (its corner's actor); a name two corners claim is no one's
        if [rid for rid in corners if self._actor(corners, rid) == actor] != [owner.rid]:
            raise Refused("another corner claims this resident's name; nothing sent")
        return owner.rid, actor

    def recipient(self, name):
        corners = self.house.corners(self.house.load())
        served = [rid for rid in (getattr(self.house, "residents", {}) or {}) if self._actor(corners, rid) == name]
        if len(served) != 1:
            raise Refused("recipient must be exactly one resident this house serves")
        return served[0]

    # ---- once -----------------------------------------------------------------------------------------------
    def _path(self, rid, request):
        return self.store / (hashlib.sha256(f"{rid}\n{request}".encode()).hexdigest()[:32] + ".json")

    def _keep(self, path, record):
        self.store.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, path)

    # ---- the action -----------------------------------------------------------------------------------------
    def handle(self, source, payload):
        try:
            return self._handle(source, payload)
        except Refused as e:
            return {"status": "refused", "reason": str(e)}
        except Exception as e:      # never into the turn's reader; and never said as done
            return {"status": "unknown", "reason": f"{type(e).__name__} in the house; not retried. Repeat this same "
                                                   "request to settle it"}

    def _handle(self, source, payload):
        if set(payload) != KEYS or not all(isinstance(payload[k], str) for k in KEYS):
            raise Refused("exact fields: " + ", ".join(sorted(KEYS)) + " (all strings)")
        if not REQUEST.fullmatch(payload["request"]):
            raise Refused("request: 1..40 letters, digits, - or _")
        rid, actor = self.issuer(source)
        words = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        path = self._path(rid, payload["request"])
        kept = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        if kept and kept.get("words") != words:
            return {"status": "refused", "request": payload["request"],
                    "reason": "this request id was used for another request; choose a new id"}
        if kept and kept.get("status") in ("delivered", "refused"):
            return {**kept["result"], "repeat": True}
        gesture = "artifact-view-" + hashlib.sha256(f"{rid}\n{payload['request']}".encode()).hexdigest()[:40]
        base = {"request": payload["request"], "artifact": payload["artifact"], "sha256": payload["sha256"],
                "recipient": payload["recipient"], "target": payload["target"], "issuer": actor}
        record = {"words": words, "rid": rid, "gesture": gesture, **base}
        try:
            self.recipient(payload["recipient"])
        except Refused as e:
            result = {"status": "refused", **base, "reason": str(e)}
            self._keep(path, {**record, "status": "refused", "result": result})
            return result
        try:
            snapshot = self.door("/api/snapshot?" + urlencode({"session": self.house.world, "as": actor}))
        except Exception as e:      # no door, or it did not answer: nothing was sent. Not kept: ask again when it answers
            return {"status": "refused", **base, "reason": f"desk snapshot unavailable ({e if isinstance(e, Refused) else type(e).__name__}); nothing sent"}
        try:
            prepared = guarded_artifacts.prepare(
                snapshot, artifact=payload["artifact"], sha256=payload["sha256"], recipient=payload["recipient"],
                target=payload["target"], prompt=payload["prompt"], root=self.root)
        except guarded_artifacts.Refusal as e:
            result = {"status": "refused", **base, "reason": str(e)}
            self._keep(path, {**record, "status": "refused", "result": result})
            return result
        p = prepared["provenance"]
        base.update(report_sha256=p["report_sha256"], journey=p["journey"], dimensions=p["dimensions"])
        self._keep(path, {**record, "status": "sending", "result": None})
        try:
            said = self.door("/api/do", {"session": self.house.world, "as": actor, "whole": True,
                                         "line": prepared["line"], "image_context": prepared["image_context"],
                                         "observed": prepared["observed"], "gesture": gesture})
        except Exception as e:
            result = {"status": "unknown", **base,
                      "reason": f"the desk door did not answer ({type(e).__name__}); not retried. Repeat this same "
                                "request to settle it: the door refuses a second comment for it"}
            self._keep(path, {**record, "status": "unknown", "result": result})
            return result
        text = str(said.get("text") or "")
        if said.get("error"):
            result = {"status": "refused", **base, "reason": "the desk refused: " + text.strip()[:300]}
        else:
            comment = re.search(r"created (c\d+)", text)
            result = {"status": "delivered", **base, "comment": comment.group(1) if comment else None,
                      "events": said.get("events") or said.get("already") or [],
                      **({"already": True} if said.get("already") else {})}
        self._keep(path, {**record, "status": result["status"], "result": result})
        return result
