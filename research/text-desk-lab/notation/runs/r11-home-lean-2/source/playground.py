"""Text-desk playground: the real lab desk (lean variant) behind a tiny local web page.
Left: the desk drawn from the world's geometry. Right: the text REPL exactly as the model sees it.
Never edits lab sources; imports them from the lab directory.
"""

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

LAB = Path(r"C:\Projects\Agora\research\text-desk-lab\notation")
sys.path.insert(0, str(LAB))
from tasks import TASKS, assess, build  # noqa: E402

HERE = Path(__file__).resolve().parent
STATE = {"task": "review", "variant": "lean", "desk": None, "log": [], "last_changed": []}


def reset(task, variant):
    STATE.update(task=task, variant=variant, desk=build(task, variant), log=[], last_changed=[])


def revs(w):
    r = {k: v["rev"] for k, v in w.nodes.items()}
    r.update({k: v["rev"] for k, v in w.subjects.items()})
    return r


def snapshot():
    d = STATE["desk"]
    w = d.world
    nodes = []
    for nid, n in w.nodes.items():
        x, y, ww, hh = w.abs_rect(nid)
        e = {"id": nid, "type": n["type"], "parent": n["parent"], "z": n["z"], "rev": n["rev"],
             "rect": [x, y, ww, hh], "depth": w.depth(nid), "seen": d.seen.get(nid),
             "hidden": round(w.hidden_fraction(nid), 2) if n["parent"] else 0,
             "open": nid in d.open}
        if n["type"] == "surface":
            e.update(title=n["title"], layout=n["layout"])
        else:
            s = w.subjects[n["subject"]]
            e.update(title=s["title"], kind=s["kind"], subject=s["id"], folded=n["folded"],
                     comments=len(s["comments"]), open_comments=sum(1 for c in s["comments"] if not c["resolved"]),
                     links=len(w.links_of(s["id"])), due=s.get("due"))
        nodes.append(e)
    return {"task": STATE["task"], "variant": STATE["variant"], "prompt": TASKS[STATE["task"]], "root": w.root,
            "nodes": nodes, "subjects": w.subjects, "links": w.links,
            "events": w.events[-30:], "n_events": len(w.events), "seen": d.seen,
            "last_changed": STATE["last_changed"], "log": STATE["log"][-200:],
            "assessment": assess(STATE["task"], d), "tasks": list(TASKS)}


def run(line):
    d = STATE["desk"]
    before = revs(d.world)
    r = d.dispatch("desk", {"line": line})
    after = revs(d.world)
    STATE["last_changed"] = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    text = r.get("text") if "text" in r else "ERR " + str(r.get("error"))
    STATE["log"].append({"line": line, "text": text, "error": "error" in r})
    return text


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/state"):
            return self._json(snapshot())
        body = (HERE / "playground.html").read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(n) or b"{}")
        if self.path.startswith("/cmd"):
            text = run(str(data.get("line", "")))
            return self._json({"text": text, "state": snapshot()})
        if self.path.startswith("/reset"):
            reset(data.get("task", STATE["task"]), data.get("variant", STATE["variant"]))
            return self._json({"state": snapshot()})
        self._json({"error": "unknown"}, 404)


if __name__ == "__main__":
    reset("review", "lean")
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    print(f"playground on http://127.0.0.1:{port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
