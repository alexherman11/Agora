"""The desktop on the new kernel, tested hidden: a fresh world per test, the kernel's door on a free loopback port, and
both modules (window, guy) running for real as processes but --headless (their windows are kept in memory, nothing
appears on the screen). Everything is said as lines over HTTP, as Alex's pages and his agent say them.

    C:/Projects/Agora4/.venv/Scripts/python.exe -m unittest test_kdesk -v        (from research/window-lab/kernel-desktop)
"""
import json
import shutil
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kdesk  # noqa: E402

SEE = {"help", "look", "rows", "holds", "status", "window.list"}
FEED = ("root : column, role sheet, of tag:post as p, each card\n"
        "card : column, role card\n"
        "  t : text \"$text\"\n"
        "  l : text \"likes $likes\", role tool, on click do like $item\n")


def quoted(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


class Desk:
    def __init__(self):
        self.dir = tempfile.mkdtemp(prefix="kdesk-test-")
        self.k, self.srv, self.host, self.entry = kdesk.start(Path(self.dir) / "world", 0, headless=True)
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        self.wait(lambda: "window.list" in self.say("help", "alex")["text"] and
                  "holds window.overlay" in self.say("status guy", "alex")["text"], 20)

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
        self.host.stop_all()
        self.srv.shutdown()
        self.srv.server_close()
        shutil.rmtree(self.dir, ignore_errors=True)


class DesktopTest(unittest.TestCase):
    def setUp(self):
        self.d = Desk()

    def tearDown(self):
        self.d.close()

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
        self.assertEqual([r["label"] for r in rows], ["Lines"])
        self.assertTrue(d.say(rows[0]["does"], "alex")["ok"])                # the taskbar's press, as Alex
        d.wait(lambda: d.window("lines"))

    def test_a_verb_note_composes_window_words(self):
        d = self.d
        d.say("window.open help")
        d.say("window.open lines")
        d.wait(lambda: len(d.windows()) == 3)
        a, b = d.wait(lambda: d.window("help")), d.wait(lambda: d.window("lines"))
        out = d.say('verb side steps="window.move $1 to=left; window.move $2 to=right" '
                    'help="side <window> <window>: two windows side by side"')
        self.assertTrue(out["ok"], out["text"])
        self.assertIn("from: verb", d.say("help side")["text"])
        out = d.say(f"side {a['id']} {b['id']}")
        self.assertTrue(out["ok"], out["text"])
        d.wait(lambda: d.window("help")["box"][0] == 24 and d.window("lines")["box"][0] > 1000)

    def test_a_rule_hears_window_opened(self):
        d = self.d
        out = d.say('make kind=rule on=window.opened do="window.move $target to=right"')
        self.assertTrue(out["ok"], out["text"])
        d.say("window.open help")
        d.wait(lambda: d.window("help")["box"][0] > 1000)
        d.wait(lambda: d.k.fired > 0)

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
        r = d.k.run(d.k.own_actor(mid), "make kind=button bar=taskbar label=sneaky")
        self.assertFalse(r["ok"])
        self.assertIn("reaches window things, not a button", r["text"])
        self.assertTrue(d.k.run(d.k.own_actor(mid), "make kind=window shows=help name=Help at=10,10 size=500,500")["ok"])
        self.assertFalse(d.k.run(d.k.own_actor(mid), "post hello from a module")["ok"])

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

    def test_replay_gives_the_same_world(self):
        d = self.d
        d.say("window.open lines")
        d.say('make kind=button bar=taskbar label=Lines does="window.open lines"')
        d.wait(lambda: len(d.windows()) == 2)
        from kernel.store import Log
        again = Log(Path(d.dir) / "world").replay()
        self.assertEqual(again.snapshot(), d.k.state.snapshot())


if __name__ == "__main__":
    unittest.main()
