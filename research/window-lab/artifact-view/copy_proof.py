"""a8191: artifact-view end to end on a disposable world copy with its own door (hud_playtest.Copy), never the live one.

JEFF's turn (the actual Resident reader, fake child process) carries one '> host-route' artifact-view line each for
Rowan and Pike; the dispatcher checks it, guarded_artifacts.prepare selects a real combined-review shot, and the copy's
deskd takes the addressed image comment. Then: both comments hold the same bytes (hash), a repeat makes no new comment,
the map-lab shot is refused, and the copy's event count moved by exactly two. No window, capture, model or live world.
    python research/window-lab/artifact-view/copy_proof.py
"""
import base64
import hashlib
import json
import queue
import sys
import tempfile
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parents[3] / "research" / "text-desk-lab" / "notation"))
import hud_playtest as pt  # noqa: E402
import house  # noqa: E402
from host_route_parent import ParentDispatcher  # noqa: E402

ARTIFACT = "2026-10-21-114241-1280x800-deployed/01-facts.png"
SHA = "eae62335b6f659242491fa5c8990cdb673b2a787d42e6e8370261f0ff19b6ca4"
TARGET = "a8191"
CORNERS = {"f5189": "jeff", "f1603": "rowan", "f576": "pike"}


class Pause(BaseException):
    pass


def main():
    copy = pt.Copy("frontier-try")
    try:
        def door(path, body=None):        # the copy's own door (a free port), the same request the house sends
            req = urllib.request.Request(copy.base + path, json.dumps(body).encode() if body is not None else None,
                                         {"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as f:
                return json.loads(f.read())
        snap = lambda: door(f"/api/snapshot?session={copy.session}&as=jeff")  # noqa: E731
        s0 = snap()
        corners = {k: v for k, v in s0["nodes"].items() if (v.get("props") or {}).get("role") == "resident"}
        tmp = tempfile.TemporaryDirectory()
        h = SimpleNamespace(dir=Path(tmp.name), world=copy.session, residents={}, load=lambda: None,
                            corners=lambda w: corners)
        route = ParentDispatcher(house=h)
        route.artifact_view.door = door
        h.host_route = route
        rs = {}
        for rid in CORNERS:
            r = object.__new__(house.Resident)
            r.house, r.rid, r.state, r.events = h, rid, {}, queue.Queue()
            r.reply, r.reply_source, r.busy = [], None, False
            r.log, r.save, r.send = Mock(), Mock(), Mock()
            r.proc = SimpleNamespace(stdout=(), wait=Mock(return_value=0), pid=1)
            r._bind_child(r.proc)
            h.residents[rid] = rs[rid] = r

        def turn(text):
            r = rs["f5189"]

            def stream():
                yield json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}) + "\n"
                yield json.dumps({"type": "result"}) + "\n"
                raise Pause()
            r.proc.stdout = stream()
            try:
                r._read(r.proc, route.sessions[r])
            except Pause:
                pass
            out = r.turns_ended()[0]
            return [json.loads(x.split(": ", 1)[1]) for x in out.host_receipts]

        def ask(request, recipient, artifact=ARTIFACT, sha=SHA):
            return "> host-route " + json.dumps({"action": "artifact-view", "request": request, "artifact": artifact,
                                                 "sha256": sha, "recipient": recipient, "target": TARGET,
                                                 "prompt": "Name three concrete things you can see in this picture."})

        copy.do(f"look {TARGET}", "jeff")
        n0 = len(door(f"/api/events?session={copy.session}&since=0")["events"])
        got = turn(ask("demo-rowan", "rowan") + "\n" + ask("demo-pike", "pike"))
        for g in got:
            print("receipt:", {k: g.get(k) for k in ("status", "recipient", "comment", "events", "reason")})
        again = turn(ask("demo-rowan", "rowan"))
        print("repeat:", {k: again[0].get(k) for k in ("status", "repeat", "comment")})
        for p in Path(tmp.name, "artifact-views").glob("*.json"):     # as if the house died after sending, before keeping
            p.unlink()
        lost = turn(ask("demo-rowan", "rowan"))
        print("record lost, asked again:", {k: lost[0].get(k) for k in ("status", "already", "events")})
        mapped = turn(ask("demo-map", "rowan", "research/map-lab/ground/shots/map-800x600.png",
                          "da3a435498f3f05c548392365c3d74d29378e74ddf94b36bfc2cf2deba6cf65b"))
        print("map-lab:", {k: mapped[0].get(k) for k in ("status", "reason")})
        n1 = len(door(f"/api/events?session={copy.session}&since=0")["events"])
        s1 = snap()
        sid = s1["nodes"][TARGET]["subject"]
        made = [c for c in s1["subjects"][sid].get("comments", []) if c["id"] in {g.get("comment") for g in got}]
        hashes = set()
        for c in made:
            img = c.get("image") or {}
            raw = base64.b64decode(str(img.get("data_url", "")).split(",", 1)[-1]) if img.get("data_url") else b""
            hashes.add(hashlib.sha256(raw).hexdigest() if raw else f"(image kept as {sorted(img)})")
            print(f"comment {c['id']} by {c.get('by')}: {str(c.get('text', ''))[:70]}... image keys {sorted(img)}")
        print("events added:", n1 - n0, "(expected 2)")
        print("same bytes in both:", hashes == {SHA}, hashes)
        ok = (all(g["status"] == "delivered" for g in got) and again[0].get("repeat") and mapped[0]["status"] == "refused"
              and lost[0].get("already")
              and n1 - n0 == 2 and len(made) == 2 and all(c.get("by") == "jeff" for c in made))
        print("PROOF", "PASS" if ok else "FAIL")
    finally:
        copy.close()


if __name__ == "__main__":
    main()
