"""fake_host.py (a8901): the home base's voice with the FAKE engine, for the sandbox film. No microphone, no sound.

    python research/window-lab/voice/fake_host.py <port> [--for <seconds>]

A page painted by screen.py has no home base, so a stub bridge (stub.js) stands in for window.pywebview.api.host and
posts here; this runs voice.Voice on voice.FakeEngine for the page's world (a screen.py copy), writing witnessed:voice
as the home base would and telling the page's door. POST /engine {session, do: hear|finish|done, text} makes the fake
engine hear words, finish an utterance, or end the voice. It answers only 127.0.0.1 and ends itself after --for.
"""
import json
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[1] / "text-desk-lab" / "notation"))
import voice  # noqa: E402
import witnessed  # noqa: E402

VOICES, LOG = {}, []


def of(session, door):
    if session not in VOICES:
        eng = voice.FakeEngine()

        def publish(rows):
            if witnessed.write(session, "voice", rows, by="fake-host", changed_only=True):
                try:
                    urllib.request.urlopen(urllib.request.Request(door + "/door/witnessed", data=b"{}", method="POST"),
                                           timeout=2).read()
                except OSError:
                    pass
        VOICES[session] = (voice.Voice(eng, publish=publish, jeff=lambda: "idle"), eng)
    return VOICES[session]


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def answer(self, text, code=200):
        b = text.encode("utf-8")
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        v, eng = of(body["session"], body.get("door") or "")
        LOG.append({"at": round(time.time(), 3), **{k: body.get(k) for k in ("verb", "words", "do", "text")}})
        try:
            if self.path == "/host":
                verb, words = body.get("verb"), str(body.get("words") or "")
                if verb == "voice.listen":
                    return self.answer("ok " + v.listen())
                if verb == "voice.stop":
                    return self.answer("ok " + v.stop("pressed"))
                if verb == "voice.hush":
                    return self.answer("ok " + v.hush())
                if verb == "voice.say":
                    sid, _, text = words.strip().partition(" ")
                    return self.answer("ok " + v.say(sid, text.strip().strip('"')))
                return self.answer(f"ERR no verb {verb}")
            if self.path == "/engine":
                {"hear": lambda: eng.hear(body["text"]), "finish": lambda: eng.finish(body["text"]),
                 "done": eng.done_speaking}[body["do"]]()
                return self.answer("ok")
        except voice.Refused as e:
            return self.answer(f"ERR {e}")
        self.answer("ERR not here", 404)

    def do_GET(self):
        if self.path == "/log":
            return self.answer(json.dumps({"log": LOG, "said": {s: [c for c in e.calls if c[0] == "say"]
                                                                for s, (_, e) in VOICES.items()}}))
        self.answer("ERR not here", 404)


if __name__ == "__main__":
    port = int(sys.argv[1])
    life = float(sys.argv[sys.argv.index("--for") + 1]) if "--for" in sys.argv else 600
    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    threading.Timer(life, srv.shutdown).start()
    print(f"fake host on 127.0.0.1:{port} for {life:.0f} s", flush=True)
    srv.serve_forever()
    for s in VOICES:
        witnessed.clear(s, "voice")
