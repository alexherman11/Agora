"""Ephemeral composition demo through Agora's unmodified compiler and painter.

No live world is loaded, no models run, no commands are accepted by the server.
The optional export contains only this synthetic fixture and source hashes.
"""

import argparse
import hashlib
import json
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LAB = ROOT / "research/text-desk-lab/notation"
sys.path.insert(0, str(LAB))

import explore  # noqa: E402
import scene  # noqa: E402
import style  # noqa: E402
from module_examples import coverage_document, registry  # noqa: E402

LENS = """root : column, role dashboard
  measure 140ch
  heading : text "Composition workshop", role hero
  subtitle : text "Measure overlaps. Draw the result. Wrap it twice.", role subtitle
  explanation : text "Two reusable capabilities compose through named child slots.", role body
  basis : text "Synthetic data; existing Agora renderer.", role meta
  examples : grid fill 32ch
    results : column
      of modules:@KNOWN@ as m
      each result
    retained : column
      of modules:@STALE@ as m
      each result
    missing : column
      of modules:@MISSING@ as m
      each result
  boundary : text "Read-only preview. No live world, model calls or action execution.", role meta
result : column, role card
  heading : text "$m.title", role section
  value : text "$m.summary", role metric
  picture : text "$m.picture", picture
  detail : text "$m.detail", role body
"""


def q(value):
    return (
        '"'
        + str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("$", "\\$")
        .replace("\n", "\\n")
        + '"'
    )


def build():
    desk = explore.fresh()
    desk._session = "module-preview-memory"

    def run(line):
        result = desk.dispatch("desk", dict(line=line, whole=True))
        if result.get("error") or result.get("text", "").startswith("ERR"):
            raise ValueError(result)
        return result.get("text", "")

    def note(title, text, tag=None, **props):
        run("look " + desk.world.root)
        result = run(f"do create {desk.world.root} kind=note title={q(title)} text={q(text)}")
        item = re.search(r"created (a\d+)", result)[1]
        if tag:
            run(f"do tag {item} add={tag}")
        for key, value in props.items():
            run("read " + item)
            run(f"do prop {item} {key}={q(value)}")
        return item

    plan = coverage_document(registry())

    def config(title, **extra):
        return dict(
            plan=plan,
            input=dict(
                title=title, unit="hours", intervals=[dict(start=0, end=5), dict(start=3, end=8)]
            ),
            **extra,
        )

    configs = dict(
        KNOWN=config("Workshop time"),
        STALE=config("Earlier observation", state="stale"),
        MISSING=config(
            "Calendar unavailable", source="missing-calendar-producer", into="intervals"
        ),
    )
    source = LENS
    for key, value in configs.items():
        item = note(value["input"]["title"], json.dumps(value))
        source = source.replace("@" + key + "@", item)
    stylesheet = (ROOT / "research/window-lab/data-dashboard/dashboard.style").read_text(
        encoding="utf-8"
    )
    note("module-demo-style", stylesheet, "style")
    note("module-workshop", source, "lens", style="module-demo-style")
    node, words = scene.scene_for(desk, "module-workshop")
    painted = dict(scene.painter_view(node), **{"def": node.get("def")})
    gen = hashlib.sha256(json.dumps(painted, sort_keys=True).encode()).hexdigest()
    return (
        dict(scene=painted, text=words, gen=gen, events_total=len(desk.world.events)),
        configs,
        stylesheet,
    )


def serve(port, export=None):
    answer, configs, stylesheet = build()
    if export:
        export.mkdir(parents=True, exist_ok=True)
        files = [
            LAB / p
            for p in (
                "capability_modules.py",
                "scene.py",
                "lens_ir.py",
                "desk-shell/lens.js",
                "desk-shell/lens.html",
            )
        ]
        (export / "module-proof.json").write_text(
            json.dumps(
                dict(
                    scene=answer,
                    configs=configs,
                    hashes={
                        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in files
                    },
                ),
                indent=2,
            ),
            encoding="utf-8",
        )

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, data, mime="application/json", code=200):
            payload = data.encode() if isinstance(data, str) else json.dumps(data).encode()
            self.send_response(code)
            self.send_header("Content-Type", mime)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            url = urlsplit(self.path)
            if url.path == "/api/scene":
                have = parse_qs(url.query).get("have")
                return self.reply(
                    dict(same=True, gen=answer["gen"]) if have == [answer["gen"]] else answer
                )
            if url.path == "/api/style":
                return self.reply(dict(looks=style.looks(stylesheet)))
            if url.path == "/api/version":
                return self.reply(dict(code="module-preview", painter="current", shape=1))
            if url.path in ("/", "/lens.html"):
                html = (LAB / "desk-shell/lens.html").read_text(encoding="utf-8")
                html = re.sub(r"<link[^>]*https://fonts[^>]*>", "", html)
                return self.reply(html, "text/html; charset=utf-8")
            target = (LAB / "desk-shell" / url.path.lstrip("/")).resolve()
            if (
                target.is_relative_to((LAB / "desk-shell").resolve())
                and target.suffix in (".js", ".css")
                and target.is_file()
            ):
                return self.reply(
                    target.read_text(encoding="utf-8"),
                    "text/javascript" if target.suffix == ".js" else "text/css",
                )
            return self.reply({}, code=404)

        def do_POST(self):
            self.rfile.read(min(int(self.headers.get("Content-Length", "0")), 200_000))
            return self.reply(
                {} if self.path == "/api/observe" else dict(error="Read-only preview")
            )

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(
        f"http://127.0.0.1:{server.server_port}/lens.html?lens=module-workshop&inspect=0",
        flush=True,
    )
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8897)
    parser.add_argument("--export", type=Path)
    args = parser.parse_args()
    serve(args.port, args.export)
