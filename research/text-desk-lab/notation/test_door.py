"""test_door (a1505): the door keeps one address while deskd is swapped behind it, and nothing is lost or doubled.

    python test_door.py

Builds the rooms world (roomworld.py), saves it as sessions/roomworld-door-<pid>-try.pickle, and starts door.py on a
free port with its own state directory (both removed after). While a page's stream is open and lines are posted with
gesture ids every 40 ms, it swaps deskd three times and tries one swap whose deskd never starts. Then:
  - every gesture made exactly one event (Sable c1538: a send at the switch is neither lost nor replayed);
  - the stream's ids run without a gap or a duplicate and reach the world's count;
  - the refused swap left the running code in place, and the news says why;
  - the news lists each swap, and a door started again on the same state still has them.
No browser: screen.py's `land` steps look at the same thing on a painted page.
"""
import json
import os
import pickle
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

import roomworld   # noqa: E402

WORLD = f"roomworld-door-{os.getpid()}-try"
fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1500]}"))
    if not ok:
        fails.append(name)


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def get(url, timeout=60):
    with urllib.request.urlopen(url, timeout=timeout) as f:
        return json.loads(f.read())


def post(url, body, timeout=300):
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as f:
        return json.loads(f.read())


t0 = time.time()
D, R = roomworld.build()
D._session = WORLD
saved = HERE / "sessions" / f"{WORLD}.pickle"
saved.write_bytes(pickle.dumps(D))
# 14 Oct (Snappy Desk): with a log, as frontier has, a deskd keeps the world in memory and the swaps hand it over
subprocess.run([sys.executable, "store.py", "begin", WORLD, "test"], cwd=HERE, capture_output=True, check=True)
state = tempfile.mkdtemp(prefix="test-door-")
port = free_port()
base = f"http://127.0.0.1:{port}"
door = None


def start_door():
    p = subprocess.Popen([sys.executable, "door.py", str(port), "--no-git", "--state", state], cwd=HERE,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t = time.time() + 60
    while time.time() < t:
        try:
            if get(base + "/door/status", 3).get("up"):
                return p
        except OSError:
            time.sleep(0.2)
    raise SystemExit("test_door: the door did not answer within 60 s")


try:
    door = start_door()
    total0 = get(f"{base}/api/events?session={WORLD}&since=999999999")["total"]

    ids, stop, heard = [], threading.Event(), threading.Event()

    def listen():
        """A page's stream, read as EventSource would: id lines, then the event's data."""
        try:
            read_stream()
        except OSError:
            pass                               # the door was stopped under it, at the end

    def read_stream():
        with urllib.request.urlopen(f"{base}/door/stream?session={WORLD}&since={total0}", timeout=120) as f:
            eid = None
            for raw in f:
                line = raw.decode("utf-8").rstrip("\n")
                if line.startswith("id: "):
                    eid = int(line[4:])
                elif line.startswith("event: world") and eid is not None:
                    ids.append(eid)
                elif not line:
                    eid = None
                if heard.is_set():
                    return

    sent, answers = [], []

    def fire():
        k = 0
        while not stop.is_set():
            k += 1
            g = f"door-test-{os.getpid()}-{k}"
            sent.append(g)
            try:
                r = post(base + "/api/do", {"session": WORLD, "as": "pike", "gesture": g,
                                             "line": f"look {R.SHELF} :1; do create {R.SHELF} kind=note title=\"tick {k}\""})
                answers.append((g, r.get("error"), r.get("code")))
            except OSError as e:
                answers.append((g, f"lost: {e}", None))
            time.sleep(0.04)

    threads = [threading.Thread(target=listen, daemon=True), threading.Thread(target=fire, daemon=True)]
    for t in threads:
        t.start()
    time.sleep(1)
    swaps = []
    for n in (1, 2):
        swaps.append(post(base + "/door/swap", {"code": f"test-{n}", "commits": [["000000" + str(n), f"land a{n}: swap {n}"]]}))
        time.sleep(0.5)
    bad = post(base + "/door/swap", {"code": "test-broken", "argv": ["-c", "raise SystemExit('broken on purpose')"]})
    time.sleep(0.5)
    swaps.append(post(base + "/door/swap", {"code": "test-3", "commits": [["0000003", "land a3: swap 3"]]}))
    time.sleep(1.5)
    stop.set()
    threads[1].join(30)
    time.sleep(3)                              # the stream's last polls
    heard.set()

    check("three swaps were made", [s["ok"] for s in swaps] == [True, True, True], swaps)
    check("a deskd that never starts is refused, and the running one kept",
          not bad["ok"] and bad["code"] == "test-2" and "broken on purpose" in (bad["why"] or ""), bad)
    evs = get(f"{base}/api/events?session={WORLD}&since={total0}")
    made = {}
    for e in evs["events"]:
        if e.get("gesture"):
            made[e["gesture"]] = made.get(e["gesture"], 0) + 1
    errors = [a for a in answers if a[1]]
    check(f"every gesture sent across the swaps made exactly one event ({len(sent)} sent)",
          len(sent) > 50 and all(made.get(g) == 1 for g in sent) and not errors,
          {"none": [g for g in sent if g not in made][:5], "twice": [g for g, c in made.items() if c > 1][:5], "errors": errors[:5]})
    check("receipts name the code that answered them, and more than one did (vii)",
          len({a[2] for a in answers if a[2]}) >= 3, sorted({str(a[2]) for a in answers}))
    gaps = [(a, b) for a, b in zip(ids, ids[1:]) if b != a + 1]
    check(f"the stream's ids run without a gap or a duplicate to the world's count ({len(ids)} events)",
          ids and ids[0] == total0 + 1 and not gaps and ids[-1] == evs["total"], {"first": ids[:3], "last": ids[-3:], "gaps": gaps[:5], "total": evs["total"]})
    st = get(base + "/door/status")
    news = st["news"]
    check("the news has the three swaps and the refusal, in order",
          [(n["to"], n["ok"]) for n in news] == [("test-1", True), ("test-2", True), ("test-broken", False), ("test-3", True)]
          and news[-1]["commits"] == [["0000003", "land a3: swap 3"]], news)
    door.terminate()
    door.wait()
    time.sleep(3.5)                            # its deskd goes on its own (DESKD_PARENT)
    door = start_door()
    check("a door started again on the same state still has the day's news",
          [n["to"] for n in get(base + "/door/status")["news"]] == ["test-1", "test-2", "test-broken", "test-3"])
    again = get(f"{base}/api/events?session={WORLD}&since={total0}")
    check("and the world it reads has every event the stopped one answered (it was held in memory, and saved going)",
          again["total"] == evs["total"] and all(any(e.get("gesture") == g for e in again["events"]) for g in made),
          (again["total"], evs["total"]))
    r = subprocess.run([sys.executable, "store.py", "check", WORLD], cwd=HERE, capture_output=True, text=True, encoding="utf-8")
    check("and its log and its file agree", r.returncode == 0, r.stdout[-800:] + r.stderr[-400:])
finally:
    if door is not None:
        door.terminate()
        door.wait()
        time.sleep(3.5)
    for p in (saved, saved.with_suffix(".lock"), saved.with_suffix(".writer"), *saved.parent.glob(f"{WORLD}.log.jsonl*"),
              *saved.parent.glob(f"{WORLD}.undo*")):
        p.unlink(missing_ok=True)
    shutil.rmtree(state, ignore_errors=True)

print(f"{len(fails)} failed" if fails else "all passed", f"({time.time() - t0:.0f} s, world {WORLD})")
sys.exit(1 if fails else 0)
