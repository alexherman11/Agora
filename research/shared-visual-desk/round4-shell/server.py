"""Isolated round-four checkpoint server; no native Agora installation."""
import argparse
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from workbench_server import HERE, Handler, InvalidDocument, Store  # noqa: E402


class ShellHandler(Handler):
    def do_GET(self):
        if not self.local_request():
            return
        path = urlsplit(self.path).path
        if path == "/api/round4":
            try:
                self.reply(200, self.server.store.read())
            except InvalidDocument as exc:
                self.reply(422, {"error": str(exc)})
            return
        if path == "/":
            self.send_response(302)
            self.send_header("Location", "/round4-shell/index.html")
            self.end_headers()
            return
        resolved = Path(self.translate_path(path)).resolve()
        assets = (HERE / "round4-shell").resolve()
        evaluator = (HERE / "foundations/program.mjs").resolve()
        if (resolved != evaluator and assets not in resolved.parents) or resolved.suffix not in {
            ".html", ".css", ".js", ".mjs", ".json"
        }:
            self.reply(404, {"error": "Not a round-four asset."})
            return
        SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if urlsplit(self.path).path != "/api/round4":
            self.reply(404, {"error": "Unknown endpoint."})
            return
        self.path = "/api/workbench"
        super().do_POST()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8772)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), ShellHandler)
    server.store = Store(name="shell", tag="round4-shell", actor="shell-editor",
                         title="The Common - rules adaptation test")
    print(f"Round four: http://127.0.0.1:{args.port}/round4-shell/index.html", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
