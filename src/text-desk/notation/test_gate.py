"""test_gate (6 Oct): nobody passes the gate without an invite, and the gate, not the page, says who is acting.

    python test_gate.py

Starts a door (door.py --no-git) on a free port over a new empty world, and gate.py in front of it, each with its own
state directory (removed after). No browser: it speaks HTTP as a phone's browser would.
  - without a key: pages and the API answer 401, and nothing reaches the desk;
  - an invite is used once, ends, and names its maker; a reserved or taken name is refused, and so is a name any
    person of the world bears or bore, with nobody listing it (a4164);
  - the gate does not start in front of a world that is not a copy unless told so in words that name the danger;
  - the person the desk makes for someone who came through the gate is kind=human;
  - with a key: a line is signed with the device's name whatever `as` and `session` the request claimed;
  - the door's own words and /door/swap are refused; a POST from another site is refused;
  - the stream passes world events through.
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable
WORLD = f"gate-{os.getpid()}-try"
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


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


OPEN = urllib.request.build_opener(NoRedirect)


def call(url, body=None, headers=None, form=False, timeout=120):
    """-> (status, headers, text)"""
    data = None
    h = dict(headers or {})
    if body is not None:
        data = body.encode() if form else json.dumps(body).encode()
        h.setdefault("Content-Type", "application/x-www-form-urlencoded" if form else "application/json")
    try:
        with OPEN.open(urllib.request.Request(url, data, h), timeout=timeout) as f:
            return f.status, f.headers, f.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read().decode("utf-8", "replace")


def wait_for(url, seconds=90):
    end = time.time() + seconds
    while time.time() < end:
        try:
            urllib.request.urlopen(url, timeout=3).read()
            return True
        except urllib.error.HTTPError:
            return True
        except OSError:
            time.sleep(0.3)
    return False


def invite(state, *more):
    out = subprocess.run([PY, str(HERE / "gate.py"), "invite", "--state", state, *more],
                         capture_output=True, text=True, check=True).stdout.strip()
    return out.split("k=", 1)[1]


def main():
    dstate, gstate = tempfile.mkdtemp(prefix="door-"), tempfile.mkdtemp(prefix="gate-")
    dport, gport = free_port(), free_port()
    door = f"http://127.0.0.1:{dport}"
    gate = f"http://127.0.0.1:{gport}"
    env = {k: v for k, v in os.environ.items() if k != "DESKD"}
    procs = [subprocess.Popen([PY, str(HERE / "door.py"), str(dport), "--world", WORLD, "--state", dstate, "--no-git"],
                              cwd=HERE, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)]
    try:
        check("the door answers", wait_for(door + "/api/health"))
        procs.append(subprocess.Popen([PY, str(HERE / "gate.py"), str(gport), "--world", WORLD, "--door", door,
                                       "--state", gstate, "--reserve", "warden"],
                                      cwd=HERE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        check("the gate answers", wait_for(gate + "/join"))

        # a4164 (1): in front of a world that is not a copy the gate does not start, and says why; told so, it starts
        lived = WORLD[:-len("-try")]
        r = subprocess.run([PY, str(HERE / "gate.py"), str(free_port()), "--world", lived, "--door", door, "--state", gstate],
                           cwd=HERE, capture_output=True, text=True, timeout=60)
        check("in front of a world that is not a copy the gate does not start, and says why",
              r.returncode != 0 and "a stranger has a member's full rights, the whole snapshot and every event" in r.stderr
              and "--strangers-have-full-rights-here" in r.stderr, (r.returncode, r.stdout, r.stderr))
        lport = free_port()
        procs.append(subprocess.Popen([PY, str(HERE / "gate.py"), str(lport), "--world", lived, "--door", door, "--state",
                                       gstate, "--strangers-have-full-rights-here"],
                                      cwd=HERE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        check("told in those words, it starts", wait_for(f"http://127.0.0.1:{lport}/join", 30))

        def desk(line, who="claude"):
            return json.loads(call(door + "/api/do", {"session": WORLD, "as": who, "line": line, "whole": True})[2])

        def people():
            subjects = json.loads(call(door + f"/api/snapshot?session={WORLD}&as=house")[2])["subjects"]
            return {s["props"].get("name"): s["props"].get("kind") for s in subjects.values() if s.get("kind") == "person"}

        desk("look")
        made = desk('do create f01 kind=chat title="Square"')
        chat = made.get("created") or []
        check("a chat was made behind the gate", bool(chat), made)
        chat = chat[0] if chat else "a03"
        # the world's own people: claude and alex have acted, pike is a person who has not, sable was renamed wren
        desk("person begin")
        desk(f"look {chat}", who="alex")
        desk(f'do append {chat} line="here"', who="alex")
        desk("person new pike kind=resident")
        desk("person new sable kind=resident")
        desk("person sable name=wren")
        check("the world has its own people", {"claude", "alex", "pike", "wren"} <= set(people()), people())
        before = json.loads(call(door + f"/api/events?session={WORLD}&since=0")[2])["total"]

        st, _, text = call(gate + "/lens.html")
        check("no key: a page is 401 and says an invite is needed", st == 401 and "invite" in text, (st, text[:200]))
        st, _, text = call(gate + "/api/do", {"session": WORLD, "as": "alex", "line": f'do append {chat} line="x"'})
        check("no key: a line is 401", st == 401, (st, text[:200]))
        st, _, text = call(gate + f"/api/scene?session={WORLD}&as=alex&lens=none")
        check("no key: a read is 401", st == 401, (st, text[:200]))
        st, _, text = call(gate + "/join?k=nonsense")
        check("a made-up invite is refused", st == 403, (st, text[:200]))

        code = invite(gstate, "--by", "alex")
        st, _, text = call(gate + "/join?k=" + code)
        check("an invite's page names its maker", st == 200 and "alex invited you" in text, (st, text[:300]))
        st, _, text = call(gate + "/join", f"k={code}&name=warden", form=True)
        check("a reserved name is refused", st == 200 and "already called warden" in text, (st, text[:300]))
        for taken in ("alex", "claude", "pike", "wren", "sable"):       # a4164 (2): nobody listed these
            st, _, text = call(gate + "/join", f"k={code}&name={taken}", form=True)
            check(f"a name a person of the world bears or bore is refused, unlisted: {taken}",
                  st == 200 and f"already called {taken}" in text, (st, text[:300]))
        st, _, text = call(gate + "/join", f"k={code}&name=x", form=True)
        check("a one-letter name is refused", st == 200 and "2 to 24" in text, (st, text[:300]))
        st, h, text = call(gate + "/join", f"k={code}&name=Maria", form=True)
        cookie = (h.get("Set-Cookie") or "").split(";")[0]
        check("joining gives a key and sends the device to its lens",
              st == 303 and cookie.startswith("desk=") and "as=maria" in (h.get("Location") or ""), (st, dict(h)))
        check("the key is HttpOnly", "HttpOnly" in (h.get("Set-Cookie") or ""), h.get("Set-Cookie"))
        st, _, text = call(gate + "/join", f"k={code}&name=second", form=True)
        check("a used invite is refused", st == 403 and "has been used" in text, (st, text[:300]))
        kept = Path(gstate, "gate.json").read_text(encoding="utf-8")
        check("neither the code nor the key is kept in the clear", code not in kept and cookie[5:] not in kept)

        old = invite(gstate, "--by", "alex", "--days", "-1")
        st, _, text = call(gate + "/join", f"k={old}&name=late", form=True)
        check("an ended invite is refused", st == 403 and "has ended" in text, (st, text[:300]))
        two = invite(gstate, "--by", "maria", "--uses", "2")
        st, _, text = call(gate + "/join", f"k={two}&name=maria", form=True)
        check("a name a device already holds is refused", st == 200 and "already called maria" in text, (st, text[:300]))

        me = {"Cookie": cookie}
        st, _, text = call(gate + "/api/do", {"session": "frontier", "as": "alex", "line": f'look {chat}; do append {chat} line="hello"', "by": "house", "kind": "wake"}, me)
        r = json.loads(text)
        check("with a key a line is run", st == 200 and not r.get("error"), (st, text[:400]))
        ev = json.loads(call(door + f"/api/events?session={WORLD}&since={before}")[2])["events"]
        check("it is signed with the device's name, in the gate's world, whatever the request claimed",
              [(e["verb"], e.get("by")) for e in ev] == [("person", "house"), ("edit", "maria")], ev)
        # a4164 (3): the person the desk made for her at that act is a human, where a local program's is a guess
        check("a person made for someone who came through the gate is kind=human",
              people().get("maria") == "human" and people().get("claude") == "agent", people())
        seen = desk(f"read {chat}")
        check("the chat shows Maria's line", "Maria: hello" in (seen.get("text") or ""), seen)

        for word in ("visit", "home", "worktree fork x", "write home hi"):
            st, _, text = call(gate + "/api/do", {"line": word}, me)
            check(f"`{word}` is refused at the gate", bool(json.loads(text).get("error")), (st, text[:300]))
        st, _, text = call(gate + "/api/do", {"line": f'do append {chat} line="a"; home'}, me)
        check("a door word hidden in a batch is refused", bool(json.loads(text).get("error")), (st, text[:300]))
        st, _, text = call(gate + "/door/swap", {"code": "x"}, me)
        check("/door/swap is not passed on", st == 404, (st, text[:200]))
        st, _, text = call(gate + "/door/status", None, me)
        check("/door/status is not passed on", st == 404, (st, text[:200]))
        st, _, text = call(gate + "/api/do", {"line": f'do append {chat} line="evil"'},
                           {**me, "Origin": "https://elsewhere.example"})
        check("a POST from another site's page is refused", st == 403, (st, text[:200]))
        st, _, text = call(gate + "/api/do", {"line": f'do append {chat} line="mine"'},
                           {**me, "Origin": f"http://127.0.0.1:{gport}"})
        check("a POST from the gate's own page is run", st == 200 and not json.loads(text).get("error"), (st, text[:300]))
        total = json.loads(call(door + f"/api/events?session={WORLD}&since=0")[2])["total"]
        check("the refused lines made no event", total == before + 3, (before, total))     # her person, and two lines

        st, _, text = call(gate + "/lens.html", None, me)
        check("with a key the painter's page is served", st == 200 and "<script" in text, (st, text[:200]))
        st, h, _ = call(gate + "/", None, me)
        check("/ sends a device to its own lens", st == 303 and "as=maria" in (h.get("Location") or ""), (st, dict(h)))
        st, _, text = call(gate + "/api/snapshot?session=frontier&as=alex", None, me)
        snap = json.loads(text)
        check("a read is of the gate's world, not the one asked for",
              st == 200 and snap.get("events_total") == total, (st, text[:200]))

        got = []

        def listen():
            req = urllib.request.Request(gate + "/door/stream?session=frontier&since=" + str(total), headers=me)
            try:
                with urllib.request.urlopen(req, timeout=20) as f:
                    for raw in f:
                        got.append(raw.decode("utf-8", "replace"))
                        if raw.startswith(b"event: world"):
                            return
            except OSError:
                pass

        t = threading.Thread(target=listen, daemon=True)
        t.start()
        time.sleep(1.0)
        call(gate + "/api/do", {"line": f'do append {chat} line="live"'}, me)
        t.join(20)
        check("the stream carries the world's events through the gate", any(x.startswith("event: world") for x in got), got[:6])
    finally:
        for p in reversed(procs):
            p.terminate()
        for p in procs:
            try:
                p.wait(10)
            except subprocess.TimeoutExpired:
                p.kill()
        time.sleep(0.5)
        shutil.rmtree(dstate, ignore_errors=True)
        shutil.rmtree(gstate, ignore_errors=True)
        for f in (HERE / "sessions").glob(WORLD + ".*"):
            try:
                f.unlink()
            except OSError:
                pass
    print(f"\n{len(fails)} failed" if fails else "\nall passed")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
