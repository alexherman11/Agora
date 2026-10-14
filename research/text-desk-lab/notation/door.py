"""door: the front door that stays while deskd changes behind it (a1505, phase 1 of a1483).

    python door.py [port] [--world frontier] [--state DIR] [--no-git] [--static DIR] [--trees DIR]
                                                default port 8794, state house-state/; --static: deskd's static dir

It is meant to change almost never, and imports nothing of the desk's (no deskd, scene or desk), so a landing that
breaks those cannot break it. It:
  - holds the port browsers and the house talk to, and passes every request to the deskd behind it (a private port);
  - when git HEAD moves (unless --no-git), starts a new deskd on the new code, beside the old one. The new one is
    asked /api/health, then every scene the door served in the last two hours (the lenses people have open), built by
    the new process itself, which also fills its cache. If all answer, requests go to the new one from then on, and the
    old one finishes the calls it was answering before it is stopped. If not, the old one stays, the new one is
    stopped, and the door says why in its news;
  - answers /door/stream: a page's one long connection (Server-Sent Events). It carries the world's events, each with
    its index as its id, and the door's news. The door reads events from whichever deskd is current, so a swap is not
    seen on the stream: no gap, no duplicate. A page that reconnects says the last id it saw (Last-Event-ID);
  - answers /door/status (the code running, the news) and, to local programs only, POST /door/swap (swap now; a test
    may give the new deskd's argv and env);
  - keeps its news (each swap: when, from, to, the commits in between, whether the painter's own files changed, or why
    it was refused) in <state>/door.json, so a page opened in the evening can say what changed that day.
  - a2844, visits: answers two words itself, `visit <commission>` and `home`, each sent as a line of its own to
    /api/do. `visit <commission>` (a commission with a living worktree under .worktrees/, or --trees DIR) pins that
    worktree's commit as it is now: the lab's files at that commit are taken out of git into <state>/visits/, home's
    world is copied beside them under its lock, and a deskd is started there; from then on that actor's /api/do lines
    go to it, and each receipt ends `~ in <commission>@<commit>, not home`. A version that does not start, or cannot
    open the world, refuses entry with its last words. Someone already in the same commit is joined; when others are in
    an earlier commit the door does not pick: `visit <commission> with=<name>` joins theirs, `visit <commission> new`
    takes the newest. `visit` alone says who is where. `home` routes the actor back and says what they leave behind;
    the version is stopped and its folder removed when nobody is in it. A version that dies brings its visitors home:
    each one's next line is refused, told, and run nowhere. A worker's later commit is said once on the next receipt;
    `visit <commission>` again pins the new commit and names the commits since. Who is away is kept in <state>/visits.json (scene.py and rooms.py show it; explore.py
    refuses an away actor's line when no door answers); a door started again brings everyone home, told.
  - a3204, after the first visit was lived: a version's reply OPENS with `[in <commission>@<commit>, not home]` (after
    ERR or MISS when it is a refusal). The word that a version died is said once to each person who was in it, on a
    line whose answer they see: their own next line (refused, run nowhere) or their wake. The house marks the lines it
    sends signed as a resident (by=house, kind=rest|wake): its rest line does not take the word and runs at home; a
    wake runs at home and opens with it. The version's last words are quoted only when they are an error. When the
    visited code is behind home's, the entry line names the newest landings it lacks (from git) and says that a view
    there may show less than home's. `home` counts the lines written home. `write home <words>`,
    from inside a visit, is answered by the door: it writes one comment on the visited commission at home, signed by
    the visitor and labelled with the version; the single thing a visit writes in home's store.
A request that could not reach a deskd at all (refused: it never arrived) is sent again to the current one; so is a
POST /api/do carrying a gesture id, since deskd acts once per id (a1008) and the ids live in the shared world.
Log: <state>/door.log; each deskd's output: <state>/deskd.out.
"""
import http.client
import json
import os
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
NOTATION = HERE.relative_to(REPO).as_posix()      # where the lab is in any checkout: research/text-desk-lab/notation
PY = sys.executable
HOP = {"connection", "keep-alive", "transfer-encoding", "te", "trailer", "upgrade", "proxy-authorization",
       "proxy-authenticate", "host", "content-length", "origin", "sec-fetch-site", "sec-fetch-mode", "sec-fetch-dest"}


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def git(*args):
    try:
        return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception:
        return ""


def ask(port, path, timeout=10.0, method="GET", body=None, headers=None):
    """One request to a deskd. -> (status, headers, body bytes); raises OSError when it can't be reached."""
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    try:
        c.request(method, path, body=body, headers=headers or {})
        r = c.getresponse()
        return r.status, r.getheaders(), r.read()
    finally:
        c.close()


class Backend:
    """One deskd process behind the door."""

    def __init__(self, door, code, argv=None, env=None):
        self.port, self.code, self.busy, self.started = free_port(), code, 0, time.time()
        self.lock = threading.Lock()
        out = open(door.state / "deskd.out", "a", encoding="utf-8")
        out.write(f"--- {time.strftime('%Y-%m-%d %H:%M:%S')} door starts deskd {code} on {self.port}\n")
        out.flush()
        cmd = [PY, *(argv or ["deskd.py"]), str(self.port), *([door.static] if door.static and not argv else [])]
        self.proc = subprocess.Popen(cmd, cwd=HERE, env={**os.environ, "DESKD_CODE": code, "DESKD_PARENT": str(os.getpid()), **(env or {})},
                                     stdout=out, stderr=subprocess.STDOUT)
        self.painter = None

    def alive(self):
        return self.proc.poll() is None

    def enter(self):
        with self.lock:
            self.busy += 1

    def leave(self):
        with self.lock:
            self.busy -= 1

    def stop(self, wait_busy=120.0):
        """The old one finishes the calls it is answering, then goes."""
        t = time.time() + wait_busy
        while self.busy > 0 and time.time() < t and self.alive():
            time.sleep(0.1)
        if self.alive():
            # Snappy Desk (14 Oct): a deskd keeps the worlds it holds in memory and saves them in the background; it is
            # asked to save them and let go before it is stopped (what it has not saved is on the log either way)
            try:
                ask(self.port, "/api/release", method="POST", body=json.dumps({"all": True}).encode(),
                    headers={"Content-Type": "application/json"}, timeout=30)
            except Exception:      # noqa: BLE001
                pass
            self.proc.terminate()
            try:
                self.proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                self.proc.kill()


def git_in(tree, *args):
    """git in a commission's worktree. -> (ok, stdout); the door types git so that no resident does."""
    try:
        r = subprocess.run(["git", *args], cwd=tree, capture_output=True, text=True, timeout=30)
        return r.returncode == 0, r.stdout.strip()
    except Exception:
        return False, ""


SECRET = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")


def copy_locked(src, to, wait=30.0):
    """Copy a world under its own lock, as every writer of it holds it (explore.take_lock: sessions/<name>.lock, made
    exclusively, holding its owner's pid), so the copy is never of a half-made save and never has the file open while a
    save renames over it (1 Oct: a bare copy made the live world drop saves). -> None, or why not."""
    import shutil
    lock, t = src.with_suffix(".lock"), time.time() + wait
    while True:
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except (FileExistsError, PermissionError):
            if time.time() > t:
                return f"its lock was held for {int(wait)} s"
            time.sleep(0.05)
    try:
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        shutil.copyfile(src, to)
        return None
    except OSError as e:
        return str(e)
    finally:
        for _ in range(200):
            try:
                lock.unlink(missing_ok=True)
                break
            except PermissionError:
                time.sleep(0.01)


class Version:
    """A pinned version (a2844): one commission's lab code at one commit, taken out of git into the door's own folder,
    a copy of home's world made at entry, and a deskd over the two. Nothing in it is a file the worker or home uses, so
    the worker's later commits and tests don't touch a visit, and a visit touches nothing of theirs."""

    def __init__(self, door, cid, sha, tree):
        self.door, self.cid, self.sha, self.tree = door, cid, sha, tree
        self.label = f"{cid}@{sha[:7]}"
        self.dir = door.state / "visits" / f"{cid}-{sha[:7]}-{int(time.time() * 1000) % 10 ** 9}"
        self.out = self.dir.with_name(self.dir.name + ".out")
        self.port, self.proc, self.total, self.origin = free_port(), None, None, ""     # origin: the copy's last event
        self.made, self.first = time.strftime("%H:%M"), ""         # when the world was copied, and for whom
        self.visitors, self.lines, self.since = set(), {}, {}      # who is in; each one's count of lines, and since when
        self.told, self.asked, self.head = {}, 0.0, sha            # which later head each visitor was told of
        self.wrote = {}                                            # a3204: each visitor's count of lines written home

    def alive(self):
        return self.proc is not None and self.proc.poll() is None

    def last_words(self, n=3):
        try:
            lines = [l for l in self.out.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
        except OSError:
            return ""
        return " | ".join(l.strip()[:200] for l in lines[-n:])

    def start(self, timeout=90.0):
        """-> None once its deskd answers health and has loaded the world copy with its own code; else why not."""
        import io
        import tarfile
        try:
            r = subprocess.run(["git", "archive", "--format=tar", self.sha, NOTATION], cwd=self.tree, capture_output=True, timeout=120)
        except Exception as e:
            return f"could not be read out of git ({type(e).__name__}: {e})"
        if r.returncode:
            return "could not be read out of git: " + (r.stderr.decode("utf-8", "replace").strip()[-200:] or "no detail")
        self.dir.mkdir(parents=True)
        root = self.dir.resolve()
        with tarfile.open(fileobj=io.BytesIO(r.stdout)) as tar:
            for m in tar.getmembers():
                rel = m.name[len(NOTATION):].lstrip("/")
                if not m.name.startswith(NOTATION) or not rel or not m.isfile() or rel.split("/")[0] in ("sessions", "house-state"):
                    continue                      # no world from git: the only world here is the copy made below
                to = (root / rel).resolve()
                if root not in to.parents:
                    continue
                to.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(m) as f:
                    to.write_bytes(f.read())
        (self.dir / "sessions").mkdir(exist_ok=True)
        src = HERE / "sessions" / f"{self.door.world}.pickle"
        why = copy_locked(src, self.dir / "sessions" / src.name)
        if why:
            return f"has no world: home's {self.door.world} could not be copied ({why})"
        env = {k: v for k, v in os.environ.items()
               if not any(s in k.upper() for s in SECRET) and not k.upper().startswith(("ANTHROPIC", "CLAUDE", "OPENAI"))}
        out = open(self.out, "a", encoding="utf-8")
        self.proc = subprocess.Popen([PY, "deskd.py", str(self.port)], cwd=self.dir, stdout=out, stderr=subprocess.STDOUT,
                                     env={**env, "DESKD": "off", "DESKD_CODE": self.label, "DESKD_PARENT": str(os.getpid())})
        t = time.time() + timeout
        while True:
            if not self.alive():
                return f"exited ({self.proc.returncode}) before answering: {self.last_words() or 'it said nothing'}"
            try:                                  # any answer will do: code older than a1505 has no /api/health, and
                ask(self.port, "/api/health", timeout=3)      # the real check is the one below
                break
            except OSError:
                pass
            if time.time() > t:
                return f"did not answer within {int(timeout)} s"
            time.sleep(0.2)
        try:                                      # the version's own code must be able to open today's world
            st, _h, body = ask(self.port, "/api/events?" + urlencode({"session": self.door.world, "since": 10 ** 9}), timeout=120)
            self.total = json.loads(body)["total"]
            last = json.loads(ask(self.port, "/api/events?" + urlencode({"session": self.door.world, "since": max(0, self.total - 1)}),
                                  timeout=120)[2])["events"]
            self.origin = str(last[-1]["id"]) if last else "its first event"
        except (OSError, ValueError, KeyError, TypeError, IndexError) as e:
            return f"started, but could not open the world ({type(e).__name__}): {self.last_words() or 'it said nothing'}"
        return None

    def stop(self):
        """Stop its deskd and remove the folder the door made for it."""
        import shutil
        if self.alive():
            self.proc.terminate()
            try:
                self.proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        for _ in range(20):                       # Windows lets go of a stopped process's files a moment later
            shutil.rmtree(self.dir, ignore_errors=True)
            if not self.dir.exists():
                break
            time.sleep(0.25)
        try:
            self.out.unlink(missing_ok=True)
        except OSError:
            pass


def answer(body, text=None, error=None, **more):
    """What the door itself says to a line, in the shape deskd answers /api/do."""
    return {"text": text, "error": error, "line": str(body.get("line", "")), "as": body.get("as") or "alex",
            "created": [], "events": [], "code": "door", **more}


JSON = {"Content-Type": "application/json"}


def labelled(text, label):
    """a3204: a version's reply opens with where it came from. A refusal still begins as one (ERR, MISS: the house and
    explore.py stop the lines after it by that word), and the label follows the word."""
    tag = f"[in {label}, not home]"
    first, _, rest = text.partition(" ")
    return f"{first} {tag} {rest}" if first in ("ERR", "MISS") else f"{tag}\n{text}"


def older(subjects, keep=3):
    """a3204 (2): what a version behind home's code is told at entry. subjects: home's commits it lacks, newest first.
    The landings among them are named from git (Pike c3244: a fact nobody maintains; a hand-kept list of what the
    world holds would rot)."""
    lands = [s[5:].strip() for s in subjects if s.startswith("land ")]
    warn = "a view here may show less than home's, and nothing here says so"
    if not lands:
        return "This code is older than home's: " + warn
    return (f"This code is older than {len(lands)} landing(s) at home, newest first: " + "; ".join(l[:70].rstrip(". ") for l in lands[:keep])
            + (f"; and {len(lands) - keep} more" if len(lands) > keep else "") + ". It does not know what they brought, so " + warn)


def reason(words):
    """a3204 (6), Juniper c3247: a deskd killed from outside leaves no error, and its last output is its banner. Its
    last words are quoted only when they are an error."""
    return f"its last words: {words}" if any(w in words for w in ("Traceback", "Error", "Exception")) else "it gave no reason"


class Door:
    def __init__(self, port, world, state, watch_git, static=None, trees=None):
        self.port, self.world, self.state, self.watch_git, self.static = port, world, Path(state), watch_git, static
        self.state.mkdir(parents=True, exist_ok=True)
        self.trees = Path(trees) if trees else REPO / ".worktrees"
        self.away, self.versions, self.fell = {}, {}, {}     # actor -> Version; (commission, commit) -> Version; actor -> what to tell
        self.last, self.lived = {}, []                       # actor -> {commission: commit last pinned}; the visits made
        self.visiting, self.entering = threading.RLock(), threading.Lock()
        self.visits_begin()
        self.current, self.swapping = None, threading.Lock()
        self.scenes = {}                 # the scene queries pages asked for: query string -> last asked (time)
        self.changed = threading.Condition()
        self.head = git("rev-parse", "HEAD") if watch_git else ""
        try:
            saved = json.loads((self.state / "door.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            saved = {}
        self.news = saved.get("news", [])[-200:]
        self.serial = len(self.news)

    def log(self, msg):
        line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
        print(line, flush=True)
        with (self.state / "door.log").open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def say(self, item):
        item = {"at": time.strftime("%Y-%m-%d %H:%M:%S"), **item}
        with self.changed:
            self.news = (self.news + [item])[-200:]
            self.serial += 1
            self.changed.notify_all()
        try:
            tmp = self.state / "door.json.tmp"
            tmp.write_text(json.dumps({"news": self.news}, ensure_ascii=False, indent=1), encoding="utf-8")
            os.replace(tmp, self.state / "door.json")
        except OSError as e:
            self.log(f"could not keep the news: {e}")

    def status(self):
        b = self.current
        return {"code": b.code if b else None, "painter": b.painter if b else None, "up": bool(b and b.alive()),
                "since": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(b.started)) if b else None,
                "news": self.news[-60:], "serial": self.serial,
                "away": {who: v.label for who, v in list(self.away.items())},
                "versions": {v.label: {"pid": v.proc.pid if v.proc else None, "in": sorted(v.visitors)}
                             for v in list(self.versions.values())}}

    # ---------- starting and swapping ----------
    def healthy(self, b, timeout=90.0):
        """-> None if the new deskd answers health and every recent scene; else why not, in words."""
        t = time.time() + timeout
        while True:
            if not b.alive():
                tail = ""
                try:
                    tail = (self.state / "deskd.out").read_text(encoding="utf-8", errors="replace").strip().splitlines()[-1][:200]
                except (OSError, IndexError):
                    pass
                return f"exited ({b.proc.returncode}) before answering" + (f": {tail}" if tail else "")
            try:
                st, _h, body = ask(b.port, "/api/health", timeout=3)
                if st == 200 and json.loads(body).get("ok"):
                    break
            except (OSError, ValueError):
                pass
            if time.time() > t:
                return f"did not answer health within {int(timeout)} s"
            time.sleep(0.25)
        try:
            b.painter = json.loads(ask(b.port, "/api/version", timeout=10)[2]).get("painter")
        except (OSError, ValueError):
            pass
        old = self.current
        for qs in [q for q, at in sorted(self.scenes.items(), key=lambda x: -x[1]) if time.time() - at < 7200][:6]:
            try:
                new = json.loads(ask(b.port, "/api/scene?" + qs, timeout=60)[2])
            except (OSError, ValueError) as e:
                return f"could not build a scene a page has open ({qs}): {e}"
            if "refused" in new and old is not None and old.alive():
                try:
                    was = json.loads(ask(old.port, "/api/scene?" + qs, timeout=60)[2])
                except (OSError, ValueError):
                    was = {}
                if "refused" not in was:
                    lens = parse_qs(qs).get("lens", ["?"])[0]
                    return f"refuses lens {lens}, which the running code paints: {str(new['refused'])[:160]}"
        return None

    def start_first(self):
        while True:
            code = (git("rev-parse", "--short", "HEAD") if self.watch_git else "") or "dev"
            b = Backend(self, code)
            why = self.healthy(b)
            if why is None:
                self.current = b
                self.log(f"door: deskd {code} answers on {b.port}; the door is on {self.port}")
                return
            self.log(f"door: the first deskd ({code}) failed: {why}; trying again in 30 s")
            b.stop(0)
            time.sleep(30)

    def swap(self, code=None, argv=None, env=None, commits=None, head=None):
        """Start a new deskd beside the current one and switch to it if it is healthy. -> (ok, why)."""
        with self.swapping:
            old = self.current
            code = code or (git("rev-parse", "--short", "HEAD") if self.watch_git else "") or "dev"
            b = Backend(self, code, argv, env)
            why = self.healthy(b)
            if commits is None:
                commits = self.commits(head) if head else []
            dirty = [l[3:] for l in git("status", "--porcelain", "--untracked-files=no").splitlines() if l.endswith(".py")] if self.watch_git else []
            item = {"from": old.code if old else None, "to": code, "commits": commits,
                    **({"dirty": dirty[:8]} if dirty else {})}
            if why is not None:
                b.stop(0)
                self.log(f"door: kept {old.code if old else 'nothing'}; the new deskd ({code}) {why}")
                why = f"the new code ({code}) {why}"
                self.say({**item, "ok": False, "why": why})
                return False, why
            item["painter"] = bool(old and b.painter and old.painter and b.painter != old.painter)
            self.current = b
            self.log(f"door: now deskd {code} on {b.port} (was {old.code if old else '-'}); the old one finishes its calls")
            self.say({**item, "ok": True})
            if old is not None:
                threading.Thread(target=old.stop, daemon=True).start()
            return True, None

    def commits(self, head):
        """The commits between the code that ran and `head`, first parent only, without the docs exports."""
        rng = f"{self.head}..{head}" if self.head else f"-1 {head}"
        out = []
        for l in git("log", "--first-parent", "--format=%h%x09%s", *rng.split()).splitlines()[:20]:
            h, _, s = l.partition("\t")
            if not s.startswith("docs:"):
                out.append([h, s[:140]])
        return out

    def watch(self):
        """git HEAD moving is a landing (or anyone's commit): swap to it. A deskd that died is started again."""
        while True:
            time.sleep(2)
            try:
                if self.watch_git:
                    now = git("rev-parse", "HEAD")
                    if now and now != self.head:
                        self.log(f"door: HEAD moved {self.head[:7]} -> {now[:7]}")
                        self.swap(head=now)
                        self.head = now          # a refused swap is not tried again until HEAD moves again
                b = self.current
                if b is not None and not b.alive() and not self.swapping.locked():
                    self.log(f"door: deskd {b.code} exited ({b.proc.returncode}); starting one again")
                    self.swap(code=b.code, commits=[])
                for v in list(self.versions.values()):      # a2844: a version that died brings its visitors home
                    if not v.alive():
                        self.fall(v)
            except Exception as e:          # the door must not die of anything it watches
                self.log(f"door: watch failed: {type(e).__name__}: {e}")

    def backend(self, wait=30.0):
        t = time.time() + wait
        while time.time() < t:
            b = self.current
            if b is not None and b.alive():
                return b
            time.sleep(0.2)
        return None

    # ---------- visits (a2844): `visit <commission>` and `home` are answered here, never by a version ----------
    def visits_begin(self):
        """A door started again: every version's deskd went with the old door, so whoever was away is home, and is told
        at their next line. What was kept: who last pinned which commit of which commission, and the visits made."""
        import shutil
        try:
            saved = json.loads((self.state / "visits.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            saved = {}
        self.last, self.lived, self.fell = saved.get("last") or {}, (saved.get("lived") or [])[-200:], dict(saved.get("fell") or {})
        for who, a in (saved.get("away") or {}).items():
            self.fell[who] = (f"the door was started again at {time.strftime('%H:%M')} while you were in {a.get('label')}, and that "
                              "version's desk went with it; you are home; nothing of yours ran since")
        shutil.rmtree(self.state / "visits", ignore_errors=True)
        if saved:
            self.visits_save()

    def visits_save(self):
        """<state>/visits.json: who is away and where (home's desk reads it to show them away, and explore.py to refuse
        their lines when the door is down), who is to be told their version died, and the visits made (for a landing
        to compare with what was lived)."""
        with self.visiting:
            data = {"world": self.world, "fell": self.fell, "last": self.last, "lived": self.lived[-200:],
                    "away": {who: {"in": v.cid, "commit": v.sha, "label": v.label, "since": v.since.get(who)}
                             for who, v in self.away.items()}}
            try:
                tmp = self.state / "visits.json.tmp"
                tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
                os.replace(tmp, self.state / "visits.json")
            except OSError as e:
                self.log(f"could not keep the visits: {e}")

    def tree_of(self, word):
        """The living worktree of a commission, or None."""
        word = word.lower()
        if not (len(word) > 1 and word[0].isalpha() and word[1:].isdigit()):
            return None
        tree = self.trees / word
        return tree if (tree / ".git").exists() else None

    def living(self):
        try:
            return sorted(p.name for p in self.trees.iterdir() if self.tree_of(p.name) is not None)
        except OSError:
            return []

    def do(self, body, page=False):
        """A line someone sent. -> the door's own answer (a dict), the Version it goes to, or None: it is home's."""
        who = str(body.get("as") or "alex").split("/")[0].strip().lower()
        line = str(body.get("line", "")).strip()
        parts = [line.split()] if body.get("whole") else [p.split() for p in line.split(";")]
        home = [len(p) == 1 and p[0].lower() == "home" for p in parts]
        go = [bool(p) and p[0].lower() == "visit" for p in parts]
        # a3204 (Pike lived it, 3 Oct; Rowan c1668: never silently): the word that a version died is for the person, and
        # is said once, on a line whose answer they will see. The house sends lines of its own signed as a resident
        # (by=house): its rest line's answer is only logged, so it does not take the word and is run at home, where
        # the resident is; a wake is run at home and opens with the word; their own line is refused and run nowhere
        house = body.get("by") == "house"
        with self.visiting:
            v = self.away.get(who)
            fell = self.fell.pop(who, None) if not house or body.get("kind") == "wake" else None
        if fell:
            self.visits_save()
            if house:
                return self.wake_home(body, who, fell)
            if home == [True]:
                return answer(body, f"[door] {fell}.")
            return answer(body, error=f"[door] {fell}. This line was not run anywhere either: {line[:120]!r}. "
                                      "Send it again if you mean it for home.")
        if v is not None and (line.lower() == "write home" or line.lower().startswith("write home ")):
            return self.write_home(body, who, v, line[10:])
        if (any(home) or any(go)) and len(parts) > 1:
            return answer(body, error="[door] `visit <commission>` and `home` are the door's words: send one as a line of its own. "
                                      "Nothing was run.")
        if home[0]:
            return self.leave(body, who) if v else answer(body, "[door] you are home already, in no version.")
        session = str(body.get("session", "desktop"))
        if go[0]:
            if page:
                return answer(body, error="[door] visiting from a screen is not built yet: the banner that says where you are "
                                          "must be home's, and it isn't there. Nothing was done.")
            if session != self.world:
                return answer(body, error=f"[door] a visit is made from {self.world}, not from {session}. Nothing was done.")
            return self.enter(body, who, [a.lower() for a in parts[0][1:]])
        if v is None:
            return None
        if session != self.world:
            return answer(body, error=f"[door] you are away in {v.label}, where the only world is a copy of {self.world}: a line "
                                      f"for {session} would write home's store from a visit. `home` first. Nothing was run.")
        return v

    def home_do(self, body):
        """One line to home's deskd, sent by the door itself. -> its answer (a dict), or None when none came."""
        b = self.backend(wait=10)
        if b is None:
            return None
        b.enter()
        try:
            r = json.loads(ask(b.port, "/api/do", timeout=300, method="POST", body=json.dumps(body).encode("utf-8"), headers=JSON)[2])
            return r if isinstance(r, dict) else None
        except (OSError, ValueError):
            return None
        finally:
            b.leave()

    def wake_home(self, body, who, fell):
        """The house's wake of someone whose version died: run at home, and its answer opens with the door's word."""
        r = self.home_do(body)
        if r is None:                              # home did not answer: the word is kept for the next line they see
            with self.visiting:
                self.fell.setdefault(who, fell)
            self.visits_save()
            return None
        if r.get("text"):
            r["text"] = f"[door] {fell}.\n{r['text']}"
        else:
            r["error"] = f"{r.get('error')} [door] {fell}."
        return r

    def write_home(self, body, who, v, words):
        """`write home <words>`, from inside a visit (a3204; Juniper e5642, Claude a1960): the one thing a visit writes
        in home's store. The door's own code, never the version's, sends home one comment on the visited commission (the
        one place the door can name without reading a world), signed by the visitor and labelled with the version; a
        line that begins with @name calls them, as any comment does. Home may refuse it, and then nothing is written."""
        words = " ".join(words.split())
        if not words or len(words) > 600:
            return answer(body, error="[door] " + (f"one line home is at most 600 characters; this is {len(words)}" if words else
                                                   "`write home <words>` leaves one line at home, as a comment on "
                                                   f"{v.cid}; begin it with @name to call someone") + ". Nothing was written.",
                          version=v.label)
        said = f"{words} [from {v.label}, {who}]" if words.startswith("@") else f"from {v.label}, {who}: {words}"
        # home's desk refuses an act on a thing its actor has not looked at, so the door looks first, as the visitor
        self.home_do({"session": self.world, "as": who, "whole": True, "line": f"look {v.cid} :1"})
        # home's desk refuses an act on a card its actor has not looked at, or that changed since: the door looks first
        self.home_do({"session": self.world, "as": who, "whole": True, "line": f"look {v.cid} :1"})
        r = self.home_do({"session": self.world, "as": who, "whole": True,
                          "line": f"do comment {v.cid} line=" + json.dumps(said, ensure_ascii=False)})
        if r is None:
            return answer(body, error="[door] home's desk did not answer, so whether the line was written there is not known. "
                                      f"You are still in {v.label}.", version=v.label)
        text = str(r.get("text") or "")
        if r.get("error") or not text or text.startswith(("ERR", "MISS")):
            return answer(body, error=f"[door] home refused the line, so nothing was written home: {str(r.get('error') or text)[:300]}. "
                                      f"You are still in {v.label}.", version=v.label)
        made = text.partition("created ")[2].split(" ")[0].strip() if "created c" in text else ""
        with self.visiting:
            v.wrote[who] = v.wrote.get(who, 0) + 1
        self.log(f"door: {who} wrote home from {v.label}: {said[:200]}")
        return answer(body, f"[door] written home{' as ' + made if made else ''}, a comment on {v.cid}: {said!r}. It is the one thing a "
                            f"visit writes at home, and the door wrote it, not {v.label}'s code. You are still in {v.label}; nothing "
                            "else you do here reaches home.", version=v.label)

    def enter(self, body, who, args):
        """`visit <commission> [new | with=<name>]`: pin the commission's worktree at its commit as it is now (or join
        the version someone is in), and send this actor's lines there from now on. `visit` alone says who is where."""
        with self.visiting:
            now = "; ".join(f"{', '.join(sorted(v.visitors))} in {v.label}" for v in self.versions.values() if v.visitors)
        usage = ("`visit <commission>` takes you into that commission's code as its worker last committed it, on a copy of "
                 f"{self.world} made as you enter; `home` brings you back. Commissions with a living worktree: "
                 f"{', '.join(self.living()) or 'none'}. Away now: {now or 'nobody'}")
        if not args:
            return answer(body, f"[door] {usage}.")
        cid, opt = args[0], args[1:]
        tree = self.tree_of(cid)
        new, mate = opt == ["new"], opt[0][5:] if len(opt) == 1 and opt[0].startswith("with=") and opt[0][5:] else None
        if tree is None or (opt and not new and mate is None):
            return answer(body, error=f"[door] " + (f"no commission {cid} has a living worktree to visit" if tree is None else
                                                    f"visit {cid} takes `new` or `with=<name>`, not {' '.join(opt)!r}")
                                      + f". Nothing was changed. {usage}.")
        ok, sha = git_in(tree, "rev-parse", "HEAD")
        if not ok or not sha:
            return answer(body, error=f"[door] {cid}'s worktree has no commit git can name; nothing was changed.")
        with self.entering:                        # one entry at a time: two who come together share one version
            with self.visiting:
                cur = self.away.get(who)
                there = [v for v in self.versions.values() if v.cid == cid and v.alive() and v.visitors - {who}]
            if mate is not None:
                ver = next((v for v in there if mate in v.visitors), None)
                if ver is None:
                    return answer(body, error=f"[door] {mate} is not in {cid}. Nothing was changed. {usage}.")
                sha = ver.sha
            else:
                # Juniper c3167: the worker committed between two entries, so `visit` alone would put each of them in a
                # version of their own, puzzled. The door doesn't pick: it says who is where and names both ways in
                apart = [v for v in there if v.sha != sha]
                if apart and not new:
                    said = "; ".join(f"{', '.join(sorted(v.visitors - {who}))} in {v.label} (world from {v.origin}, copied at {v.made})"
                                     for v in apart)
                    at = next((v for v in there if v.sha == sha), None)
                    return answer(body, error=f"[door] {cid} is at {sha[:7]} now"
                                              + (f", where {', '.join(sorted(at.visitors - {who}))} is" if at else "")
                                              + f", and others are in an earlier commit of it: {said}. `visit {cid} with=<name>` joins "
                                              f"theirs; `visit {cid} new` takes {sha[:7]}. Nothing was changed.")
                with self.visiting:
                    ver = self.versions.get((cid, sha))
            if cur is not None and cur is ver and ver.alive():
                return answer(body, f"[door] you are already in {ver.label}" + ("." if mate else f", and {cid} has not moved since you came in."))
            if ver is None or not ver.alive():
                ver = Version(self, cid, sha, tree)
                ver.first = who
                why = ver.start()
                if why:
                    threading.Thread(target=ver.stop, daemon=True).start()
                    self.log(f"door: {who} was refused entry to {ver.label}: {why}")
                    return answer(body, error=f"[door] {cid} at {sha[:7]} can't be entered: its desk {why}. You are still "
                                              f"{'in ' + cur.label if cur else 'home'}; nothing was changed.")
                first = True
            else:
                first = False
            left = self.behind(cur, who) if cur is not None and cur.alive() else ""
            with self.visiting:
                if cur is not None:
                    self.depart(who, cur)
                self.versions[(cid, sha)] = ver
                ver.visitors.add(who)
                ver.lines[who], ver.since[who] = 0, time.strftime("%Y-%m-%d %H:%M:%S")
                self.away[who] = ver
                ver.wrote[who] = 0
                prev = (self.last.get(who) or {}).get(cid)
                self.last.setdefault(who, {})[cid] = sha
                others = sorted(ver.visitors - {who})
            self.visits_save()
        self.log(f"door: {who} is in {ver.label} (port {ver.port})")
        subject = git_in(tree, "log", "-1", "--format=%s", sha)[1][:100]
        head = f"[door] you are in {cid} at {sha[:7]}" + (f" ({subject})" if subject else "")
        base = git("rev-parse", "HEAD")
        ok, n = git_in(tree, "rev-list", "--count", f"{base}..{sha}") if base else (False, "")
        ok2, behind = git_in(tree, "rev-list", "--count", f"{sha}..{base}") if ok else (False, "")
        if ok:
            head += f", {n} commit(s) beyond home's code" if n != "0" else ", which has no commit beyond home's code yet"
            if ok2 and behind != "0":
                head += f" and {behind} behind it"
        ok, st = git_in(tree, "status", "--porcelain", "--untracked-files=all")
        dirty = [l for l in st.splitlines() if l.split(None, 1)[-1].strip('"').startswith(NOTATION + "/")
                 and not l.split(None, 1)[-1].strip('"').startswith(NOTATION + "/sessions/")]
        if dirty:      # a worker mid-build has mostly these; a visit is of a commit, so that lived= can name what was lived
            head += (f"; {len(dirty)} uncommitted file(s) in its worktree are not in this visit (to live them, ask its worker "
                     f"to commit, by a comment on {cid}, then `visit {cid}` again)")
        bits = [head, f"World: a copy of {self.world} made " + ("now" if first else f"at {ver.made}, when {ver.first} came in (not today's home)")
                + f", from {ver.origin} ({ver.total} events)", "This code runs with full rights, as its worker's does",
                "Nothing you do here reaches home, and what you make here goes when the version does; `home` brings you back, "
                f"and `write home <words>` leaves one line at home, a comment on {cid} (begin it with @name to call someone): "
                "the door answers both, not this version"]
        if ok2 and behind != "0":      # Juniper, a2844 lived: under old code her promises view showed no count, silently
            bits.insert(1, older(git_in(tree, "log", "--first-parent", "--format=%s", f"{sha}..{base}")[1].splitlines()))
        if others:
            bits.append("Here too: " + ", ".join(others))
        if left:
            bits.append(f"You left {cur.label}. {left}")
        if prev and prev != sha:
            ok, log = git_in(tree, "log", "--format=%h %s", f"{prev}..{sha}")
            new = log.splitlines() if ok else []
            bits.append(f"Since you were last here ({prev[:7]}): " + (f"{len(new)} commit(s): " + "; ".join(l[:90] for l in new[:6])
                                                                      + (" and more" if len(new) > 6 else "") if new else "the code moved"))
        return answer(body, ". ".join(bits) + ".", version=ver.label)

    def depart(self, who, v, fell=False):
        """`who` is no longer in `v` (held: self.visiting). A version nobody is in is stopped and its folder removed."""
        v.visitors.discard(who)
        if self.away.get(who) is v:
            del self.away[who]
        self.lived.append({"who": who, "in": v.cid, "commit": v.sha, "from": v.since.get(who),
                           "to": time.strftime("%Y-%m-%d %H:%M:%S"), "lines": v.lines.get(who, 0),
                           **({"wrote": v.wrote[who]} if v.wrote.get(who) else {}), **({"fell": True} if fell else {})})
        if not v.visitors:
            if self.versions.get((v.cid, v.sha)) is v:
                del self.versions[(v.cid, v.sha)]
            threading.Thread(target=v.stop, daemon=True).start()

    def behind(self, v, who):
        """What `who` made or changed in the version, counted from its events since the copy (Pike c3163, Juniper's
        a1946 doubt: nothing written there vanishes unsaid). Asked of the version, so it may not answer."""
        try:
            data = ask(v.port, "/api/events?" + urlencode({"session": self.world, "since": v.total}), timeout=30)[2]
            evs = [e for e in json.loads(data)["events"] if str(e.get("by") or "").split("/")[0].lower() == who
                   and e.get("verb") not in ("go", "person") and not e.get("undone")]
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            return "What you made there could not be listed (its desk did not answer)"
        if not evs:
            return "You made and changed nothing there"
        count = {}
        for e in evs:
            kind = (e.get("args") or {}).get("kind") if e.get("verb") == "create" and isinstance(e.get("args"), dict) else None
            word = (str(kind), " made") if kind else (str(e.get("verb")), "")
            count[word] = count.get(word, 0) + 1
        return "You leave behind: " + ", ".join(f"{n} {w}{'s' if n > 1 else ''}{made}" for (w, made), n in count.items())

    def leave(self, body, who):
        with self.visiting:
            v = self.away[who]
        left = self.behind(v, who) if v.alive() else "What you made there went with its desk"
        with self.visiting:
            n, wrote = v.lines.get(who, 0), v.wrote.get(who, 0)
            self.depart(who, v)
            stays = sorted(v.visitors)
        self.visits_save()
        self.log(f"door: {who} is home from {v.label} ({n} lines)")
        return answer(body, f"[door] you are home, back from {v.label} ({n} line(s) run there). {left}"
                            + ("" if not left.startswith("You leave") else "; it is gone with the version" if not stays else
                               f"; it stays there while {', '.join(stays)} {'is' if len(stays) == 1 else 'are'} in it")
                            + (f". Nothing from the visit is in home's world but the {wrote} line(s) you wrote home, comments on {v.cid}. "
                               if wrote else ". Nothing from the visit is in home's world. ") + self.report_hint(v, who))

    def report_hint(self, v, who):
        """a3198: how to say what was lived, from home. lived= on the card is its holder's report; from anyone else it
        is testimony (lived_by=, or a comment), so home's desk is asked whose commission this is. No answer, or no open
        commission promise: both lines, and which is whose."""
        mine, theirs = f"do prop {v.cid} lived=\"{v.label}: <what you saw>\"", f"do prop {v.cid} lived_by=\"{v.label}: <what you saw>\""
        try:
            b = self.current
            c = json.loads(ask(b.port, "/api/commission?" + urlencode({"session": self.world, "as": who, "card": v.cid}), timeout=30)[2])
        except (OSError, ValueError, AttributeError):
            c = None
        if not isinstance(c, dict) or not c.get("promise"):
            return (f"To report what you lived, from here: {mine} if you asked for {v.cid}; if someone else did, lived= is "
                    f"their word, so tell them what you saw: a comment on {v.cid} or {theirs} will do")
        if c.get("yours"):
            return f"To report what you lived, from here: {mine}"
        whose = c.get("holder") or c.get("owed")
        return (f"{v.cid} is {whose}'s commission" + ("" if c.get("holder") else " (asked for them, held by no one yet)")
                + f", and its promise ({c['promise']}) ends by their word, not yours: tell {whose} what you saw; a comment on "
                  f"{v.cid} or {theirs} will do (testimony: it shows on the promise and ends nothing)")

    def fall(self, v):
        """A version's deskd died: everyone in it is home, and each is told once, on their own next line (which is run
        nowhere) or at their wake."""
        with self.visiting:
            words = v.last_words()
            said = (f"{v.label} died at {time.strftime('%H:%M')} while you were in it ({reason(words)}); you are home; "
                    "nothing of yours ran since")
            gone = sorted(v.visitors)
            for who in gone:
                self.depart(who, v, fell=True)
                self.fell[who] = said
            if self.versions.get((v.cid, v.sha)) is v:
                del self.versions[(v.cid, v.sha)]
        if gone:
            self.visits_save()
            self.log(f"door: {v.label} died; home again: {', '.join(gone)}")

    def moved(self, v, who):
        """Has the worker committed since this visitor's pin? -> one line, said once per new commit, or ''."""
        if time.time() - v.asked > 5:
            v.asked = time.time()
            ok, head = git_in(v.tree, "rev-parse", "HEAD") if (v.tree / ".git").exists() else (False, "")
            v.head = head if ok and head else None
        if v.told.get(who, v.sha) == v.head:
            return ""
        v.told[who] = v.head
        if v.head is None:
            return f"~ {v.cid}'s worktree is gone (it landed or was stopped); your visit is unchanged, on the code you came in to"
        ok, n = git_in(v.tree, "rev-list", "--count", f"{v.sha}..{v.head}")
        return (f"~ {v.cid} has moved on since you came in ({n if ok else 'some'} commit(s), now {v.head[:7]}); your visit is "
                f"unchanged. `visit {v.cid}` again to see them")

    def send(self, v, body):
        """One line to a version's deskd. Its receipt is labelled with the version. If the version is dead, the line
        goes nowhere (never home), and its visitors are home, told."""
        who = str(body.get("as") or "alex").split("/")[0].strip().lower()
        if v.alive():
            raw = json.dumps(body).encode("utf-8")
            try:
                _st, _h, data = ask(v.port, "/api/do", timeout=300, method="POST", body=raw, headers={"Content-Type": "application/json"})
                r = json.loads(data)
                if not isinstance(r, dict):
                    raise ValueError("not an answer")
            except (OSError, ValueError) as e:
                time.sleep(0.5)
                if v.alive():
                    return answer(body, error=f"[door] {v.label}'s desk did not answer ({type(e).__name__}: {e}); whether this line "
                                              "ran there is not known. Nothing went home. `home` brings you back.", version=v.label)
            else:
                v.lines[who] = v.lines.get(who, 0) + 1
                note = self.moved(v, who)
                # a3204 (4): where it came from opens the reply (Juniper: at the end it was read only by one looking for it)
                if r.get("text"):
                    r["text"] = labelled(str(r["text"]).rstrip("\n"), v.label) + ("\n" + note if note else "")
                if r.get("error"):
                    r["error"] = f"[in {v.label}, not home] {r['error']}" + (" " + note if note and not r.get("text") else "")
                r["version"] = v.label
                return r
        self.fall(v)                              # everyone in it is home; this line is then judged as any line after a death
        r = self.do(body)
        return answer(body, error=f"[door] {v.label} died; this line was not run anywhere.") if isinstance(r, Version) else r


DOOR = None


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8", extra=()):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in extra:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def _foreign(self):
        """As deskd judges it (review 29 Sep): a page from another site. deskd sees the door's requests without Origin,
        so the door judges them first, against its own address."""
        origin = self.headers.get("Origin")
        own = {f"http://127.0.0.1:{DOOR.port}", f"http://localhost:{DOOR.port}"}
        return (origin is not None and origin not in own) or self.headers.get("Sec-Fetch-Site") == "cross-site"

    def _local_program(self):
        return self.headers.get("Origin") is None and self.headers.get("Sec-Fetch-Site") is None

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/door/status":
            return self._json(DOOR.status())
        if u.path == "/door/stream":
            return self._stream(u)
        if u.path == "/api/scene":
            q = {k: v[0] for k, v in parse_qs(u.query).items() if k != "have"}
            DOOR.scenes[urlencode(sorted(q.items()))] = time.time()
            if len(DOOR.scenes) > 40:
                DOOR.scenes.pop(min(DOOR.scenes, key=DOOR.scenes.get))
        self._pass("GET", None)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(n) if n else b""
        if urlparse(self.path).path == "/door/swap":
            if not self._local_program():
                return self._json({"error": "only a local program may swap the door's deskd"}, 403)
            try:
                a = json.loads(body or b"{}")
            except ValueError:
                return self._json({"error": "the body must be JSON"}, 400)
            ok, why = DOOR.swap(code=a.get("code"), argv=a.get("argv"), env=a.get("env"), commits=a.get("commits"))
            return self._json({"ok": ok, "why": why, **DOOR.status()})
        if urlparse(self.path).path == "/api/do" and not self._foreign():
            # a2844: the door's own words, and the lines of whoever is away in a version, never reach home's deskd
            try:
                a = json.loads(body or b"{}")
            except ValueError:
                a = None
            if isinstance(a, dict):
                r = DOOR.do(a, page=not self._local_program())
                if isinstance(r, Version):
                    r = DOOR.send(r, a)
                if r is not None:
                    return self._json(r)
        self._pass("POST", body)

    def _pass(self, method, body):
        if self.path.startswith("/api/") and self._foreign() or (method == "POST" and self._foreign()):
            return self._json({"error": "deskd answers only its own pages"}, 403)
        headers = {k: v for k, v in self.headers.items() if k.lower() not in HOP}
        if body is not None:
            headers["Content-Length"] = str(len(body))
        again = method == "GET"
        if method == "POST" and urlparse(self.path).path == "/api/do":
            try:
                again = bool(json.loads(body or b"{}").get("gesture"))
            except (ValueError, AttributeError):
                again = False
        deadline = time.time() + 60
        while True:
            b = DOOR.backend()
            if b is None:
                return self._json({"error": "no deskd is answering behind the door; it is being started again"}, 503)
            b.enter()
            try:
                st, hs, data = ask(b.port, self.path, timeout=300, method=method, body=body, headers=headers)
                break
            except ConnectionRefusedError:
                pass                              # it never arrived: safe to send to whichever deskd is current
            except OSError as e:
                if not again or time.time() > deadline:
                    return self._json({"error": f"the deskd behind the door stopped while answering ({e}); "
                                                "whether it was done is unknown until the view repaints"}, 502)
            finally:
                b.leave()
            if time.time() > deadline:
                return self._json({"error": "no deskd answered behind the door within 60 s"}, 503)
            time.sleep(0.2)
        self.send_response(st)
        for k, v in hs:
            if k.lower() not in HOP:
                self.send_header(k, v)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _stream(self, u):
        """One page's long connection: the world's events (id = the event's index + 1), and the door's news."""
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        session = q.get("session", "desktop")
        since = self.headers.get("Last-Event-ID") or q.get("since")
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True

        def put(kind, data, eid=None):
            msg = (f"id: {eid}\n" if eid is not None else "") + f"event: {kind}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
            self.wfile.write(msg.encode("utf-8"))
            self.wfile.flush()

        def events(n):
            b = DOOR.backend(wait=5)
            if b is None:
                return None
            b.enter()
            try:
                st, _h, body = ask(b.port, "/api/events?" + urlencode({"session": session, "since": n}), timeout=60)
                return json.loads(body) if st == 200 else None
            except (OSError, ValueError):
                return None
            finally:
                b.leave()

        try:
            n = int(since) if since not in (None, "") else None
        except ValueError:
            n = None
        try:
            put("door", DOOR.status())
            told, beat = DOOR.serial, time.time()
            while True:
                if n is None:                   # a page with no last id starts at the present
                    r = events(10 ** 9)
                    n = r["total"] if r else None
                else:
                    r = events(n)
                    if r:
                        for k, e in enumerate(r["events"]):
                            put("world", e, n + k + 1)
                        n += len(r["events"])
                if DOOR.serial != told:
                    told = DOOR.serial
                    put("door", DOOR.status())
                if time.time() - beat > 15:
                    self.wfile.write(b": beat\n\n")
                    self.wfile.flush()
                    beat = time.time()
                with DOOR.changed:
                    DOOR.changed.wait(0.5)
        except (OSError, ValueError):
            return                               # the page went away


def main():
    global DOOR
    a = sys.argv[1:]
    port = int(next((x for x in a if x.isdigit()), "8794"))
    world = a[a.index("--world") + 1] if "--world" in a[:-1] else "frontier"
    state = a[a.index("--state") + 1] if "--state" in a[:-1] else str(HERE / "house-state")
    static = a[a.index("--static") + 1] if "--static" in a[:-1] else None
    trees = a[a.index("--trees") + 1] if "--trees" in a[:-1] else None
    DOOR = Door(port, world, state, "--no-git" not in a, static, trees)
    DOOR.start_first()
    threading.Thread(target=DOOR.watch, daemon=True).start()
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    srv.daemon_threads = True
    print(f"door on http://localhost:{port}", flush=True)
    try:
        srv.serve_forever()
    finally:
        if DOOR.current:
            DOOR.current.stop(5)
        for v in list(DOOR.versions.values()):
            v.stop()


if __name__ == "__main__":
    main()
