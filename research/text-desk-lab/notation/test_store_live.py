"""test_store_live (7 Oct 2026): the log through the two doors a world is changed by, as real processes.

    python test_store_live.py       (also run by test_store.py without --quick)

Saves the rooms world as sessions/roomworld-store-<pid>-try.pickle, begins its log, and then:

  - the CLI (explore.py, one process per call, several people): every line one record, the log and the world agree;
  - a fork takes the log with it and goes on from the same records;
  - deskd (one process, many requests at once): six people act at the same time for a while: chat lines, cards,
    paragraphs of one document, one lens. Every press that changed the world is one record and no more (a press sent
    twice is one), the log replayed says what the world says, and nothing was written outside a record;
  - a server killed while people are writing: when it is back, the log and the world still agree.

The world, its lock, its log and its forks are removed at the end.
"""
import json
import os
import pickle
import random
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:      # noqa: BLE001
    pass

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:2500]}"))
    if not ok:
        fails.append(name)


import explore     # noqa: E402
import roomworld   # noqa: E402
import store       # noqa: E402

WORLD = f"roomworld-store-{os.getpid()}-try"
SESS = HERE / "sessions"
SAVED = SESS / f"{WORLD}.pickle"
LOG = store.Log(store.log_path(SAVED))
ENV = dict(os.environ, DESKD="off", PYTHONIOENCODING="utf-8")

D, R = roomworld.build()
D._session = WORLD
explore.save_desk(SAVED, D)


def world():
    explore.take_lock(SESS / f"{WORLD}.lock")
    try:
        return pickle.loads(SAVED.read_bytes()).world
    finally:
        explore.release_lock(SESS / f"{WORLD}.lock")


def agrees(label, name=WORLD):
    r = subprocess.run([sys.executable, "store.py", "check", name], cwd=HERE, env=ENV, capture_output=True, text=True, encoding="utf-8")
    check(label, r.returncode == 0, r.stdout[-1500:] + r.stderr[-800:])


def cli(who, *lines, name=WORLD):
    r = subprocess.run([sys.executable, "explore.py", name, "--as", who, "--whole"], input="\n".join(lines) + "\n", cwd=HERE, env=ENV,
                       capture_output=True, text=True, encoding="utf-8")
    return r.stdout + r.stderr


try:
    # ---- the CLI ---------------------------------------------------------------------------------------------------
    out = cli("alex", f"look {R.BOARD} :3", f"do prop {R.CARDS[0]} status=before-the-log")
    check("a world without a log is changed as ever, and gets no log", "ok" in out and not LOG.exists(), out[-400:])
    r = subprocess.run([sys.executable, "store.py", "begin", WORLD, "test"], cwd=HERE, env=ENV, capture_output=True, text=True, encoding="utf-8")
    check("store.py begin starts its log", r.returncode == 0 and LOG.exists() and LOG.head()[0] == 1, r.stdout + r.stderr)
    out = cli("alex", f"look {R.BOARD} :3", f"do prop {R.CARDS[0]} status=doing", f'do append {R.TALK[R.BOARD]} line="started"')
    out += cli("sable", f"look {R.BOARD} :3", f'do create {R.BOARD} kind=note title="From the CLI" text="one\\ntwo"', "look", "find card")
    out += cli("pike", f"go {R.LOUNGE} :1", f'do append {R.TALK[R.LOUNGE]} line="hello from pike"')
    recs = [rec for rec, _ in LOG.records()]
    check("through the CLI, every line that changed the world is one record (reads and walking none)",
          [r_["by"] for r_ in recs[1:]] == ["alex", "alex", "sable", "pike"] and "ERR" not in out, ([r_.get("words") for r_ in recs[1:]], out[-600:]))
    agrees("and the log replayed says what the saved world says")
    out = cli("alex", "worktree fork sketch")
    fork = f"{WORLD}@sketch"
    flog = store.Log(store.log_path(SESS / f"{fork}.pickle"))
    check("a fork takes the log with it", flog.exists() and flog.head() == LOG.head(), out[-300:])
    cli("alex", f"look {R.BOARD} :3", f"do prop {R.CARDS[1]} status=in-the-fork", name=fork)
    cli("sable", f"look {R.BOARD} :3", f"do prop {R.CARDS[1]} status=at-home")
    tail_f = [rec for rec, _ in flog.records()][len(recs):]
    check("and goes on from the same records: its own are a tail after the base's, readable as facts",
          len(tail_f) == 1 and [f[1] for f in store.facts_of(tail_f[0])] == ["prop:status"] and store.facts_of(tail_f[0])[0][2] == "in-the-fork", tail_f)
    agrees("the fork's log says what the fork's world says", fork)
    agrees("and home's says what home's says")

    # ---- deskd: many people at once ----------------------------------------------------------------------------------
    def free_port():
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        p = s.getsockname()[1]
        s.close()
        return p

    def start():
        port = free_port()
        p = subprocess.Popen([sys.executable, "deskd.py", str(port)], cwd=HERE, env=ENV, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        url = f"http://127.0.0.1:{port}"
        for _ in range(100):
            try:
                urllib.request.urlopen(url + "/api/health", timeout=2).read()
                return p, url
            except Exception:      # noqa: BLE001
                time.sleep(0.1)
        raise RuntimeError("deskd did not start")

    def do(url, who, line, press=None, timeout=120):
        body = json.dumps({"session": WORLD, "as": who, "line": line, "whole": True, **({"gesture": press} if press else {})}).encode("utf-8")
        with urllib.request.urlopen(urllib.request.Request(url + "/api/do", body, {"Content-Type": "application/json"}), timeout=timeout) as f:
            return json.loads(f.read().decode("utf-8"))

    proc, URL = start()
    r = do(URL, "alex", f"look {R.HOME} :2")
    r = do(URL, "alex", f'do create {R.HOME} kind=surface title="The document" layout=column')
    DOC = r["created"][0]
    paras = []
    for i in range(6):
        do(URL, "alex", f"look {DOC} :1")
        paras.append(do(URL, "alex", f'do create {DOC} kind=note title=p{i} text="paragraph {i}, first draft"')["created"][0])
    do(URL, "alex", f"look {R.HOME} :2")
    lens_text = "root : column\\n" + "\\n".join(f'  part{i} : text \\"part {i}\\"' for i in range(6))
    LENS = do(URL, "alex", f'do create {R.HOME} kind=note tags=lens title=shared-lens text="{lens_text}"')["created"][0]
    n0 = LOG.head()[0]
    PEOPLE = ["alex", "sable", "juniper", "pike", "rowan", "ibis"]
    done, refused, twice, errors = [], [], [], []
    lock = threading.Lock()

    def person(k, who):
        rnd = random.Random(k)
        mine_para, my_part = paras[k], f"part{k}"
        made = None
        for step in range(14):
            kind = rnd.choice(["line", "line", "para", "para", "lens", "card", "prop", "press-twice", "read"])
            try:
                if kind == "line":
                    r = do(URL, who, f'do append {R.TALK[R.LOUNGE]} line="{who} says {step}"')
                elif kind == "para":       # each person writes their own paragraph of the one document
                    do(URL, who, f"read {mine_para}")
                    r = do(URL, who, f'do rewrite {mine_para} text="paragraph {k}, by {who}, draft {step}"')
                elif kind == "lens":       # each person changes their own part of the one lens, having read it some time ago
                    if step < 4 or rnd.random() < 0.3:
                        do(URL, who, f"read {LENS}")
                    cur = world().subjects[world().nodes[LENS]["subject"]]["text"]
                    line = next(l for l in cur.split("\n") if l.strip().startswith(my_part + " :"))
                    r = do(URL, who, 'do replace %s old="%s" new="%s"' % (LENS, line.replace('"', '\\"'),
                                                                        f'  {my_part} : text \\"part {k} by {who} at {step}\\"'))
                elif kind == "card":
                    do(URL, who, f"look {R.BOARD} :1")
                    r = do(URL, who, f'do create {R.BOARD} kind=task title="{who} card {step}" text=x status=open')
                    made = (r.get("created") or [made])[0]
                elif kind == "prop":
                    if not made:
                        continue
                    r = do(URL, who, f"do prop {made} status=step{step}")
                elif kind == "press-twice":
                    press = f"{who}-{step}-{k}"
                    r = do(URL, who, f'do append {R.TALK[R.BOARD]} line="{who} pressed once at {step}"', press)
                    again = do(URL, who, f'do append {R.TALK[R.BOARD]} line="{who} pressed once at {step}"', press)
                    with lock:
                        twice.append(bool(again.get("already")))
                else:
                    do(URL, who, f"look {R.LOUNGE} :2")
                    continue
                with lock:
                    (refused if r.get("error") else done).append((who, kind, r.get("error") or r.get("events")))
            except Exception as e:      # noqa: BLE001
                with lock:
                    errors.append((who, kind, repr(e)))

    t0 = time.time()
    threads = [threading.Thread(target=person, args=(k, who)) for k, who in enumerate(PEOPLE)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    took = time.time() - t0
    recs = [rec for rec, _ in LOG.records()][n0:]
    changed = [d for d in done if d[2]]
    check(f"six people at once through deskd, {len(done)} lines landed in {took:.0f} s: no request failed", not errors, errors[:5])
    check("every line that changed the world is one record, and no record is anyone else's",
          len(recs) == len(changed) and not [r_ for r_ in recs if r_["parts"][0]["cause"] == "outside"],
          (len(recs), len(changed), [r_["parts"][0]["cause"] for r_ in recs if r_["parts"][0]["cause"] != "act"][:5]))
    check("a press sent twice is one record (the second is answered 'already done')", twice and all(twice) and
          len([r_ for r_ in recs if r_.get("press")]) == len(twice), (twice, len([r_ for r_ in recs if r_.get("press")])))
    w = world()
    lens_now = w.subjects[w.nodes[LENS]["subject"]]["text"]
    lens_done = [d for d in done if d[1] == "lens"]
    lens_refused = [d for d in refused if d[1] == "lens"]
    last = {}
    for who, kind, _e in lens_done:
        last[who] = True
    check(f"one lens, six editors each on their own part: {len(lens_done)} edits landed, {len(lens_refused)} were refused; "
          "every editor who landed one has their part in the lens now, and it still has its six parts",
          all(f"by {who} at" in lens_now for who in last) and lens_now.count(" : text ") == 6, (lens_now, lens_refused[:3]))
    joined = sum(1 for r_ in recs if r_["words"].startswith(f"do replace {LENS}") and r_["parts"][0]["verb"] in ("edit",)
                 and (r_.get("saw") or {}))
    para_refused = [d for d in refused if d[1] == "para"]
    check("one document, six writers each in their own paragraph: none was refused", not para_refused, para_refused[:3])
    other = [d for d in refused if d[1] not in ("lens",)]
    check("nothing else was refused either", not other, other[:5])
    agrees("after all of it, the log replayed says what the saved world says")
    print(f"     {len(recs)} records in {took:.1f} s; refused lens edits: {[d[2][:90] for d in lens_refused][:3]}")

    # ---- the server killed while people write ------------------------------------------------------------------------
    stop = threading.Event()
    sent = []

    def writer(who):
        i = 0
        while not stop.is_set():
            try:
                r = do(URL, who, f'do append {R.TALK[R.LOUNGE]} line="{who} keeps writing {i}"', timeout=20)
                sent.append(bool(r.get("events")))
            except Exception:      # noqa: BLE001
                sent.append(None)
                time.sleep(0.05)
            i += 1

    ws = [threading.Thread(target=writer, args=(who,)) for who in PEOPLE[:4]]
    for t in ws:
        t.start()
    time.sleep(2.5)
    proc.kill()
    proc.wait()
    time.sleep(0.5)
    stop.set()
    for t in ws:
        t.join()
    for stale in SESS.glob(f"{WORLD}.lock"):
        pass                                  # a dead holder's lock is taken over by the next one (explore.take_lock)
    proc, URL = start()
    r = do(URL, "alex", f'do append {R.TALK[R.LOUNGE]} line="after the crash"')
    tail = [rec for rec, _ in LOG.records()][-2:]
    lost = [r_ for r_ in tail if r_["parts"][0]["cause"] == "outside"]
    check(f"deskd killed while four people wrote ({sum(1 for s in sent if s)} lines had landed, {sum(1 for s in sent if s is None)} requests failed): "
          "it comes back and takes the next line", not r.get("error") and r.get("events"), r)
    agrees("and the log and the world agree" + (" (a line logged but never saved was taken back by an 'outside' record)" if lost else ""))
    proc.kill()
    proc.wait()
finally:
    try:
        proc.kill()
    except Exception:      # noqa: BLE001
        pass
    time.sleep(0.3)
    for p in list(SESS.glob(f"{WORLD}*")):
        try:
            p.unlink()
        except OSError:
            pass
    import shutil
    shutil.rmtree(HERE / "house-state" / WORLD, ignore_errors=True)

if __name__ == "__main__":
    print()
    print("FAILED: " + "; ".join(fails) if fails else "all passed")
    sys.exit(1 if fails else 0)
