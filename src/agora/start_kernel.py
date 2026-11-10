"""Start the kernel on a fixed loopback port, for the desktop and anyone else who depends on it.

    C:/Projects/Agora4/.venv/Scripts/python.exe src/agora/start_kernel.py ^
        --world <dir> --genesis <genesis.json> [--port 8810] [--entry http://127.0.0.1:8817] [--dev-entry 8811]

- `--world` is a folder of its own (keep it out of git: it holds the keep). An empty folder is founded from `--genesis`.
- In a genesis, a module's `run` words that name a file next to the genesis file are made absolute, so a module can
  live beside the genesis that installs it.
- `--entry` is the entry service (sign-in). With `--dev-entry PORT` instead, a loopback stand-in answers on PORT from
  `<world>/keep/dev-sessions.json`, `{"<token>": {"account": "<account id>", "agent": "<label>"?}}`, which you write
  yourself and never commit; `GET /dev/signin?token=<token>&next=/lens.html?...` then sets the session cookie for a
  page on this origin. The shared secret is KERNEL_SHARED_SECRET from the environment; with --dev-entry and none set,
  one is made for this run only.
- Nothing is drawn on the screen. Ctrl+C (or ending the process) stops it and every module it started.
"""
import argparse
import json
import os
import secrets
import sys
import threading
from http.server import BaseHTTPRequestHandler
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from kernel.door import Server, serve  # noqa: E402
from kernel.kernel import Kernel       # noqa: E402


def load_genesis(path):
    g = json.loads(Path(path).read_text(encoding="utf-8"))
    here = Path(path).resolve().parent
    for m in g.get("modules", []):
        m["run"] = [str((here / w).resolve()) if (here / w).is_file() else w for w in m.get("run", [])]
    return g


def dev_entry(world, port, secret):
    """A loopback stand-in for the entry service's /internal/session/check, reading tokens from the keep."""
    path = Path(world) / "keep" / "dev-sessions.json"

    def sessions():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
            if self.path != "/internal/session/check" or self.headers.get("X-Kernel-Secret") != secret:
                self.send_response(403)
                self.end_headers()
                return
            s = sessions().get(str(body.get("token")))
            ans = {"account": s["account"], "method": "dev", "agent": s.get("agent"),
                   "record": {"account_id": s["account"]}} if s else {"account": None, "method": None, "agent": None}
            data = json.dumps(ans).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    srv = Server(("127.0.0.1", port), H)               # refuses a port another program holds (door.Server)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return sessions


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--world", required=True)
    ap.add_argument("--genesis")
    ap.add_argument("--port", type=int, default=8810)
    ap.add_argument("--entry", default="http://127.0.0.1:8817")
    ap.add_argument("--dev-entry", type=int)
    a = ap.parse_args()
    secret = os.environ.get("KERNEL_SHARED_SECRET", "")
    if a.dev_entry and not secret:
        secret = secrets.token_hex(16)                   # this run only; never written anywhere
    k = Kernel(a.world, load_genesis(a.genesis) if a.genesis else None)
    entry = a.entry
    if a.dev_entry:
        k.dev_sessions = dev_entry(a.world, a.dev_entry, secret)
        entry = f"http://127.0.0.1:{a.dev_entry}"
    srv, host = serve(k, entry, secret, a.port, LAB)
    print(f"kernel on http://127.0.0.1:{a.port} · world {a.world} · {len(k.log.records)} records · "
          f"sign-in {'dev stand-in on ' + str(a.dev_entry) if a.dev_entry else entry}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        host.stop_all()


if __name__ == "__main__":
    main()
