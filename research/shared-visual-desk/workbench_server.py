"""Loopback research workbench; persists through the experimental desk's verbs.

This is neither the native Agora gateway nor a general command/host-execution API.
"""

from __future__ import annotations

import argparse
import json
import os
import pickle
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from team_desk import HERE, fresh, session_lock

TAG = "visual-workbench"
ACTOR = "visual-editor"


class Conflict(Exception):
    pass


class InvalidDocument(Exception):
    pass


def validate_document(document):
    if not isinstance(document, dict) or not isinstance(document.get("state"), dict):
        raise InvalidDocument("A workbench document needs a state object.")
    if not isinstance(document.get("program"), dict):
        raise InvalidDocument("A workbench document needs a program object.")
    # The browser evaluator owns language validation. This endpoint stores source.
    try:
        text = json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False)
    except (ValueError, TypeError) as exc:
        raise InvalidDocument(str(exc)) from exc
    if len(text.encode("utf-8")) > 512_000:
        raise InvalidDocument("Document exceeds the prototype's 512 KB limit.")
    return text


class Store:
    def __init__(self, state_dir=None):
        self.state_dir = Path(state_dir) if state_dir else HERE / ".state"
        self.path = self.state_dir / "visual.pickle"

    def load(self):
        return pickle.loads(self.path.read_bytes()) if self.path.exists() else fresh()

    def record(self, desk):
        matches = [s for s in desk.world.subjects.values() if TAG in s.get("tags", [])]
        if len(matches) > 1:
            raise InvalidDocument("Multiple workbench subjects; resolve the ambiguity in the desk.")
        if not matches:
            return {"revision": None, "document": None, "appearance": None, "subject": None}
        subject = matches[0]
        try:
            document = json.loads(subject["text"])
            validate_document(document)
        except (ValueError, TypeError) as exc:
            raise InvalidDocument(
                "Saved desk source is invalid JSON; repair it through text commands."
            ) from exc
        return {
            "revision": f"{subject['id']}:{subject['rev']}",
            "document": document,
            "appearance": next(iter(desk.world.appearances_of(subject["id"])), None),
            "subject": subject["id"],
        }

    def read(self):
        with session_lock(self.state_dir / "visual.guard"):
            return self.record(self.load())

    def save(self, base_revision, document):
        text = validate_document(document)
        with session_lock(self.state_dir / "visual.guard"):
            desk = self.load()
            before = self.record(desk)
            if before["revision"] != base_revision:
                raise Conflict(
                    "Desk source changed. Your local draft is retained; "
                    "load the newer version before saving."
                )
            desk.world.me = ACTOR
            per = getattr(desk, "_per", {})
            desk.seen, desk.open, desk.last_event_seen = per.get(
                ACTOR, ({}, {desk.world.root}, len(desk.world.events))
            )
            if before["subject"]:
                target = before["subject"]
                self.dispatch(desk, "read", {"target": target})
                receipt = self.dispatch(
                    desk, "do", {"verb": "rewrite", "target": target, "args": {"text": text}}
                )
            else:
                self.dispatch(desk, "look", {"target": desk.world.root})
                receipt = self.dispatch(
                    desk,
                    "do",
                    {
                        "verb": "create",
                        "target": desk.world.root,
                        "args": {
                            "kind": "note",
                            "title": "Field Notes - executable workbench",
                            "tags": TAG,
                            "text": text,
                        },
                    },
                )
            per[ACTOR] = (desk.seen, desk.open, desk.last_event_seen)
            desk._per = per
            result = self.record(desk)
            result["receipt"] = receipt
            payload = pickle.dumps(desk)
            temporary = self.path.with_suffix(".tmp-" + str(os.getpid()))
            try:
                with temporary.open("wb") as handle:
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, self.path)
            finally:
                if temporary.exists():
                    temporary.unlink()
            return result

    @staticmethod
    def dispatch(desk, name, args):
        result = desk.dispatch(name, args)
        if result.get("error"):
            raise InvalidDocument(str(result["error"]))
        return result.get("text", "")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(HERE), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def reply(self, status, value):
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def local_request(self):
        port = self.server.server_address[1]
        hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if self.headers.get("Host") not in hosts:
            self.reply(403, {"error": "Local host required."})
            return False
        origin = self.headers.get("Origin")
        if origin and origin not in {"http://" + host for host in hosts}:
            self.reply(403, {"error": "Same-origin request required."})
            return False
        return True

    def do_GET(self):
        if not self.local_request():
            return
        path = urlsplit(self.path).path
        if path == "/api/workbench":
            try:
                self.reply(200, self.server.store.read())
            except InvalidDocument as exc:
                self.reply(422, {"error": str(exc)})
            return
        if path == "/":
            self.send_response(302)
            self.send_header("Location", "/editing/visual-workbench/index.html")
            self.end_headers()
            return
        resolved = Path(self.translate_path(path)).resolve()
        workbench = (HERE / "editing" / "visual-workbench").resolve()
        program = (HERE / "foundations" / "program.mjs").resolve()
        if (resolved != program and workbench not in resolved.parents) or resolved.suffix not in {
            ".html",
            ".css",
            ".js",
            ".mjs",
            ".json",
        }:
            self.reply(404, {"error": "Not a workbench asset."})
            return
        super().do_GET()

    def do_HEAD(self):
        self.reply(405, {"error": "Use GET."})

    def do_POST(self):
        if not self.local_request():
            return
        if urlsplit(self.path).path != "/api/workbench":
            self.reply(404, {"error": "Unknown endpoint."})
            return
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            self.reply(415, {"error": "JSON required."})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 512_000:
                raise InvalidDocument("Request size must be between 1 and 512000 bytes.")
            payload = json.loads(self.rfile.read(size))
            if not isinstance(payload, dict) or "baseRevision" not in payload:
                raise InvalidDocument("baseRevision is required (null for a new artifact).")
            result = self.server.store.save(payload["baseRevision"], payload.get("document"))
            self.reply(200, result)
        except Conflict as exc:
            self.reply(409, {"error": str(exc)})
        except (InvalidDocument, ValueError, TypeError) as exc:
            self.reply(422, {"error": str(exc)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8771)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    server.store = Store()
    print(
        f"Field Notes: http://127.0.0.1:{args.port}/editing/visual-workbench/index.html", flush=True
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
