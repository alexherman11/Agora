"""the_walk (a3941, for Juniper's a3932): one invented stranger, mina, walks the nine steps, and each step says how far
today's desk lets her get.

    python the_walk.py [world]            default world: frontier-try

Never the live world: it copies sessions/<world>.pickle to sessions/walk-<pid>-try.pickle (removed after, with what
the desk writes beside it), starts a door (door.py --no-git) over the copy and gate.py in front of the door, each with
its own state directory (removed after). In what it prints, "home" is that copy standing in for the live world.
No browser: mina speaks HTTP through the gate as a phone's browser would (her key is the cookie the gate gave her);
alex speaks to the door as a local program, as the house and a terminal do.

It changes nothing in the desk's code and proves nothing passes: every step prints one verdict
    RAN            it happened as the walk asks
    WORKAROUND     something happened, by another road than the walk's; the road is named
    CANNOT         it cannot be tried today; what is missing is named
and under it the facts that were read off the running servers. Step 9 is the walk's own check: the events mina left
in home's history. The folds and the phone-sized painter need a real browser: see screen.py (the commission's done
comment names the runs).
"""
import json
import os
import shutil
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
SRC = next((a for a in sys.argv[1:] if not a.startswith("-")), "frontier-try")
WORLD = f"walk-{os.getpid()}-try"
TABLE, CARD, LENS = "f562", "a591", "command-center"      # Alex's Desktop, a card on it, the lens he looks through
OPEN_CHAT, PRIVATE_CHAT = "a570", "a575"                  # Lounge talk (members=all); Talk with Alex, Sable (members=alex)
verdicts = []


def free_port():
    import socket
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


OPEN = urllib.request.build_opener(NoRedirect)


def call(url, body=None, headers=None, form=False, timeout=300):
    """-> (status, headers, text)"""
    data, h = None, dict(headers or {})
    if body is not None:
        data = body.encode() if form else json.dumps(body).encode()
        h.setdefault("Content-Type", "application/x-www-form-urlencoded" if form else "application/json")
    try:
        with OPEN.open(urllib.request.Request(url, data, h), timeout=timeout) as f:
            return f.status, f.headers, f.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read().decode("utf-8", "replace")


def wait_for(url, seconds=120):
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


def step(n, name):
    print(f"\n=== {n}. {name}")


def verdict(n, word, why):
    verdicts.append((n, word, why))
    print(f"  >> {word}: {why}")


def fact(*words):
    print("  -", *words)


def short(s, n=300):
    s = str(s)
    for mark in ("[3] ", "[2] "):                 # several commands in one line: the last one's answer
        if mark in s:
            s = s.split(mark, 1)[1]
            break
    s = " ".join(l for l in s.splitlines() if not l.startswith(("!!", "   "))) or s      # not what was missed since a look
    s = " ".join(s.split())
    return s if len(s) <= n else s[:n] + " ..."


def main():
    src = HERE / "sessions" / f"{SRC}.pickle"
    if not src.exists():
        sys.exit(f"the_walk: no world {SRC!r} in {HERE / 'sessions'}")
    copy = HERE / "sessions" / f"{WORLD}.pickle"
    shutil.copyfile(src, copy)
    dstate, gstate = tempfile.mkdtemp(prefix="walk-door-"), tempfile.mkdtemp(prefix="walk-gate-")
    dport, gport = free_port(), free_port()
    door, gate = f"http://127.0.0.1:{dport}", f"http://127.0.0.1:{gport}"
    env = {k: v for k, v in os.environ.items() if k != "DESKD"}
    procs = [subprocess.Popen([PY, str(HERE / "door.py"), str(dport), "--world", WORLD, "--state", dstate, "--no-git"],
                              cwd=HERE, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)]
    try:
        if not wait_for(door + "/api/health"):
            sys.exit("the_walk: the door did not answer")
        procs.append(subprocess.Popen([PY, str(HERE / "gate.py"), str(gport), "--world", WORLD, "--door", door, "--state", gstate,
                                       "--lens", LENS, "--reserve", "alex,claude"],
                                      cwd=HERE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        if not wait_for(gate + "/join"):
            sys.exit("the_walk: the gate did not answer")
        print(f"the_walk: home is a copy of {SRC} ({WORLD}); door {door}; gate {gate}")

        def alex(line):
            return json.loads(call(door + "/api/do", {"session": WORLD, "as": "alex", "line": line})[2])

        def total():
            return json.loads(call(door + f"/api/events?session={WORLD}&since=1000000000")[2])["total"]

        def events(since):
            return json.loads(call(door + f"/api/events?session={WORLD}&since={since}")[2])["events"]

        def said(r):
            return short(r.get("error") or r.get("text") or r)

        alex("look")                              # so that alex's later answers do not open with what he missed
        start = total()
        fact(f"home's history has {start} events before mina")

        # ---------------------------------------------------------------- 0: no invite
        step(0, "WITH NO INVITE")
        st, _, text = call(gate + "/")
        fact(f"GET / -> {st}: {short(text.split('<h1>')[-1], 160)}")
        st2, _, text = call(gate + f"/api/scene?session={WORLD}&as=alex&lens={LENS}")
        fact(f"GET /api/scene claiming as=alex -> {st2}: {short(text, 120)}")
        st3, _, text = call(gate + "/api/do", {"session": WORLD, "as": "alex", "line": "look"})
        fact(f"POST /api/do claiming as=alex -> {st3}: {short(text, 120)}")
        st4, _, text = call(gate + "/join?k=made-up-code")
        fact(f"GET /join with a made-up code -> {st4}: {short(text.split('<h1>')[-1], 160)}")
        fact(f"home's history after these: {total()} events")
        verdict(0, "RAN", "nothing is shown and nothing is done without an invite" if (st, st2, st3, st4) == (401, 401, 401, 403) and total() == start
                else "the gate let something through without an invite; read the facts above")

        # ---------------------------------------------------------------- 1: arrive
        step(1, "ARRIVE")
        out = subprocess.run([PY, str(HERE / "gate.py"), "invite", "--by", "alex", "--state", gstate],
                             capture_output=True, text=True, check=True).stdout.strip()
        fact(f"alex made an invite on this machine (gate.py invite --by alex): {out.split('k=')[0]}k=<code>")
        code = out.split("k=", 1)[1]
        t0 = time.time()
        st, _, text = call(gate + "/join?k=" + code)
        fact(f"mina opens the link -> {st}: {short(text.split('<h1>')[-1].split('<form')[0], 200)} and a box: What should people here call you?")
        st, h, _ = call(gate + "/join", f"k={code}&name=Mina", form=True)
        cookie = (h.get("Set-Cookie") or "").split(";")[0]
        where = h.get("Location") or ""
        fact(f"she types Mina and presses Come in -> {st}, a key in a cookie ({'yes' if cookie.startswith('desk=') else 'NO'}), sent to {where}")
        me = {"Cookie": cookie, "Origin": gate}
        st, _, text = call(gate + where, None, {"Cookie": cookie})
        fact(f"that page -> {st}, {len(text)} characters, the painter's page: {'yes' if '<script' in text else 'no'}")
        st, _, text = call(gate + f"/api/scene?lens={LENS}&view=painter", None, {"Cookie": cookie})
        sc = json.loads(text)
        took = time.time() - t0

        def count(n):
            return 1 + sum(count(k) for k in (n.get("kids") or []))
        gen0 = sc.get("gen")
        fact(f"the scene she is drawn ({LENS}) -> {st}: " + (f"refused: {short(sc['refused'])}" if "refused" in sc else
                                                              f"{count(sc['scene'])} painted parts, {len(text)} bytes"))
        fact(f"from link to a painted scene: {took:.1f} s over HTTP on this machine (no phone, no network)")
        after = total()
        fact(f"home's history: {after} events; arriving and looking made {after - start}")
        people = alex("person mina")
        fact(f"alex asks `person mina` before she has acted: {said(people)}")

        def mina(line, **more):
            st, _, text = call(gate + "/api/do", {"line": line, **more}, me)
            try:
                return st, json.loads(text)
            except ValueError:
                return st, {"error": text}

        n0 = total()
        st, r = mina("look")
        fact(f"her first line, `look` -> {st}: {said(r)}")
        made = events(n0)
        for e in made:
            fact(f"  it made {e['id']} {e['verb']} {e.get('target')} by={e.get('by')} args={short(e.get('args'), 120)}")
        fact(f"alex asks `person mina` after it: {said(alex('person mina'))} (a look changes nothing, so it made no person)")
        verdict(1, "WORKAROUND" if "refused" not in sc else "CANNOT",
                "she arrives by a one-use invite alex made by hand on this machine, with a name she typed, and is drawn the lens the gate "
                "was started with; nothing was installed. The road is not the walk's: an invite per person, a gate nothing starts, "
                "and no address outside this machine" if "refused" not in sc else "the gate's lens was refused for her")

        # ---------------------------------------------------------------- 2: see his table live
        step(2, "SEE HIS TABLE LIVE")
        got, opened = [], threading.Event()

        def listen():
            req = urllib.request.Request(gate + "/door/stream", headers={"Cookie": cookie})
            try:
                with urllib.request.urlopen(req, timeout=40) as f:
                    opened.set()
                    for raw in f:
                        if raw.startswith(b"data:") and got and got[-1][0] == "world":
                            got[-1] = ("world", time.time(), raw.decode("utf-8", "replace"))
                        if raw.startswith(b"event: world"):
                            got.append(("world", time.time(), ""))
                        if len([g for g in got if g[2]]) >= 1:
                            return
            except OSError:
                pass

        t = threading.Thread(target=listen, daemon=True)
        t.start()
        opened.wait(20)
        time.sleep(1.5)
        alex(f"look {TABLE} :2")
        t1 = time.time()
        r = alex(f"do move {CARD} before=a564")
        fact(f"alex moves a card on his table (do move {CARD} before=a564): {said(r)}")
        t.join(30)
        if got and got[0][2]:
            e = json.loads(got[0][2].split("data:", 1)[1])
            fact(f"mina's open connection carried it {got[0][1] - t1:+.2f} s after alex's line was answered: {e.get('id')} {e.get('verb')} "
                 f"{e.get('target')} by={e.get('by')}, the whole event, as the door sends every event of the world to every page")
        else:
            fact("mina's open connection carried nothing within 30 s")
        st, _, text = call(gate + f"/api/scene?lens={LENS}&view=painter&have={gen0}", None, {"Cookie": cookie})
        sc2 = json.loads(text)
        fact("her next scene: " + ("the same build (this lens does not show that card's place)" if sc2.get("same") else f"a new build ({sc2.get('gen')}), no reload"))
        _, snap = call(gate + "/api/snapshot", None, {"Cookie": cookie})[1:]
        snap = json.loads(snap)
        fact(f"what she reads is home itself: /api/snapshot through the gate says {snap.get('events_total')} events; home has {total()}")
        for word in (f"visit a3941", "worktree fork mine"):
            st, r = mina(word)
            fact(f"mina asks for a copy of her own (`{word}`) -> {st}: {said(r)}")
        st, _, text = call(door + "/api/do", {"session": WORLD, "as": "mina", "line": "visit a3941"}, {"Origin": door})
        fact(f"the same word from a page straight at the door, no gate -> {st}: {short(text, 260)}")
        verdict(2, "WORKAROUND", "she sees his change in about a second with no reload, but only because she is looking at home itself. "
                                 "A copy that keeps receiving his events does not exist, and the two copies that do exist (a visit, a fork) "
                                 "are refused to her")

        # ---------------------------------------------------------------- 3: be there with others
        step(3, "BE THERE WITH OTHERS")
        def here(r):
            return [l for l in (r.get("text") or "").splitlines() if l.startswith(("You are", "Here", "No one")) or " seen from " in l]

        def pike(line):                           # a resident, asked on the copy: what someone who has a place is told
            return json.loads(call(door + "/api/do", {"session": WORLD, "as": "pike", "line": line})[2])

        st, r = mina("look")
        fact(f"mina looks; where she is and who is with her: {here(r)}")
        fact(f"alex looks at that room (Home): {here(alex('look f149'))}")
        fact(f"a resident looks at that room: {here(pike('look f149'))}")
        n3 = total()
        st, r = mina("go Desktop")
        fact(f"mina walks to alex's table (`go Desktop`) -> {st}: {short(here(r) or said(r), 200)}; it made "
             + (", ".join(f"{e['id']} {e['verb']} by={e.get('by')}" for e in events(n3)) or "no event"))
        fact(f"alex looks at his table: {here(alex(f'look {TABLE}'))}")
        fact(f"a resident looks at his table: {here(pike(f'look {TABLE}'))}")
        fact("mina closes her page (the connection of step 2 is closed) and they look again:")
        time.sleep(1)
        line2 = here(alex(f"look {TABLE}")) + here(pike(f"look {TABLE}"))
        fact(f"  {line2}")
        st, _, text = call(gate + "/door/status", None, {"Cookie": cookie})
        fact(f"the door's own account of itself, asked through the gate -> {st} (not passed on); asked directly it lists: "
             f"{sorted(json.loads(call(door + '/door/status')[2]).keys())}")
        verdict(3, "CANNOT", "being here is a fact kept in history (the room someone last went to), not who has a page open: "
                             + ("she is named at his table only after a `go`, which is an event in home's history, and she is still "
                                "named after she closed the page" if any("Mina" in l for l in line2) else
                                "mina is not named to anyone, open page or not")
                             + ". Nothing counts open pages; presence that is shown and not kept is missing")

        # ---------------------------------------------------------------- 4: do something of her own
        step(4, "DO SOMETHING OF HER OWN")
        fact("a fold and a scroll are hers alone and make no event: that needs a browser (screen.py; see the done comment)")
        n4 = total()
        st, r = mina(f"look {TABLE} :2")
        st, r = mina(f"do move {CARD} after=a566")
        fact(f"mina moves alex's card to where she likes it (do move {CARD} after=a566) -> {st}: {said(r)}")
        for e in events(n4):
            if e.get("verb") == "person":
                fact(f"  before it, the desk made her a person: {e['id']} {e['verb']} {e.get('target')} by={e.get('by')} args={short(e.get('args'), 120)}")
        fact(f"  alex asks `person mina`: {said(alex('person mina'))}")
        hers = [e for e in events(n4) if e.get("by") == "mina"]
        move = next((e for e in hers if e.get("verb") == "move"), None)
        for e in hers:
            fact(f"  home's history now holds {e['id']} {e['verb']} {e.get('target')} by={e.get('by')}")
        r = alex(f"examine {CARD}")
        fact(f"alex examines his card: {short([l for l in (r.get('text') or '').splitlines() if 'where:' in l or 'last touched' in l], 260)}")
        verdict(4, "CANNOT", "a fold and a scroll are hers; a moved card is not: her move is a fact of home, signed mina, and alex's card "
                             "moved for alex and everyone"
                if move else "her move was refused, and there is no other place for it to go")

        # ---------------------------------------------------------------- 5: keep following
        step(5, "KEEP FOLLOWING WHERE SHE HAS NOT DIFFERED")
        rev = (json.loads(call(gate + "/api/snapshot", None, {"Cookie": cookie})[2]).get("nodes") or {}).get(CARD, {}).get("rev")
        alex(f"look {CARD}")
        r = alex(f'do retitle {CARD} title="The command center (walk)"')
        fact(f"alex retitles the card: {said(r)}")
        st, r = mina(f"look {TABLE} :2")
        fact(f"mina looks: the new title is there: {'yes' if 'The command center (walk)' in (r.get('text') or '') else 'no'} (she reads home, so she always follows)")
        alex(f"look {CARD}")
        r = alex(f"do move {CARD} after=a587")
        fact(f"alex moves the card she moved: {said(r)}")
        st, r = mina(f"do move {CARD} before=a566", observed={"item": CARD, "rev": rev, "at": 0})
        fact(f"mina presses on the card as her page painted it before alex's two changes (revision {rev}) -> {st}: {said(r)}")
        verdict(5, "CANNOT", "following is all she can do (she reads home), and there is nothing of hers to keep: alex's move replaced where the "
                             "card is, for her too, and nothing told her. What exists is the "
                             "fence on a press made from an old painting, which is refused and names his event")

        # ---------------------------------------------------------------- 6: come back
        step(6, "COME BACK")
        if move:
            st, r = mina(f"undo {move['id']}")
            fact(f"mina takes her own move back (undo {move['id']}) -> {st}: {said(r)}")
        alex(f"look {CARD}")
        n6 = total()
        r = alex(f"do prop {CARD} walk=his")
        ret = next((e for e in events(n6) if e.get("by") == "alex"), None)
        fact(f"alex marks his card (do prop {CARD} walk=his): {said(r)}")
        if ret:
            st, r = mina(f"undo {ret['id']}")
            fact(f"mina takes back ALEX's change, the latest on the card (undo {ret['id']}) -> {st}: {said(r)}")
            r = alex(f"look {TABLE} :2")
            fact(f"  alex's card still says walk=his: {'yes' if 'walk=his' in (r.get('text') or '') else 'NO: the stranger undid his change'}")
        verdict(6, "CANNOT", "with nothing of hers laid over his, there is nothing to drop. The only way back is undo, which is itself an "
                             "event in home's history, is refused once anything was built on the event, and reaches other people's events too")

        # ---------------------------------------------------------------- 7: touch a shared thing
        step(7, "TOUCH A SHARED THING")
        n7 = total()
        st, r = mina(f'look {OPEN_CHAT}; do append {OPEN_CHAT} line="hello from the walk"', session="frontier", **{"as": "alex"})
        e7 = events(n7)
        fact(f"mina adds a line to the open chat, her request claiming as=alex and the real world's name -> {st}: {said(r)}")
        for e in e7:
            fact(f"  home's history: {e['id']} {e['verb']} {e.get('target')} by={e.get('by')} (the gate wrote the name and the world, not the page)")
        r = alex(f"read {OPEN_CHAT}")
        fact(f"alex reads the chat and her line is in it, under her name: {'yes' if 'Mina: hello from the walk' in (r.get('text') or '') else 'no'}")
        st, r = mina(f"read {PRIVATE_CHAT}")
        fact(f"mina reads a chat between alex and one resident (members=alex) -> {st}: {'she is given ' + str(len(r.get('text') or '')) + ' characters of it' if not r.get('error') else said(r)}")
        st, r = mina(f'look {PRIVATE_CHAT}; do append {PRIVATE_CHAT} line="hello from the walk"')
        fact(f"mina writes in that chat -> {st}: {said(r)}")
        st, r = mina(f'look {TABLE} :2; do create {TABLE} kind=note title="left by mina"')
        fact(f"mina puts a note of her own on alex's table, which nobody marked shared -> {st}: {said(r)}")
        time.sleep(10.5)
        codes = [mina("look")[0] for _ in range(34)]
        fact(f"after ten quiet seconds, 34 lines as fast as they go: {codes.count(200)} run, {codes.count(429)} refused (the gate's one limit: 30 lines in 10 s for a device)")
        verdict(7, "WORKAROUND", "her chat line is added, signed mina by the gate, and alex reads it. But nothing is marked shared and nothing "
                                 "needs to be: she may write wherever any member may. The only limit on a stranger is 30 lines in 10 seconds")
        time.sleep(10.5)

        # ---------------------------------------------------------------- 8: offer a change
        step(8, "OFFER A CHANGE TO HIS THING")
        n8 = total()
        st, r = mina(f'look {CARD}; do comment {CARD} line="the title should say Command centre"')
        fact(f"mina comments on his card -> {st}: {said(r)}")
        for e in events(n8):
            fact(f"  home's history: {e['id']} {e['verb']} {e.get('target')} by={e.get('by')}")
        r = alex(f"examine {CARD}")
        fact(f"alex examines the card and finds it: {'yes' if 'Command centre' in (r.get('text') or '') else 'no'}")
        verdict(8, "WORKAROUND", "she can say it in words, as a comment alex resolves; the comment does not carry the new title, and alex would "
                                 "retype it. Nothing makes her offer: she may change his card herself, as she moved it in step 4")

        # ---------------------------------------------------------------- 9: leave, and his desk is unchanged
        step(9, "LEAVE, AND HIS DESK IS UNCHANGED")
        st, _, text = call(gate + "/leave", None, {"Cookie": cookie})
        fact(f"there is no leaving: GET /leave -> {st}; her key still opens the place: GET / -> {call(gate + '/', None, {'Cookie': cookie})[0]} (a year, by the cookie)")
        kept = json.loads(Path(gstate, "gate.json").read_text(encoding="utf-8"))
        fact(f"the gate's own file holds {len(kept['devices'])} device(s) and {len(kept['invites'])} invite(s), as hashes; removing her is editing that file by hand")
        evs = events(start)
        hers = [e for e in evs if e.get("by") == "mina"]
        about = [e for e in evs if e.get("by") != "mina" and "mina" in json.dumps(e.get("args") or {}).lower()]
        by_verb = {}
        for e in hers:
            by_verb[e["verb"]] = by_verb.get(e["verb"], 0) + 1
        fact(f"home's history grew by {len(evs)} events during the walk; {len(hers)} are signed mina: {by_verb}")
        fact(f"and {len(about)} more are about her, signed {sorted({e.get('by') for e in about})} (the person made for her at her first act)")
        allowed = [e for e in hers if (e.get("target") == OPEN_CHAT and e.get("verb") == "edit") or e.get("verb") == "comment"]
        fact(f"of hers, {len(allowed)} are what the walk allows (a line on a shared thing, an offer); {len(hers) - len(allowed)} are not: "
             + ", ".join(f"{e['id']} {e['verb']} {e.get('target')}" for e in hers if e not in allowed)[:600])
        verdict(9, "RAN" if len(hers) == len(allowed) else "CANNOT",
                "home's history holds nothing of hers but shared lines and offers" if len(hers) == len(allowed) else
                f"the check fails today: {len(hers) - len(allowed)} events of hers on things nobody shared are in home's history, and it cannot "
                "pass while she acts in home itself")
    finally:
        for p in reversed(procs):
            p.terminate()
        for p in procs:
            try:
                p.wait(10)
            except subprocess.TimeoutExpired:
                p.kill()
        time.sleep(3.5)                           # the door's deskd goes within 3 s of the door (deskd.py, DESKD_PARENT)
        shutil.rmtree(dstate, ignore_errors=True)
        shutil.rmtree(gstate, ignore_errors=True)
        for f in (HERE / "sessions").glob(WORLD + "*"):
            try:
                f.unlink()
            except OSError:
                pass
    print("\n=== HOW FAR MINA GOT")
    for n, word, why in verdicts:
        print(f"  {n}. {word}: {why}")


if __name__ == "__main__":
    main()
