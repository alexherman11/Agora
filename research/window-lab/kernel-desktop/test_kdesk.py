"""The desktop on the new kernel, tested hidden: a fresh world per test, the kernel's door on a free loopback port, and
both modules (window, guy) running for real as processes but --headless (their windows are kept in memory, nothing
appears on the screen). Everything is said as lines over HTTP, as Alex's pages and his agent say them.

    C:/Projects/Agora4/.venv/Scripts/python.exe -m unittest test_kdesk -v        (from research/window-lab/kernel-desktop)
"""
import json
import struct
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from urllib.parse import quote
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kdesk  # noqa: E402
from kernel import scratch  # noqa: E402

SEE = {"help", "look", "rows", "holds", "status", "window.list", "window.desktop", "system.now", "media.now"}
FEED = ("root : column, role sheet, of tag:post as p, each card\n"
        "card : column, role card\n"
        "  t : text \"$text\"\n"
        "  l : text \"likes $likes\", role tool, on click do like $item\n")


def quoted(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def scratch_dir(prefix):
    """A fresh folder for a test world. Not tempfile.mkdtemp: since Python 3.12.4 that makes an owner-only folder on
    Windows (SYSTEM, Administrators, OWNER RIGHTS, nothing inherited), so a sandboxed House worker can't write inside it,
    even in its own worktree. A plain mkdir inherits the folder's access. Point TMP at a writable place first."""
    base = Path(tempfile.gettempdir())
    for _ in range(100):
        p = base / f"{prefix}{os.urandom(4).hex()}"
        try:
            p.mkdir(parents=True)
            return str(p)
        except FileExistsError:
            continue
    raise FileExistsError(f"no free scratch name under {base}")


class Desk:
    def __init__(self):
        self.dir = scratch_dir("kdesk-test-")
        self.k, self.srv, self.host, self.entry = kdesk.start(Path(self.dir) / "world", 0, headless=True)
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        self.wait(lambda: "window.list" in self.say("help all", "alex")["text"] and
                  "holds window.overlay" in self.say("status guy", "alex")["text"], 20)
        # Offers arrive asynchronously. Wait for every publisher before measuring
        # an unchanged log; late dictionary-install records are not telemetry.
        self.wait(lambda: all(w in self.say('help all')['text'] for w in ('system.now','media.now','media.prev'))
                  and self.window('taskbar'), 20)

    def say(self, line, who="claude"):
        route = "/see" if line.split()[0] in SEE else "/do"
        req = urllib.request.Request(self.url + route, json.dumps({"line": line}).encode(),
                                     {"Content-Type": "application/json",
                                      "Authorization": "Bearer " + self.entry.token(who)})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            return {"ok": False, "text": e.read().decode(), "code": e.code}

    def wait(self, cond, timeout=10):
        end = time.time() + timeout
        while time.time() < end:
            try:
                got = cond()
                if got:
                    return got
            except Exception:
                pass
            time.sleep(0.2)
        raise AssertionError("timed out waiting")

    def windows(self):
        return [r for r in self.say("window.list")["rows"] if r.get("kind") == "window"]

    def window(self, shows):
        return next((w for w in self.windows() if w["shows"] == shows), None)

    def close(self):
        # door first, then unhook the modules from the kernel, then stop them: every kernel act ends with a reconcile,
        # so an act still running (a module's own, a request) would otherwise start a module after stop_all
        self.srv.shutdown()
        self.k.modules = None
        self.host.stop_all()
        self.srv.server_close()
        shutil.rmtree(self.dir, ignore_errors=True)


class DesktopTest(unittest.TestCase):
    def setUp(self):
        self.d = Desk()

    def tearDown(self):
        self.d.close()

    def test_window_origins_are_distinct_reused_and_keep_origin_protection(self):
        d = self.d
        for _ in range(2):
            self.assertTrue(d.say('window.open help new=yes')['ok'])
        windows = d.wait(lambda: [w for w in d.windows() if w['shows'] == 'help'])
        d.wait(lambda: len([w for w in d.windows() if w['shows'] == 'help']) == 2)
        windows = [w for w in d.windows() if w['shows'] == 'help']
        pool = d.srv.window_origins
        first, second = [pool.origin(w['id']) for w in windows]
        self.assertNotEqual(first, second)
        self.assertEqual(first, pool.origin(windows[0]['id']))
        route = d.url + '/desk/window-origin?win=' + windows[0]['id'] + '&next='
        for nxt in ('//example.com/x', '/desk/x\r\nInjected: yes', '/desk/\\example.com'):
            req = urllib.request.Request(route + quote(nxt, safe=''),
                headers={'Authorization': 'Bearer ' + d.entry.token('alex')})
            with self.assertRaises(urllib.error.HTTPError) as refused:
                urllib.request.urlopen(req, timeout=2)
            self.assertEqual(400, refused.exception.code)
        with self.assertRaises(urllib.error.HTTPError) as refused:
            urllib.request.urlopen(route + quote('/desk/help.html', safe=''), timeout=2)
        self.assertEqual(401, refused.exception.code)
        for origin in (first, second):
            sibling = second if origin == first else first
            for supplied, status in ((origin, 200), (sibling, 403), (d.url, 403), ('https://example.com', 403), ('null', 403)):
                req = urllib.request.Request(origin + '/see', b'{"line":"help"}',
                    {'Content-Type': 'application/json', 'Origin': supplied,
                     'Authorization': 'Bearer ' + d.entry.token('alex')})
                try:
                    with urllib.request.urlopen(req, timeout=2) as r:
                        self.assertEqual(r.status, status)
                except urllib.error.HTTPError as e:
                    self.assertEqual(e.code, status)
        self.assertTrue(d.say('window.close ' + windows[0]['id'])['ok'])
        d.wait(lambda: all(w['id'] != windows[0]['id'] for w in d.windows()))
        self.assertTrue(d.say('window.open help new=yes')['ok'])
        new = d.wait(lambda: next((w for w in d.windows() if w['shows'] == 'help'
                     and w['id'] not in {r['id'] for r in windows}), None))
        self.assertEqual(first, pool.origin(new['id']))
        self.assertEqual(2, len(pool.servers))

    def test_taskbar_appears_by_itself_and_windows_open_move_close_and_undo(self):
        d = self.d
        d.wait(lambda: d.window("taskbar"))
        out = d.say("window.open lines")
        self.assertTrue(out["ok"], out["text"])
        self.assertIn("by window for Alex", out["text"])                    # one record, by the module, for its caller
        w = d.wait(lambda: d.window("lines"))
        out = d.say(f"window.move {w['id']} to=left")
        self.assertTrue(out["ok"], out["text"])
        d.wait(lambda: d.window("lines")["box"][0] == 24)
        out = d.say(f"window.close {w['id']}")
        self.assertTrue(out["ok"], out["text"])
        d.wait(lambda: d.window("lines") is None)
        out = d.say("undo")
        self.assertTrue(out["ok"], out["text"])
        back = d.wait(lambda: d.window("lines"))                            # back, where it was (on the left)
        self.assertEqual(back["box"][0], 24)

    def test_a_page_from_another_door_on_this_machine_opens_in_its_own_window(self):
        # 27 Oct: the top bar's JEFF button opened JEFF's conversation, a lens of the frontier desk on 8794. That desk
        # was archived on 27 Oct, and a window on a door that does not answer stays shut (28 Oct), so another door
        # that answers stands in for it here.
        import http.server
        other = http.server.ThreadingHTTPServer(("127.0.0.1", 0), http.server.SimpleHTTPRequestHandler)
        threading.Thread(target=other.serve_forever, daemon=True).start()
        self.addCleanup(other.server_close)
        self.addCleanup(other.shutdown)
        d = self.d
        page = f"http://127.0.0.1:{other.server_address[1]}/lens.html?session=frontier&as=alex&lens=jeff-chat&inspect=0"
        out = d.say(f'window.open url="{page}" name=JEFF')
        self.assertTrue(out["ok"], out["text"])
        w = d.wait(lambda: d.window("page"))
        self.assertEqual("JEFF", w["name"])
        again = d.say(f'window.open url="{page}" name=JEFF')                 # the same page is brought forward
        self.assertIn("open already", again["text"])
        self.assertEqual(1, sum(1 for x in d.windows() if x["shows"] == "page"))
        for far in ("https://example.com/", "http://192.168.1.4:8794/", "file:///C:/Windows/win.ini", "http://127.0.0.1/"):
            self.assertIn("this machine only", d.say(f'window.open url="{far}"')["text"], far)

    def test_a_picture_of_a_view_is_a_file_that_a_line_hands_on(self):
        # 4 Nov, the wallpaper pilot: window.picture draws what window.open would show, hidden, and hands it back as
        # the caller's own file; in a line, `; ... $new` passes it on (the world rule that makes the theme the
        # wallpaper is this line on theme.changed). The window module may make files only once a steward says so.
        d = self.d
        mod = next(r["id"] for r in d.say("rows module", "alex")["rows"] if r.get("name") == "window")
        refused = d.say("window.picture help size=320x200", "alex")
        self.assertFalse(refused.get("ok"), refused["text"])
        self.assertIn("upload", refused["text"])
        self.assertTrue(d.say(f'grant {mod} words="upload" only=kind:file', "alex")["ok"])
        sid = d.say('make kind=shell-settings name="Shell settings"', "alex")["made"][0]
        out = d.say(f'window.picture help size=320x200 name="Help picture" ; set {sid} wallpaper=$new', "alex")
        self.assertTrue(out["ok"], out["text"])
        fid = d.say("rows shell-settings", "alex")["rows"][0]["wallpaper"]
        f = next(r for r in d.say("rows file", "alex")["rows"] if r["id"] == fid)
        self.assertEqual(("image/png", "Help picture"), (f["mime_type"], f["name"]))
        data = (Path(d.dir) / "world" / "blobs" / f["blob_hash"]).read_bytes()
        self.assertEqual(b"\x89PNG", data[:4])
        self.assertEqual((320, 200), struct.unpack(">II", data[16:24]))     # the PNG's own width and height
        self.assertIn("no view, lens or thing", d.say("window.picture nothing-called-this", "alex")["text"])

    def test_off_window_closes_all_and_undo_brings_them_back(self):
        d = self.d
        d.say("window.open lines")
        d.wait(lambda: len(d.windows()) == 2)
        out = d.say("off window", "alex")
        self.assertTrue(out["ok"], out["text"])
        self.assertIn("off", d.say("window.list")["text"])
        self.assertTrue(d.say("undo", "alex")["ok"])
        d.wait(lambda: len(d.windows()) == 2, 15)

    def test_a_taskbar_button_is_a_line_and_its_line_runs_as_whoever_presses_it(self):
        d = self.d
        out = d.say('make kind=button bar=taskbar label="Lines" does="window.open lines"')
        self.assertTrue(out["ok"], out["text"])
        rows = d.say("rows any bar=taskbar")["rows"]
        rows = [r for r in rows if r["id"] == out["made"][0]]
        self.assertEqual([r["label"] for r in rows], ["Lines"])
        self.assertTrue(d.say(rows[0]["does"], "alex")["ok"])                # the taskbar's press, as Alex
        d.wait(lambda: d.window("lines"))

    def test_where_a_window_sits_is_not_in_the_world(self):
        # Alex, 26 Oct: "visual state should not live in the world". The world says which windows are open and what
        # they show; where they sit is this screen's (and its window manager's). A move changes the screen only.
        d = self.d
        d.say("window.open help")
        d.say("window.open lines")
        d.wait(lambda: len(d.windows()) == 3)
        a, b = d.wait(lambda: d.window("help")), d.wait(lambda: d.window("lines"))
        for row in d.say("rows window")["rows"]:
            self.assertNotIn("at", row)
            self.assertNotIn("size", row)
        out = d.say(f"window.move {b['id']} to=left")
        self.assertTrue(out["ok"], out["text"])
        self.assertFalse(out.get("records"), out)
        d.wait(lambda: d.window("lines")["box"][0] == 24)
        # a verb of module words still works: `shove` is `window.move`, and it records nothing either
        out = d.say('verb shove steps="window.move $1 to=right" help="shove <window>: to the right"')
        self.assertTrue(out["ok"], out["text"])
        out = d.say(f"shove {a['id']}")
        self.assertTrue(out["ok"], out["text"])
        d.wait(lambda: d.window("help")["box"][0] > 1000)
        for row in d.say("rows window")["rows"]:
            self.assertNotIn("at", row)

    def test_a_rule_hears_window_opened(self):
        d = self.d
        out = d.say('make kind=rule on=window.opened do="window.move $target to=right"')
        self.assertTrue(out["ok"], out["text"])
        d.say("window.open help")
        d.wait(lambda: d.window("help")["box"][0] > 1000)
        d.wait(lambda: d.k.rules_fired)

    def test_stop_is_a_verb_note_made_in_the_world(self):
        d = self.d
        self.assertFalse(d.say("stop guy", "alex")["ok"])                   # nothing answers to stop yet
        out = d.say('verb stop steps="off $1" help="stop <module>: the same as off"')
        self.assertTrue(out["ok"], out["text"])
        out = d.say("stop guy", "alex")
        self.assertTrue(out["ok"], out["text"])
        d.wait(lambda: "nothing is held" in d.say("holds")["text"])          # off ended his hold
        self.assertIn("not running", d.say("status guy")["text"])
        self.assertTrue(d.say("undo", "alex")["ok"])                        # undo brings him back, holding again
        d.wait(lambda: "guy holds window.overlay" in d.say("holds")["text"], 15)

    def test_the_guy_says_what_he_is_and_what_he_is_doing(self):
        d = self.d
        self.assertIn("a module: on, running", d.say("look guy")["text"])
        self.assertIn("guy holds window.overlay", d.say("holds")["text"])
        self.assertTrue(d.say("guy.say hello")["ok"])
        self.assertIn("saying", d.say("status guy")["text"])

    def test_the_window_module_is_narrowed_to_window_things(self):
        d = self.d
        mid = d.k.module_named("window")
        r = d.k.module_own(mid, "make kind=button bar=taskbar label=sneaky")
        self.assertFalse(r["ok"])
        self.assertIn("reaches only window things, not a button", r["text"])
        self.assertTrue(d.k.module_own(mid, "make kind=window shows=help name=Help at=10,10 size=500,500")["ok"])
        self.assertFalse(d.k.module_own(mid, "post hello from a module")["ok"])

    def test_only_the_owner_opens_windows(self):
        d = self.d
        k = d.k
        from kernel.kernel import Actor, Tx
        with k.lock:                                     # a second person in the place
            tx = Tx(k)
            tx.part("join", None, "join")
            pid = tx.mint()
            tx.set(pid, "kind", "person")
            tx.set(pid, "name", "Maya")
            k._commit(tx, by=pid, words="join", via="test")
        r = k.run(Actor(pid, pid, "person"), "window.open lines")
        self.assertFalse(r["ok"])
        self.assertIn("only for this desktop's owner", r["text"])
        for word in ('window.desktop', 'window.start', 'window.activate handle=123', 'window.settings which=volume',
                     'window.launch path=C:/Windows/notepad.exe'):
            r = k.run(Actor(pid, pid, 'person'), word)
            self.assertFalse(r['ok'], word)
            self.assertIn("only for this desktop's owner", r['text'])

    def test_the_stream_carries_happenings(self):
        d = self.d
        got = []

        def listen():
            req = urllib.request.Request(d.url + "/door/stream",
                                         headers={"Authorization": "Bearer " + d.entry.token("alex")})
            with urllib.request.urlopen(req, timeout=10) as r:
                for line in r:
                    if line.startswith(b"data: "):
                        got.append(json.loads(line[6:]))
                        if any(h.get("word") == "post" for h in got):
                            return
        t = threading.Thread(target=listen, daemon=True)
        t.start()
        time.sleep(0.5)
        d.say("post a happening for the stream")
        t.join(8)
        self.assertTrue(any(h.get("word") == "post" for h in got), got)

    def test_a_lens_window_paints_kernel_things_through_lens_js(self):
        d = self.d
        self.assertTrue(d.say(f"make kind=lens name=feed text={quoted(FEED)}")["ok"])
        self.assertTrue(d.say("post Council meets Tuesday")["ok"])
        out = d.say("window.open feed")
        self.assertTrue(out["ok"], out["text"])
        w = d.wait(lambda: d.window("feed"))
        self.assertEqual(d.k.state.get(w["id"], "lens"), "feed")
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
        tok = d.entry.token("alex")
        r = opener.open(d.url + f"/dev/signin?token={tok}&next=/desk/frame.html%3Fwin%3D{w['id']}%26lens%3Dfeed",
                        timeout=10)
        self.assertIn(b"lens.js itself", r.read())                       # the frame, reached with the cookie set
        sc = json.loads(opener.open(d.url + "/api/scene?lens=feed", timeout=30).read())
        self.assertIn("Council meets Tuesday", sc.get("text", ""), sc)

    # -- the bars (24 Oct): the top bar is a lens on the top edge; widgets are world things painted with live readings
    def make_top_bar(self):
        d = self.d
        lenses = HERE / "lenses"
        out = d.say(f"make kind=style name=bars text={quoted((lenses / 'bars.style').read_text(encoding='utf-8'))}")
        self.assertTrue(out["ok"], out["text"])
        out = d.say(f"make kind=lens name=topbar style=bars "
                    f"text={quoted((lenses / 'topbar.lens').read_text(encoding='utf-8'))}")
        self.assertTrue(out["ok"], out["text"])

    def scene(self, lens):
        d = self.d
        req = urllib.request.Request(d.url + f"/api/scene?lens={lens}&text=1",
                                     headers={"Authorization": "Bearer " + d.entry.token("alex")})
        with urllib.request.urlopen(req, timeout=30) as r:
            out = json.loads(r.read())
        return out.get("refused") or out.get("text") or ""

    def test_the_top_bar_is_a_lens_on_the_top_edge(self):
        d = self.d
        self.make_top_bar()
        out = d.say("window.open topbar edge=top")
        self.assertTrue(out["ok"], out["text"])
        bar = d.wait(lambda: d.window("topbar"))
        self.assertEqual(d.k.state.get(bar["id"], "edge"), "top")
        self.assertEqual(bar["box"][1], 0)                                 # along the top, the whole width
        self.assertEqual(d.wait(lambda: d.window("taskbar"))["box"][1] > 1000, True)   # the strip keeps the bottom
        self.assertIn("holds", d.say("window.open topbar edge=top new=yes")["text"])   # one bar per edge
        self.assertFalse(d.say("window.open lines edge=top")["ok"])        # only a lens can be a bar
        self.assertIn("keeps its edge", d.say(f"window.move {bar['id']} to=left")["text"])
        self.assertTrue(d.say(f"window.close {bar['id']}")["ok"])
        d.wait(lambda: d.window("topbar") is None)
        self.assertTrue(d.say("undo")["ok"])
        d.wait(lambda: d.window("topbar"))

    def test_a_widget_is_one_line_and_shows_a_live_reading(self):
        d = self.d
        self.make_top_bar()
        self.assertNotIn("CPU", self.scene("topbar"))
        out = d.say("make kind=widget bar=top side=right shows=cpu label=CPU order=40")   # one line, as an agent says it
        self.assertTrue(out["ok"], out["text"])
        d.wait(lambda: '"12%"' in self.scene("topbar"), 15)               # the system module's (headless) reading
        n = len(d.k.log.records)
        time.sleep(4.5)                                                   # two more readings arrive
        self.assertEqual(len(d.k.log.records), n)
        d.say("make kind=widget bar=top side=right shows=time order=100")
        d.say("make kind=widget bar=top side=right shows=feed label=Feed order=90")
        d.say("post one")
        d.say("post two")
        text = self.scene("topbar")
        self.assertIn(time.strftime("%H:%M"), text)
        self.assertIn('"2" [value]', text)                               # two posts not read yet
        cpu = next(r for r in d.say("rows widget")["rows"] if r.get("shows") == "cpu")
        self.assertTrue(d.say(f"set {cpu['id']} order=5 side=left")["ok"])          # moved across, by a line
        self.assertIn("[pill] row tip \"CPU: 12% \" · only when $bar = \"top\" and $side = \"left\" ($bar=top, $side=left)",
                      self.scene("topbar"))
        self.assertTrue(d.say(f"forget {cpu['id']}")["ok"])
        self.assertNotIn('"CPU"', self.scene("topbar"))

    def test_system_and_media_words(self):
        d = self.d
        d.wait(lambda: "media.now" in d.say("help all", "alex")["text"] and "system.now" in d.say("help all", "alex")["text"], 20)
        out = d.say("system.now")
        self.assertTrue(out["ok"], out["text"])
        self.assertIn("cpu: 12%", out["text"])
        self.assertIn("nothing is playing", d.say("media.now")["text"])
        out = d.say("media.play")                                          # 27 Oct (P3): an honest no-op
        self.assertFalse(out["ok"], out["text"])
        self.assertIn("nothing pressed", out["text"])
        self.assertIn("nothing pressed", d.say("media.pause")["text"])
        out = d.say("media.play start=yes")
        self.assertTrue(out["ok"], out["text"])
        self.assertIn("undo cannot take it back", out["text"])            # it touched the outside world

    def test_replay_gives_the_same_world(self):
        d = self.d
        d.say("window.open lines")
        d.say('make kind=button bar=taskbar label=Lines does="window.open lines"')
        d.wait(lambda: len(d.windows()) == 2)
        from kernel.store import Log
        again = Log(Path(d.dir) / "world").replay()
        self.assertEqual(again.snapshot(), d.k.state.snapshot())

    def test_native_words_remain_words_and_are_owner_only(self):
        d = self.d
        d.wait(lambda: 'window.desktop' in d.say('help all')['text'])
        self.assertEqual(d.say('window.desktop')['rows'], [])
        for word in ('window.start', 'window.activate handle=123', 'window.settings which=volume',
                     'window.launch path=C:/Windows/notepad.exe'):
            out = d.say(word)
            self.assertTrue(out['ok'], out)
            self.assertIn('headless', out['text'])
            self.assertIn('undo cannot take it back', out['text'])

    def test_v2_definitions_are_world_things_and_feed_actions_survive(self):
        d = self.d
        from restyle import install
        install(d.entry.token('claude'), d.srv.server_address[1])
        slots = {r['slot']:r for r in d.say('rows any bar=taskbar')['rows'] if r.get('slot')}
        self.assertEqual(set(slots), {'start','agora','network','volume','battery','clock','off','holds','twitch'})
        self.assertEqual(slots['start']['does'], 'window.start')
        self.assertEqual(slots['off']['confirm'], 'yes')
        self.assertTrue(d.say(f"set {slots['start']['id']} label=Launcher icon=layout-grid")['ok'])
        self.assertEqual(next(r for r in d.say('rows button')['rows'] if r.get('slot')=='start')['label'], 'Launcher')
        d.say('post A useful post')
        text = self.scene('feed')
        self.assertIn('A useful post', text)
        self.assertIn('like ', text)
        self.assertIn('pin ', text)
        self.assertIn('make kind=pin bar=taskbar', text)
        d.say('make kind=widget bar=top side=right shows=cpu order=40')
        d.say('make kind=widget bar=top side=right shows=media order=30 does="media.play"')
        text = self.scene('topbar')
        self.assertIn('[icon] picture', text)
        self.assertIn('tip "Cpu:', text)
        self.assertNotIn('fonts.googleapis', (HERE / 'pages' / 'taskbar.html').read_text())


class RecoveryTest(unittest.TestCase):
    """Real separate watchdog processes; only a hidden surrogate HWND is touched.

    Enabled/disabled stands in for shown/hidden, keeping every test invisible.
    The production lease/owner-identity/death/recovery code is otherwise identical.
    """
    def setUp(self):
        import ctypes as C
        from ctypes import wintypes as W
        import subprocess
        import taskbar_guard as guard
        self.C, self.W, self.guard = C, W, guard
        (HERE / 'state').mkdir(exist_ok=True)        # ignored by git, so absent in a fresh House worktree
        self.tmp = scratch.TemporaryDirectory(prefix='taskbar-probe-', dir=HERE / 'state')
        self.lease = Path(self.tmp.name) / 'lease.json'
        self.u = C.WinDLL('user32')
        self.u.CreateWindowExW.argtypes = [W.DWORD,W.LPCWSTR,W.LPCWSTR,W.DWORD,C.c_int,C.c_int,C.c_int,C.c_int,W.HWND,W.HMENU,W.HINSTANCE,W.LPVOID]
        self.u.CreateWindowExW.restype = W.HWND
        self.u.IsWindowEnabled.argtypes = [W.HWND]
        self.u.DestroyWindow.argtypes = [W.HWND]
        self.hwnd = self.u.CreateWindowExW(0, 'STATIC', 'Invisible taskbar surrogate', 0, 0, 0, 10, 10, None, None, None, None)
        self.assertTrue(self.hwnd)
        self.owner = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(60)'], creationflags=0x08000000)
        self.worker = subprocess.Popen([sys.executable, str(HERE / 'taskbar_guard.py'), '--owner', str(self.owner.pid),
                                        '--lease', str(self.lease), '--probe', str(self.hwnd)], creationflags=0x08000000)
        self.wait(lambda: self.data().get('ready'))
        self.assertFalse(self.u.IsWindowEnabled(self.hwnd))
        self.assertFalse(guard.u.IsWindowVisible(self.hwnd))

    def data(self):
        try:
            return json.loads(self.lease.read_text())
        except (OSError,ValueError):
            return {}

    def wait(self, cond):
        end = time.monotonic()+10
        while time.monotonic()<end:
            msg = self.W.MSG()
            while self.u.PeekMessageW(self.C.byref(msg),None,0,0,1):
                self.u.TranslateMessage(self.C.byref(msg))
                self.u.DispatchMessageW(self.C.byref(msg))
            if cond():
                return
            time.sleep(.02)
        self.fail('watchdog did not acknowledge hidden probe')

    def tearDown(self):
        self.owner.terminate()
        if self.worker.poll() is None:
            self.worker.terminate()
        self.worker.wait(timeout=5)
        self.owner.wait(timeout=5)
        self.u.DestroyWindow(self.hwnd)
        self.tmp.cleanup()

    def test_hard_owner_death_restores_taskbar(self):
        self.owner.kill()
        self.wait(lambda: self.data().get('restored'))
        self.assertTrue(self.u.IsWindowEnabled(self.hwnd))
        self.assertFalse(self.guard.u.IsWindowVisible(self.hwnd))

    def test_off_release_restores_taskbar(self):
        data = self.data()
        data['release'] = True
        self.guard.write(self.lease, data)
        self.wait(lambda: self.data().get('restored'))
        self.assertTrue(self.u.IsWindowEnabled(self.hwnd))

    def test_signin_recovers_stale_lease_and_leaves_active_owner_alone(self):
        self.assertFalse(self.guard.restore(self.lease))
        self.worker.kill()
        self.worker.wait(timeout=5)
        self.owner.kill()
        self.owner.wait(timeout=5)
        self.assertTrue(self.guard.restore(self.lease))
        self.assertTrue(self.u.IsWindowEnabled(self.hwnd))

    def test_reused_pid_does_not_keep_stale_lease(self):
        data = self.data()
        data['created'] += 1
        self.assertFalse(self.guard.owner_alive(data))


if __name__ == "__main__":
    unittest.main()
