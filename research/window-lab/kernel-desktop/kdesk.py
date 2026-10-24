"""kdesk: Alex's desktop on the new kernel. One process: the kernel (research/kernel-lab, unchanged), its
door on loopback 8810, and the modules the world says are on (the window host and the little guy).

    python kdesk.py [--world <dir>] [--port 8810]       run it (kdesk_on.py starts it detached; kdesk_off.py stops all)

The door is the kernel's own (kernel/door.py make_handler): /do, /see, /door/stream, the painter's routes that lens.js
speaks (/api/scene, /api/style, /api/do, /lens.html and the desk-shell files), and /dev/signin. One route is added:
    GET /desk/<file>     the desktop's own pages (pages/: the taskbar, the frame a lens window sits in, lines, help)

Signing in. There is no entry service on the desktop. A stand-in in this process plays its half of the seam (SHAPE 3):
it knows two sessions, Alex's (for the pages on his screen) and his agent's ("agent for Alex", label claude), kept in
<world>/keep/sessions.json beside the world, never in the log and never in git (state/ is ignored). The window host
opens each page through /dev/signin, which sets the session as an HttpOnly cookie, so no page script holds it.
"""
import argparse
import json
import mimetypes
import os
import secrets
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "kernel-lab"))
from kernel import door as KD  # noqa: E402
from kernel import modules as KM  # noqa: E402
from kernel.kernel import Kernel  # noqa: E402
from kernel import painter as KP  # noqa: E402
sys.path.insert(0, str(HERE))
import live  # noqa: E402

live.install(KP.Facade)            # widgets carry live readings when painted (live.py), never recorded

PAGES = HERE / "pages"
DEFAULT_WORLD = HERE / "state" / "world"
BASE_PY = Path(getattr(sys, "_base_executable", sys.executable))
STEWARD_ACCOUNT = "desktop:alex"

WINDOW_GRANTS = "window.* make set forget rows look hear:make hear:set hear:forget hear:undo hear:off"
GUY_GRANTS = "guy.* window.list window.overlay rows look hear:window.opened"
SYSTEM_GRANTS = "system.* rows look"
MEDIA_GRANTS = "media.* rows look"


def module_specs(headless=False):
    """The desktop's modules, as a genesis says them. The later ones (system, media: 24 Oct) are added to an older
    world once by after_genesis."""
    py = str(BASE_PY)            # the real interpreter, so the pid the kernel holds is the module's own (gotchas note)
    tail = ["--headless"] if headless else []
    return [
        {"name": "window", "run": [py, str(HERE / "kd_window.py")] + tail, "publishes": "window.*",
         "grants": WINDOW_GRANTS, "only": "kind:window", "for": "steward"},
        {"name": "guy", "run": [py, str(HERE / "kd_guy.py")] + tail, "publishes": "guy.*", "grants": GUY_GRANTS,
         "for": "steward"},
        {"name": "system", "run": [py, str(HERE / "kd_system.py")] + tail, "publishes": "system.*",
         "grants": SYSTEM_GRANTS, "for": "steward"},
        {"name": "media", "run": [py, str(HERE / "kd_media.py")] + tail, "publishes": "media.*",
         "grants": MEDIA_GRANTS, "for": "steward"},
    ]


def genesis(headless=False):
    """The first record of Alex's desktop world: the place, its steward, the kernel's words, and its modules.
    headless: the modules keep their windows in memory and read nothing from the machine (hidden tests)."""
    return {"tag": "dk", "name": "Alex's desktop", "steward": {"name": "Alex", "account": STEWARD_ACCOUNT},
            "modules": module_specs(headless)}


ABOUT = {"window": "the window host: it makes the Agora windows on this desktop match the window things in the world, "
                   "and says what is open (window.list)",
         "guy": "a little guy who walks on the Agora taskbar and hops onto windows; he holds window.overlay and sees "
                "window.list",
         "system": "what this machine is doing (CPU, memory, network, volume, battery, the window in front), for the "
                   "bars' widgets and system.now",
         "media": "the media words (media.play, media.next, media.prev, media.now) through Windows' media session"}


def after_genesis(k, headless=False):
    """What a genesis cannot say, written once as the kernel's own record: what each module is, in words. A world
    founded before the kernel took `only` and `for` (23 Oct, 19:36) also gets those here: the window grant narrowed to
    window things, and both modules installed for the steward."""
    from kernel.kernel import Tx
    with k.lock:
        todo = []
        steward = next((t for t in k.things("person") if k.is_steward(t)), None)
        have = {k.state.get(m, "name") for m in k.things("module")}
        new = [spec for spec in module_specs(headless) if spec["name"] not in have]
        for m in k.things("module"):
            if k.state.get(m, "name") in ABOUT and steward and not k.state.get(m, "for"):
                todo.append((m, "for", steward))
            name = k.state.get(m, "name")
            if name == "window":
                for g in k.things("grant"):
                    if k.state.get(g, "to") == m and not k.state.get(g, "only"):
                        todo.append((g, "only", "kind:window"))
            if ABOUT.get(name) and not k.state.get(m, "about"):
                todo.append((m, "about", ABOUT[name]))
        if not todo and not new:
            return
        tx = Tx(k)
        tx.part("install", None, "install")
        for t, a, v in todo:
            tx.set(t, a, v)
        for spec in new:                     # a module this desktop gained after the world was founded, as genesis says it
            mid = tx.mint()
            for a, v in (("kind", "module"), ("name", spec["name"]), ("run", spec["run"]),
                         ("publishes", spec["publishes"]), ("on", True), ("for", steward),
                         ("about", ABOUT.get(spec["name"], ""))):
                tx.set(mid, a, v)
            g = tx.mint()
            for a, v in (("kind", "grant"), ("to", mid), ("words", spec["grants"]), ("where", k.place), ("by", steward)):
                tx.set(g, a, v)
        k._commit(tx, by="kernel", words="install: what each module is, whose, and the window grant's narrowing")


class LocalEntry:
    """The entry service's half of the seam, in process: token -> {account, method, agent?}."""

    def __init__(self, keep):
        self.path = Path(keep) / "sessions.json"
        self.sessions = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}
        changed = False
        for who, agent in (("alex", None), ("claude", "claude")):
            if not any(v.get("signer") == who for v in self.sessions.values()):
                self.sessions[secrets.token_urlsafe(24)] = {"account": STEWARD_ACCOUNT, "method": "desktop",
                                                            "signer": who, **({"agent": agent} if agent else {})}
                changed = True
        if changed:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.sessions, indent=1), encoding="utf-8")
            os.replace(tmp, self.path)

    def check(self, token):
        s = self.sessions.get(token)
        return {"account": s["account"], "method": s["method"], "agent": s.get("agent")} if s else None

    def token(self, signer):
        return next(t for t, v in self.sessions.items() if v.get("signer") == signer)


def make_desk_handler(kernel, entry):
    Base = KD.make_handler(kernel, entry, "")

    class Handler(Base):
        def do_GET(self):
            path = urlsplit(self.path).path
            if path.startswith("/desk/"):
                return self._file(path[6:])
            if path == '/lens.html':
                # Desktop hosts use local system type. Keep the shared painter
                # unchanged, but do not let its optional Google font hit the network.
                content, ctype = KP.static_file(path)
                content = re.sub(rb'<link[^>]+href="https://fonts\.googleapis\.com/[^>]+>', b'', content)
                content = content.replace(b'<head>', b'<head><script src="/desk/stream.js"></script>', 1)
                return self._raw(200, content, ctype)
            return super().do_GET()

        def _file(self, rel):
            p = (PAGES / rel).resolve()
            if PAGES.resolve() not in p.parents or not p.is_file():
                return self._send(404, {"error": "no such page"})
            ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
            if ctype.startswith("text/") or ctype.endswith("javascript"):
                ctype += "; charset=utf-8"
            content = p.read_bytes()
            if p.suffix == '.html':
                content = content.replace(b'<head>', b'<head><script src="/desk/stream.js"></script>', 1)
            self._raw(200, content, ctype)

    return Handler


def start(world=DEFAULT_WORLD, port=8810, modules=True, headless=False):
    """-> (kernel, server, host, entry). Serves on a thread; the caller decides how long it lives."""
    import threading
    world = Path(world)
    k = Kernel(world, None if (world / "log" / "0001.jsonl").exists() else genesis(headless))
    after_genesis(k, headless)
    entry = LocalEntry(k.keep_dir)
    k.dev_sessions = lambda: entry.sessions             # the door's /dev/signin knows these sessions
    srv = KD.Server(("127.0.0.1", port), make_desk_handler(k, entry))
    os.environ["AGORA_KDESK_PORT"] = str(srv.server_address[1])     # the modules (children) read where the door is
    host = KM.Host(k, HERE)
    threading.Thread(target=srv.serve_forever, daemon=True, name="door").start()
    if modules:
        host.reconcile()
    return k, srv, host, entry


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", default=str(DEFAULT_WORLD))
    ap.add_argument("--port", type=int, default=8810)
    ap.add_argument("--no-modules", action="store_true")
    ap.add_argument("--log", help="write what it says here (it runs under pythonw, with no console)")
    a = ap.parse_args()
    if a.log:
        Path(a.log).parent.mkdir(parents=True, exist_ok=True)
        sys.stdout = sys.stderr = open(a.log, "a", encoding="utf-8", buffering=1)
    k, srv, host, entry = start(a.world, a.port, modules=not a.no_modules)
    (k.keep_dir / "kdesk.pid").write_text(str(os.getpid()))
    print(f"kdesk: {k.name(k.place)} on http://127.0.0.1:{a.port} · {len(k.log.records)} records · modules "
          f"{', '.join(k.state.get(m, 'name') for m in k.things('module') if k.state.get(m, 'on'))}", flush=True)
    try:
        while True:
            time.sleep(2)
            host.reconcile()                        # a module that died is started again (after the kernel's rest)
    except KeyboardInterrupt:
        pass
    finally:
        host.stop_all()
        srv.shutdown()


if __name__ == "__main__":
    main()
