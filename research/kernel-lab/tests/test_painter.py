"""The painter's routes on the kernel: lens.js's own requests, answered from kernel things through the desk's compiler.

Every press here is made the way lens.js makes one (desk-shell/lens.js, sendNow): the line from a painted node's
`acts`, and `observed` from that node's `fence`. Nothing is hand-built that lens.js would not send.
"""
import json
import os
import secrets
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_skeleton import StandInEntry, post        # noqa: E402
from kernel.door import serve                        # noqa: E402
from kernel.kernel import Kernel                     # noqa: E402
from kernel.painter import NOTATION                  # noqa: E402

FEED = ("root : column, role sheet, of tag:post as p, each card\n"
        "card : column, role card\n"
        "  who : text \"$by\", role meta\n"
        "  t : text \"$text\"\n"
        "  n : row\n"
        "    l : text \"♥ $likes\", role tool, on click do like $item\n"
        "    p : text \"pin\", role tool, on click do pin $item\n")


def quoted(text):
    """A value for `k="..."` in a line: its own quotes and backslashes escaped, as the line language (and the desk)
    asks. Without this a lens's `text "$by"` ends the value at its first quote (found 23 Oct, as on the desk)."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def walk(n):
    yield n
    for k in n.get("kids") or []:
        yield from walk(k)


class Painter(unittest.TestCase):
    def setUp(self):
        self.t0 = time.time()
        self.dir = tempfile.mkdtemp(prefix="kernel-paint-")
        self.secret = secrets.token_hex(16)
        self.entry = StandInEntry(self.secret)
        self.k = Kernel(self.dir, {"tag": "sb", "name": "Seabright", "invites_counted_by": "kernel",
                                   "steward": {"account": "google:alex", "name": "Alex"},
                                   "invites": [{"code": "x", "uses": 9}], "groups": [{"name": "Organizers"}]})
        self.srv, self.host = serve(self.k, self.entry.url, self.secret, 0, LAB)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        self.entry.kernel_url = self.url
        self.alex = "alex"
        self.entry.sessions[self.alex] = {"account": "google:alex", "method": "google"}
        self.maya, _ = self.entry.sign_in("google:maya", "Maya", invite="x")
        self.group = self.k.things("group")[0]

    def tearDown(self):
        for s in (self.srv, self.entry.srv):
            s.shutdown()
            s.server_close()
        self.host.stop_all()

    def get(self, path, token):
        req = urllib.request.Request(self.url + path, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())

    def do(self, token, line):
        code, out = post(self.url + "/do", {"line": line}, token=token)
        self.assertEqual(code, 200, out)
        self.assertTrue(out["ok"], out["text"])
        return out

    def scene(self, token):
        r = self.get("/api/scene?lens=feed&view=painter&text=1", token)
        self.assertNotIn("refused", r, r.get("refused"))
        return r

    def press(self, token, sc, key_end, on="click"):
        """What lens.js sends for a press on the painted part whose key ends with `key_end`."""
        app, part = key_end.split("/")
        node = next(n for n in walk(sc["scene"]) if n.get("acts") and n["key"].startswith(f"root/{app}/")
                    and n["key"].endswith("/" + part))
        act = next(a for a in node["acts"] if a["on"] == on)
        observed = dict(node.get("fence") or {}, at=sc["events_total"], **{"def": sc["scene"].get("def")})
        code, out = post(self.url + "/api/do", {"session": "x", "as": "someone-else", "line": act["line"],
                                                "observed": observed, "gesture": secrets.token_hex(6)},
                         token=token, headers={"Origin": self.url})
        self.assertEqual(code, 200, out)
        return out

    def test_a_lens_made_by_a_line_paints_kernel_things_and_takes_presses(self):
        lens = self.do(self.alex, f'make kind=lens name=feed text={quoted(FEED)}')["made"][0]
        self.assertEqual(self.k.state.get(lens, "text"), FEED)
        p = self.do(self.maya, "post Council meets Tuesday at 7")["made"][0]
        q = self.do(self.alex, f"post Organizers only: bring the projector in={self.group}")["made"][0]
        sc = self.scene(self.maya)
        self.assertIn("Council meets Tuesday at 7", sc["text"])
        self.assertNotIn("projector", sc["text"])                    # who sees, through the compiler too
        self.assertIn("projector", self.scene(self.alex)["text"])
        n = self.k.facade_num = int(p[2:])
        out = self.press(self.maya, sc, f"a{n * 8}/l")              # Maya presses ♥ on her own post
        self.assertIsNone(out["error"], out["text"])
        self.assertEqual(out["line"], f"do like {p}")
        self.assertEqual(out["as"], "Maya")                          # the session decides, never the body's `as`
        self.assertIn("♥ 1", self.scene(self.alex)["text"])
        refused = self.press(self.maya, sc, f"a{n * 8}/p")          # she may not pin
        self.assertIn("pin is for leaders", refused["error"])
        del q

    def test_a_press_painted_before_a_change_to_what_it_read_is_refused(self):
        self.do(self.alex, f'make kind=lens name=feed text={quoted(FEED)}')
        p = self.do(self.maya, "post A post two leaders will pin")["made"][0]
        n = int(p[2:])
        painted = self.scene(self.alex)
        self.do(self.maya, f"like {p}")                              # a like moves the post, but not what pin reads
        self.assertIsNone(self.press(self.alex, painted, f"a{n * 8}/p")["error"])
        self.do(self.alex, "undo")                                   # the pin taken back: `pinned` changed since paint
        out = self.press(self.alex, painted, f"a{n * 8}/p")
        self.assertIn("stale", out["error"])
        self.assertIn("pinned", out["error"])
        fresh = self.scene(self.alex)
        self.assertIsNone(self.press(self.alex, fresh, f"a{n * 8}/p")["error"])

    def test_the_rest_of_what_lens_js_asks(self):
        self.do(self.alex, f'make kind=lens name=feed text={quoted(FEED)}')
        v = json.loads(urllib.request.urlopen(self.url + "/api/version", timeout=10).read())
        self.assertEqual(v["shape"], 1)
        st = self.get("/api/style?name=calm", self.alex)
        self.assertIn("looks", st)
        html = urllib.request.urlopen(self.url + "/lens.html", timeout=10).read().decode()
        self.assertIn("lens.js", html)
        self.assertEqual(urllib.request.urlopen(self.url + "/lens.js", timeout=10).read(),
                         (NOTATION / "desk-shell" / "lens.js").read_bytes())          # served unchanged
        with self.assertRaises(urllib.error.HTTPError):
            urllib.request.urlopen(self.url + "/../keep/seal.key", timeout=10)
        sc = self.scene(self.alex)
        again = self.get(f"/api/scene?lens=feed&view=painter&text=1&have={sc['gen']}", self.alex)
        self.assertTrue(again.get("same"))
        # the stream says `world` for the next record
        req = urllib.request.Request(self.url + "/door/stream", headers={"Authorization": f"Bearer {self.alex}"})
        got = []

        def listen():
            with urllib.request.urlopen(req, timeout=20) as r:
                for line in r:
                    if line.startswith(b"event: world"):
                        got.append(line)
                        return
        t = threading.Thread(target=listen, daemon=True)
        t.start()
        time.sleep(0.5)
        self.do(self.maya, "post a post the stream should hear")
        t.join(10)
        self.assertEqual(len(got), 1)

    def test_nothing_is_written_into_the_desks_folder(self):
        self.do(self.alex, f'make kind=lens name=feed text={quoted(FEED)}')
        self.do(self.maya, "post one")
        self.scene(self.alex)
        self.get("/api/style?name=calm", self.alex)
        newer = [str(p) for p in NOTATION.rglob("*") if p.is_file() and p.stat().st_mtime > self.t0
                 and "sessions" not in p.parts and "house-state" not in p.parts and "reaches" not in p.parts]
        self.assertEqual(newer, [], "the painter wrote into research/text-desk-lab/notation")


if __name__ == "__main__":
    unittest.main()
