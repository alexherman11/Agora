"""The keeper: the kernel restarts, ports and modules stay (design approved by Alex 28 Oct). Real processes on a
trial world, headless modules: nothing appears on the screen and nothing touches the live desktop (8810).

    C:/Projects/Agora4/.venv/Scripts/python.exe -m pytest -q test_keeper.py   (from this directory)
"""
import json
import subprocess
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
import kdesk_keeper  # noqa: E402


class Trial:
    def __init__(self):
        self.dir = Path(tempfile.mkdtemp(prefix="keeper-test-"))
        self.info = self.dir / "keeper.json"
        self.proc = subprocess.Popen([sys.executable, str(HERE / "kdesk_keeper.py"), "--port", "0",
                                      "--world", str(self.dir / "world"), "--info", str(self.info),
                                      "--log", str(self.dir / "keeper.log"), "--kernel-log", str(self.dir / "kdesk.log"),
                                      "--headless"], creationflags=0x08000000)
        self.wait(lambda: self.info.exists(), 20)
        self.port = json.loads(self.info.read_text())["door"]
        self.url = f"http://127.0.0.1:{self.port}"
        self.wait(lambda: "window.list" in self.say("help all", "alex")["text"]
                  and "window.overlay" in self.say("holds", "alex")["text"], 60)

    def token(self, who):
        sessions = json.loads((self.dir / "world" / "keep" / "sessions.json").read_text(encoding="utf-8"))
        return next(t for t, v in sessions.items() if v.get("signer") == who)

    def say(self, line, who="alex", timeout=20):
        see = line.split()[0] in ("help", "holds", "window.list", "status", "rows", "look")
        req = urllib.request.Request(self.url + ("/see" if see else "/do"), json.dumps({"line": line}).encode(),
                                     {"Content-Type": "application/json", "Authorization": "Bearer " + self.token(who)})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            return {"ok": False, "text": e.read().decode(), "code": e.code}

    def status(self):
        return kdesk_keeper.ask("status", self.info) or {}

    def log(self):
        return (self.dir / "keeper.log").read_text(encoding="utf-8", errors="replace")

    @staticmethod
    def wait(cond, timeout=20):
        end = time.time() + timeout
        last = None
        while time.time() < end:
            try:
                got = cond()
                if got:
                    return got
            except Exception as exc:          # noqa: BLE001
                last = exc
            time.sleep(0.2)
        raise AssertionError(f"timed out waiting ({last!r})")

    def close(self):
        subprocess.run(["taskkill", "/PID", str(self.proc.pid), "/T", "/F"], capture_output=True)


class KeeperTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = Trial()

    @classmethod
    def tearDownClass(cls):
        cls.t.close()

    def steady(self):
        """What must be the same after any kernel restart."""
        s = self.t.status()
        holds = self.t.say("holds")["text"]
        return s["modules"], s["ports"], holds

    def back(self, old_kernel):
        self.t.wait(lambda: self.t.status().get("kernel") not in (None, old_kernel), 60)
        self.t.wait(lambda: "window.list" in self.t.say("help all")["text"]
                    and "window.overlay" in self.t.say("holds")["text"], 60)

    def test_1_restarts_keep_modules_ports_and_holds(self):
        t = self.t
        self.assertTrue(t.say("window.open help")["ok"])
        t.wait(lambda: any(r.get("shows") == "help" for r in t.say("window.list").get("rows") or []))
        modules, ports, holds = self.steady()
        self.assertGreaterEqual(len(modules), 3, modules)
        gaps = []
        for i in range(10):
            old = t.status()["kernel"]
            self.assertTrue(kdesk_keeper.ask("restart-kernel", t.info)["ok"])
            # a request sent while NO kernel is connected waits in the port's queue and is answered by the next one
            t.wait(lambda: t.status().get("kernel") is None, 10)
            began = time.time()
            r = t.say("help all", timeout=60)
            gaps.append(time.time() - began)
            self.assertIn("window.list", r["text"], f"restart {i}: {r}")
            self.back(old)
            m2, p2, h2 = self.steady()
            self.assertEqual(m2, modules, f"restart {i}: module processes changed")
            self.assertEqual(p2, ports, f"restart {i}: ports changed")
            self.assertEqual(sorted(l.split()[0] for l in h2.splitlines() if l.strip()),
                             sorted(l.split()[0] for l in holds.splitlines() if l.strip()), f"restart {i}: holds")
        print(f"\n10 restarts; a request sent mid-restart waited {min(gaps):.1f}-{max(gaps):.1f} s and was answered")
        # a module call goes through the new kernel to the kept module and back
        self.assertTrue(t.say("window.open lines")["ok"])
        t.wait(lambda: any(r.get("shows") == "lines" for r in t.say("window.list").get("rows") or []))

    def test_1b_a_window_keeps_its_page_port(self):
        t = self.t

        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **k):
                return None
        opener = urllib.request.build_opener(NoRedirect)

        def origin(wid):
            req = urllib.request.Request(f"{t.url}/desk/window-origin?win={wid}&next=/desk/help.html",
                                         headers={"Authorization": "Bearer " + t.token("alex")})
            try:
                opener.open(req, timeout=20)
            except urllib.error.HTTPError as e:
                return e.headers.get("Location")
        wid = next(r["id"] for r in t.say("window.list")["rows"] if r.get("shows") == "help")
        before = t.wait(lambda: origin(wid))
        self.assertNotIn(f":{t.port}/", before)                     # its own port, not the door's
        old = t.status()["kernel"]
        kdesk_keeper.ask("restart-kernel", t.info)
        self.back(old)
        self.assertEqual(origin(wid), before)                       # same port after the restart
        with urllib.request.urlopen(before.split("/desk/")[0] + "/desk/help.html", timeout=20) as r:
            self.assertEqual(r.status, 200)                         # and the new kernel answers on it

    def test_1c_no_request_fails_across_restarts(self):
        t = self.t
        done, results = threading.Event(), []

        def hammer():
            while not done.is_set():
                try:
                    results.append("window.list" in t.say("help all", timeout=60)["text"])
                    s = t.say("status window", timeout=60)["text"]          # needs the kept module itself
                    results.append(True if "on the screen" in s else s)
                except Exception as exc:          # noqa: BLE001
                    results.append(repr(exc))
        threads = [threading.Thread(target=hammer) for _ in range(3)]
        for th in threads:
            th.start()
        for _ in range(3):
            old = t.status()["kernel"]
            kdesk_keeper.ask("restart-kernel", t.info)
            self.back(old)
        done.set()
        for th in threads:
            th.join(70)
        bad = [r for r in results if r is not True]
        print(f"\n{len(results)} requests across 3 restarts; {len(bad)} failed {bad[:3]}")
        self.assertEqual(bad, [])

    def test_2_a_kernel_that_dies_is_started_again_and_modules_stay(self):
        t = self.t
        modules, ports, _ = self.steady()
        for _ in range(2):                    # killed hard, twice, as soon as it is up
            old = t.status()["kernel"]
            subprocess.run(["taskkill", "/PID", str(old), "/F"], capture_output=True)
            self.back(old)
        m2, p2, _ = self.steady()
        self.assertEqual((m2, p2), (modules, ports))
        self.assertIn("kernel ended by itself", t.log())

    def test_3_off_module_still_stops_it_and_on_starts_a_new_one(self):
        t = self.t
        before = t.status()["modules"]
        mid = next(iter(before))
        name = next(r["name"] for r in t.say("rows module")["rows"] if r["id"] == mid)
        self.assertTrue(t.say(f"off {name}")["ok"])
        t.wait(lambda: mid not in t.status()["modules"], 15)
        self.assertTrue(t.say(f"on {name}")["ok"])
        t.wait(lambda: mid in t.status()["modules"], 40)
        self.assertNotEqual(t.status()["modules"][mid], before[mid])

    def test_4_killing_the_keeper_ends_everything(self):
        t = Trial()
        pids = list(t.status()["modules"].values()) + [t.status()["kernel"]]
        t.close()
        time.sleep(2)
        out = subprocess.run(["powershell", "-NoProfile", "-Command",
                              "(Get-Process -Id " + ",".join(map(str, pids)) + " -ea 0).Count"],
                             capture_output=True, text=True).stdout.strip()
        self.assertEqual(out or "0", "0", f"left running: {out}")
        with self.assertRaises(Exception):
            urllib.request.urlopen(t.url + "/health", timeout=2)


if __name__ == "__main__":
    unittest.main()
