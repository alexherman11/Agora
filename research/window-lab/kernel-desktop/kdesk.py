"""kdesk: Alex's desktop on the new kernel. One process: the kernel (research/kernel-lab, unchanged), its
door on loopback 8810, and the modules the world says are on (the window host and the little guy).

    python kdesk.py [--world <dir>] [--port 8810]       run it (kdesk_on.py starts it detached; kdesk_off.py stops all)

The door is the kernel's own (kernel/door.py make_handler): /do, /see, /door/stream, the painter's routes that lens.js
speaks (/api/scene, /api/style, /api/do, /lens.html and the desk-shell files), and /dev/signin. Desktop routes:
    GET /desk/<file>     the desktop's own pages (pages/: the taskbar, the frame a lens window sits in, lines, help)
    GET /desk/window-origin?win=<window>&next=<page>   owner-only redirect to a leased loopback listener

Signing in. There is no entry service on the desktop. A stand-in in this process plays its half of the seam (SHAPE 3):
it knows three sessions, Alex's (for the pages on his screen), his agent's ("agent for Alex", label claude) and JEFF's
(a person of his own since 27 Oct, account desktop:jeff, which the house runs him with), kept in
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
from urllib.parse import urlsplit, parse_qs
import threading

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "kernel-lab"))
from kernel import door as KD  # noqa: E402
from kernel import modules as KM  # noqa: E402
from kernel.kernel import Kernel  # noqa: E402
from kernel import painter as KP  # noqa: E402
sys.path.insert(0, str(HERE))
import live  # noqa: E402
from widgets import Widgets  # noqa: E402

live.install(KP.Facade)            # widgets carry live readings when painted (live.py), never recorded

PAGES = HERE / "pages"
DEFAULT_WORLD = HERE / "state" / "world"
BASE_PY = Path(getattr(sys, "_base_executable", sys.executable))
STEWARD_ACCOUNT = "desktop:alex"

WINDOW_GRANTS = "window.* make set forget rows look who hear:make hear:set hear:forget hear:undo hear:off"
GUY_GRANTS = "guy.* window.list window.overlay rows look holds hear:window.opened"
SYSTEM_GRANTS = "system.* rows look"
MEDIA_GRANTS = "media.* rows look"
SUMMARIZE_GRANTS = "summarize.* model.preview rows make set"
HOUSE_GRANTS = "house.* rows look chat hear:say hear:make hear:set hear:undo hear:task.*"
JEFF_ACCOUNT = "desktop:jeff"
THEME_GRANTS = "theme.* make set forget rows look file-read clock hear:set hear:make hear:forget hear:undo"


def module_specs(headless=False):
    """The desktop's modules, as a genesis says them. The later ones (system, media: 24 Oct) are added to an older
    world once by after_genesis."""
    py = str(BASE_PY)            # the real interpreter, so the pid the kernel holds is the module's own (gotchas note)
    tail = ["--headless"] if headless else []
    return [
        {"name": "summarize", "run": [str(HERE.parents[2] / '.venv/Scripts/python.exe'),
         str(HERE.parents[1] / 'kernel-lab/modules/summarize/summarize.py')],
         "publishes": "summarize.*", "grants": SUMMARIZE_GRANTS,
         "only": "kind:taskboard-task", "for": "steward"},
        {"name": "window", "run": [py, str(HERE / "kd_window.py")] + tail, "publishes": "window.*",
         "grants": WINDOW_GRANTS, "only": "kind:window", "for": "steward"},
        {"name": "guy", "run": [py, str(HERE / "kd_guy.py")] + tail, "publishes": "guy.*", "grants": GUY_GRANTS,
         "for": "steward"},
        {"name": "system", "run": [py, str(HERE / "kd_system.py")] + tail, "publishes": "system.*",
         "grants": SYSTEM_GRANTS, "for": "steward"},
        {"name": "media", "run": [py, str(HERE / "kd_media.py")] + tail, "publishes": "media.*",
         "grants": MEDIA_GRANTS, "for": "steward"},
        {"name": "house", "run": [py, str(HERE.parents[1] / "kernel-lab/modules/house/house.py")],
         "publishes": "house.*", "grants": HOUSE_GRANTS, "for": "steward"},
        {"name": "theme", "run": [py, str(HERE.parents[1] / "kernel-lab/theme/theme_module.py")],
         "publishes": "theme.*", "grants": THEME_GRANTS, "only": "kind:theme,theme-settings,theme-choice",
         "for": "steward"},
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
         "media": "the media words (media.play, media.next, media.prev, media.now) through Windows' media session",
         "summarize": "local task summaries with honest literal fallback; off summarize stops it",
         "house": "the house: runs the world's agents (JEFF first), wakes one only when someone addresses it (@name, "
                  "its closed chat such as the Conversation, a task given to it, house.wake); house.who says what each "
                  "is doing; off house ends every agent's process",
         "theme": "the themes: theme.use, theme.try, theme.import, theme.export; one look for every window, bar and widget "
                  "(research/kernel-lab/theme/THEMES.md); off theme stops the words, the look stays"}


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
            if name == 'guy':
                for g in k._grants_to(m):
                    words=k.state.get(g,'words') or ''
                    if 'holds' not in words.split():
                        todo.append((g,'words',words+' holds'))
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
            if spec.get('only'):
                tx.set(g, 'only', spec['only'])
        k._commit(tx, by="kernel", words="install: what each module is, whose, and the window grant's narrowing")


def moving_in(k):
    """JEFF moves in (MOVING-IN.md, build step 1, 27 Oct): a person of his own (his account is the local entry's,
    desktop:jeff), the team (an open group he leads), the Conversation (a chat only Alex and JEFF see), Shop talk (the
    team's open chat where agents coordinate) and his house-agent thing, which says how the house runs him. Written once, as the kernel's own record. He starts
    asleep (want=asleep); setting want=awake is moving him in for real."""
    from kernel.kernel import Tx
    with k.lock:
        steward = next((t for t in k.things("person") if k.is_steward(t)), None)
        jeff = k.accounts.get(JEFF_ACCOUNT)
    if jeff is None:
        jeff = k.join(JEFF_ACCOUNT, "JEFF", invite={"admitted": "steward", "channel": "moving in"})["person"]
    with k.lock:
        chats = {k.state.get(c, "name") for c in k.things("chat")}
        agents = {k.state.get(a, "person") for a in k.things("house-agent")}
        team = next((g for g in k.things("group") if k.state.get(g, "name") == "team"), None)
        shop = next((c for c in k.things("chat") if k.state.get(c, "name") == "Shop talk"), None)
        if "Conversation" in chats and shop and jeff in agents and team and k.state.get(shop, f"in:{team}"):
            return
        tx = Tx(k)
        tx.part("install", None, "install")
        n = len(k.log.records) + 1

        def thing(**facts):
            t = tx.mint()
            for a, v in facts.items():
                tx.set(t, a, v)
            tx.set(t, "made_by", steward)
            tx.set(t, f"in:{k.place}", n)
            return t
        if "Conversation" not in chats:
            thing(kind="chat", name="Conversation", **{"with": f"{steward} {jeff}"},
                  sees=f"person:{steward}|person:{jeff}",
                  about="Alex and JEFF talking. Only they see it; every line in it speaks to the other.")
        if team is None:
            # the team: JEFF leads it (the coordinator for Alex, 27 Oct: a leader of a group, not of the place, so
            # Alex stays the only steward); open, so the whole place sees what is in it
            team = tx.mint()
            for a, v in (("kind", "group"), ("name", "team"), ("open", True), (f"in:{k.place}", n),
                         (f"member:{jeff}", "leader"), ("made_by", steward)):
                tx.set(team, a, v)
        if shop is None:
            shop = thing(kind="chat", name="Shop talk", about="Where agents coordinate. @name reaches one person.")
        if not k.state.get(shop, f"in:{team}"):
            tx.set(shop, f"in:{team}", n)            # Shop talk is the team's
            tx.set(shop, f"in:{k.place}")
        if jeff not in agents:
            thing(kind="house-agent", name="JEFF", person=jeff, signer="jeff", provider="claude",
                  model="claude-opus-5-5", reasoning="medium", fallback_provider="codex", fallback_model="gpt-6-astra",
                  fallback_reasoning="medium", speaks="text", want="asleep")
        k._commit(tx, by="kernel", words="install: JEFF moves in: the Conversation, Shop talk, and how the house runs him")


class LocalEntry:
    """The entry service's half of the seam, in process: token -> {account, method, agent?}."""

    def __init__(self, keep):
        self.path = Path(keep) / "sessions.json"
        self.sessions = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}
        changed = False
        # Alex's pages, his agent ("agent for Alex": the builders' session), and JEFF, a person of his own (27 Oct)
        for who, account, agent in (("alex", STEWARD_ACCOUNT, None), ("claude", STEWARD_ACCOUNT, "claude"),
                                    ("jeff", JEFF_ACCOUNT, None)):
            if not any(v.get("signer") == who for v in self.sessions.values()):
                self.sessions[secrets.token_urlsafe(24)] = {"account": account, "method": "desktop",
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


class WindowOrigins:
    """One HTTP connection pool per native window, all serving the same kernel.

    Listeners are reused only after their window disappears; the number of
    listeners is the high-water mark of concurrently open windows, not all opens.
    Cookies are host scoped (ports do not isolate identity). No proxy rewrites
    Host or Origin: the kernel door checks the actual destination as before.
    """
    def __init__(self, kernel, handler):
        self.kernel, self.handler = kernel, handler
        self.lock = threading.Lock()
        self.leases = {}
        self.servers = []

    def origin(self, wid):
        with self.lock:
            with self.kernel.lock:
                active = {w for w in self.kernel.things('window')
                          if not self.kernel.state.get(w, 'forgotten')}
            if wid not in active:
                raise ValueError('no such window')
            self.leases = {w: s for w, s in self.leases.items() if w in active}
            if wid not in self.leases:
                used = set(self.leases.values())
                server = next((s for s in self.servers if s not in used), None)
                if server is None:
                    server = KD.Server(('127.0.0.1', 0), self.handler)
                    self.servers.append(server)
                    threading.Thread(target=server.serve_forever, kwargs={'poll_interval': .1},
                                     daemon=True, name='window-door').start()
                self.leases[wid] = server
            return f'http://127.0.0.1:{self.leases[wid].server_address[1]}'

    def close(self):
        for server in self.servers:
            server.shutdown()
            server.server_close()


class DesktopServer(KD.Server):
    def server_close(self):
        if hasattr(self, 'window_origins'):
            self.window_origins.close()
        super().server_close()


def make_desk_handler(kernel, entry):
    Base = KD.make_handler(kernel, entry, "")
    widgets = Widgets(kernel)

    class Handler(Base):
        widget_broker = widgets

        def do_POST(self):
            path = urlsplit(self.path).path
            if path.startswith('/desk/widget/'):
                if self._cross_site():
                    return self._send(403, {'ok': False, 'text': 'foreign origin'})
                if not secrets.compare_digest(self.headers.get('X-Agora-Widget-Host') or '', widgets.guard_key):
                    return self._send(403, {'ok': False, 'text': 'widgets need a guarded desktop host'})
                actor, why = self._actor()
                if actor is None:
                    return self._send(401, {'ok': False, 'text': why})
                from kernel.blobs import cap
                body_size = int(self.headers.get('Content-Length') or 0)
                if body_size > max(100000, 4 * ((cap(kernel) + 2) // 3) + 16384):
                    return self._send(413, {'ok': False, 'text': 'bridge message too large'})
                try:
                    body = self._body() or {}
                    if body_size > 100000 and body.get('op') != 'upload':
                        return self._send(413, {'ok': False, 'text': 'bridge message too large'})
                    out = widgets.request(actor, path.rsplit('/', 1)[-1], body)
                except (KD.Refused, ValueError, KeyError, TypeError) as e:
                    out = {'ok': False, 'text': 'refused: ' + str(e)}
                return self._send(200, out)
            return super().do_POST()

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == '/desk/window-origin':
                actor, why = self._actor()
                if actor is None:
                    return self._send(401, {'error': why})
                if not kernel.is_steward(actor.person):
                    return self._send(403, {'error': 'only the desktop owner opens windows'})
                q = parse_qs(urlsplit(self.path).query)
                nxt = q.get('next', [''])[0]
                dest = urlsplit(nxt)
                if (dest.scheme or dest.netloc or '\\' in nxt or any(ord(c) < 32 or ord(c) == 127 for c in nxt)
                        or not (dest.path.startswith('/desk/') or dest.path == '/lens.html')):
                    return self._send(400, {'error': 'not a desktop page'})
                try:
                    origin = Handler.window_origins.origin(q.get('win', [''])[0])
                except ValueError as e:
                    return self._send(404, {'error': str(e)})
                return self._raw(302, b'', 'text/plain', [('Location', origin + nxt)])
            if path.startswith("/desk/theme") and path[6:] in ("theme.css", "theme.json", "theme-native.json",
                                                                 "theme-wallpaper"):
                return self._theme(path[6:], {k: v[0] for k, v in parse_qs(urlsplit(self.path).query).items()},
                                   "/desk/")
            if path == "/desk/icon":
                # colour icons with alpha for the shell (shell_icons.py): exe:, hwnd:, pkg:, aumid:, agora: references
                actor, why = self._actor()
                if actor is None or not kernel.is_steward(actor.person):
                    return self._send(401, {"error": why or "only the desktop owner"})
                import shell_icons
                q = parse_qs(urlsplit(self.path).query)
                code, ctype, data = shell_icons.serve(q.get("ref", [""])[0], q.get("size", ["128"])[0])
                return self._raw(code, data, ctype, [("Cache-Control", "private, max-age=3600")])
            if path.startswith("/desk/"):
                return self._file(path[6:])
            if path == '/lens.html':
                # Desktop hosts use local system type. Keep the shared painter
                # unchanged, but do not let its optional Google font hit the network.
                content, ctype = KP.static_file(path)
                content = re.sub(rb'<link[^>]+href="https://fonts\.googleapis\.com/[^>]+>', b'', content)
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
            self._raw(200, content, ctype)

    return Handler


def start(world=DEFAULT_WORLD, port=8810, modules=True, headless=False):
    """-> (kernel, server, host, entry). Serves on a thread; the caller decides how long it lives."""
    world = Path(world)
    k = Kernel(world, None if (world / "log" / "0001.jsonl").exists() else genesis(headless))
    after_genesis(k, headless)
    entry = LocalEntry(k.keep_dir)
    moving_in(k)
    k.dev_sessions = lambda: entry.sessions             # the door's /dev/signin knows these sessions
    handler = make_desk_handler(k, entry)
    srv = DesktopServer(("127.0.0.1", port), handler)
    srv.window_origins = handler.window_origins = WindowOrigins(k, handler)
    os.environ['AGORA_WIDGET_HOST_KEY'] = handler.widget_broker.guard_key
    os.environ["AGORA_KDESK_PORT"] = str(srv.server_address[1])     # the modules (children) read where the door is
    host = KM.Host(k, HERE)
    threading.Thread(target=srv.serve_forever, daemon=True, name="door").start()
    if modules:
        host.reconcile()
    if modules and not headless:
        from widget_overlay import Overlays
        srv.widget_overlays = Overlays(k, f'http://127.0.0.1:{srv.server_address[1]}', entry)
        threading.Thread(target=srv.widget_overlays.loop, daemon=True, name='widget-surfaces').start()
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
            srv.RequestHandlerClass.widget_broker.reap()
            host.reconcile()                        # a module that died is started again (after the kernel's rest)
    except KeyboardInterrupt:
        pass
    finally:
        if hasattr(srv, 'widget_overlays'):
            srv.widget_overlays.close()
        host.stop_all()
        srv.shutdown()
        srv.server_close()


if __name__ == "__main__":
    main()
