"""Council night (proof card a13431): a Tuesday council hearing on the development, run end to end on the kernel.

Forty neighbours, three of their agents and two modules in Node (agenda, tally) share one world over real HTTP on
loopback. Before the meeting the agenda module brings the posted agenda in, neighbours sign up for two-minute comment
slots (once each, a fixed number of seats, closing at a time of day) and claim carpool seats. During it thirty phones
follow "now speaking" on a painted page while the floor reporter moves it on, neighbours' agents draft a summary of
each item, labelled as agents, and a sealed pulse poll asks whether to push for a continuance. After it the outcome is
a pinned announcement in the feed, with the staff report linked. Speakers' phone numbers are seen only by leaders.

Every press is made the way lens.js makes one (the line and fence of a painted node); every typed act is a line to
/do. The kernel's clock is the night's (set by this script), so sign-up can close at 5:45 pm. Nothing appears on the
screen: the pages are drawn by headless Chrome with --shots.

    C:/Projects/Agora4/.venv/Scripts/python.exe src/agora/proof/council_night.py [--shots] [--out DIR]

Labels for what it writes: the people, their words, the agenda and the summaries are imagined (written here; no model
is called); the counts, refusals and timings are ran.
"""
import argparse
import json
import random
import re
import secrets
import shutil
import statistics
import subprocess
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

PROOF = Path(__file__).resolve().parent
LAB = PROOF.parent
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(LAB / "tests"))

from test_skeleton import StandInEntry, post        # noqa: E402
from test_painter import quoted, walk                # noqa: E402
from kernel.door import serve                        # noqa: E402
from kernel.kernel import Kernel                     # noqa: E402
from kernel import scratch  # noqa: E402

NODE = shutil.which("node")
PY = sys.executable
INVITE = "council-flyer"
FIRST = ["Maya", "Bea", "Jo", "Ruth", "Sam", "Lena", "Omar", "Priya", "Tom", "Ines", "Gus", "Hana", "Wes", "Nora",
         "Raul", "Kiko", "Abel", "Fern", "Luis", "Mei", "Otto", "June", "Cruz", "Tess", "Ike", "Lark", "Pia", "Ravi",
         "Sol", "Vera", "Yuri", "Zoe", "Ada", "Ben", "Cleo", "Dev", "Eli", "Faye", "Hugo"]
STREETS = ["Murray St", "5th Ave", "Seabright Ave", "Logan St", "Mott Ave", "Watson St", "Effey St", "3rd Ave"]


class Clock:
    """The night's time, which the kernel reads for every record and for when sign-up closes."""

    def __init__(self, at):
        self.set(at)

    def set(self, at):
        self.t = datetime.strptime(at, "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)

    def __call__(self):
        return self.t


class Night:
    def __init__(self, out):
        self.out = out
        self.dir = scratch.mkdtemp(prefix="council-night-")
        self.secret = secrets.token_hex(16)
        self.entry = StandInEntry(self.secret)
        self.clock = Clock("2026-10-28T20:00Z")                      # 1 pm in Seabright
        genesis = {"tag": "sb", "name": "Seabright", "steward": {"account": "google:alex", "name": "Alex"},
                   "invites_counted_by": "kernel", "invites": [{"code": INVITE, "channel": "flyers", "uses": 80}],
                   "groups": [{"name": "Organizers"}, {"name": "Council watch", "open": True}],
                   "modules": [
                       {"name": "agenda", "run": [NODE, str(LAB / "modules/agenda/agenda.js")],
                        "publishes": "agenda.*", "grants": "find look make set"},
                       {"name": "tally", "run": [NODE, str(LAB / "modules/tally/tally.js")],
                        "publishes": "tally.*", "grants": "look pin"}]}
        self.k = Kernel(self.dir, genesis)
        self.k.clock = self.clock
        self.srv, self.host = serve(self.k, self.entry.url, self.secret, 0, LAB)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        self.entry.kernel_url = self.url
        for m in ("agenda", "tally"):
            assert self.host.wait_offered(self.k.module_named(m)), f"{m} did not offer its words"
        self.tok = {"Alex": "alex-session"}
        self.entry.sessions["alex-session"] = {"account": "google:alex", "method": "google"}
        self.pid = {"Alex": self.k.accounts["google:alex"]}
        self.checks, self.acts, self.refusals = [], [], []
        self.lock = threading.Lock()

    # ------------------------------------------------------------------ acting, as the pages and phones do
    def sign_in(self, name, street, agent=None):
        account = f"google:{name.lower()}"
        token, said = self.entry.sign_in(account, name, invite=INVITE, answers={"street": street}, agent=agent)
        assert token, said
        self.tok[name + (f"/{agent}" if agent else "")] = token
        self.pid[name] = self.k.accounts[account]
        return token

    def _note(self, who, line, out, ms, how):
        with self.lock:
            self.acts.append({"who": who, "how": how, "line": line[:120], "ok": out.get("ok", out.get("error") is None),
                              "ms": round(ms, 1), "said": (out.get("text") or "").split("\n")[0][:160]})

    def do(self, who, line):
        t = time.perf_counter()
        code, out = post(self.url + "/do", {"line": line}, token=self.tok[who])
        assert code == 200, (code, out)
        self._note(who, line, out, (time.perf_counter() - t) * 1000, "typed")
        return out

    def get(self, path, who):
        req = urllib.request.Request(self.url + path, headers={"Authorization": f"Bearer {self.tok[who]}"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())

    def scene(self, who, lens):
        sc = self.get(f"/api/scene?lens={lens}&view=painter&text=1", who)
        assert "refused" not in sc, sc.get("refused")
        return sc

    def press(self, who, sc, thing, part):
        """What lens.js sends for a press on part `part` of the painted card for `thing`, from scene `sc`."""
        n = int(thing[2:])
        seg = f"a{n * 8}"
        node = next((x for x in walk(sc["scene"]) if x.get("acts") and seg in x["key"].split("/")
                     and x["key"].split("/")[-1] == part), None)
        assert node is not None, f"no painted {part} for {thing}"
        act = next(a for a in node["acts"] if a["on"] == "click")
        observed = dict(node.get("fence") or {}, at=sc["events_total"], **{"def": sc["scene"].get("def")})
        t = time.perf_counter()
        code, out = post(self.url + "/api/do", {"session": "phone", "line": act["line"], "observed": observed,
                                                "gesture": secrets.token_hex(6)},
                         token=self.tok[who], headers={"Origin": self.url})
        assert code == 200, (code, out)
        out["ok"] = out.get("error") is None
        self._note(who, act["line"], out, (time.perf_counter() - t) * 1000, "pressed")
        return out

    def check(self, name, ok, detail):
        self.checks.append({"check": name, "ok": bool(ok), "detail": detail})
        print(("  ok   " if ok else "  FAIL ") + name + (f" · {detail}" if detail else ""))

    def records(self):
        return len(self.k.log.records)


class Follower:
    """A phone following the meeting: the kernel's stream says a record was made; the page asks for its scene again
    (one request at a time, as lens.js does, so a burst of records is one redraw) and notes when each "Now:" appeared."""

    def __init__(self, night, who):
        self.n, self.who = night, who
        self.seen, self.gen, self.redraws, self.errors = {}, None, 0, []
        self.dirty, self.ready = threading.Event(), threading.Event()
        threading.Thread(target=self.listen, daemon=True).start()
        threading.Thread(target=self.redraw, daemon=True).start()

    def listen(self):
        req = urllib.request.Request(self.n.url + "/door/stream",
                                     headers={"Authorization": f"Bearer {self.n.tok[self.who]}"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                self.ready.set()
                for line in r:
                    if line.startswith(b"event: world"):
                        self.dirty.set()
        except Exception as e:                    # noqa: BLE001
            self.errors.append(repr(e))

    def redraw(self):
        while True:
            self.dirty.wait()
            self.dirty.clear()
            try:
                sc = self.n.get(f"/api/scene?lens=council&view=painter&text=1&have={self.gen}", self.who)
            except Exception as e:                # noqa: BLE001
                self.errors.append(repr(e))
                continue
            if sc.get("same"):
                continue
            self.gen = sc["gen"]
            self.redraws += 1
            m = re.search(r'"Now: ([^"]+)"', sc.get("text", ""))
            if m and m.group(1) not in self.seen:
                self.seen[m.group(1)] = time.perf_counter()


def pct(xs, p):
    xs = sorted(xs)
    return round(xs[min(len(xs) - 1, int(len(xs) * p))], 1) if xs else None


def main(argv=None, night=None, retain=False):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=str(PROOF / "evidence"))
    ap.add_argument("--shots", action="store_true", help="draw two phone-width pages with headless Chrome")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    random.seed(28)
    started = time.perf_counter()
    N = night or Night(out)
    k = N.k
    cw = next(g for g in k.things("group") if k.state.get(g, "name") == "Council watch")

    print("founding: forty neighbours and three agents sign in (1 pm)")
    names = FIRST[:40] if len(FIRST) >= 40 else FIRST + [f"Neighbour {i}" for i in range(40 - len(FIRST))]
    names = ["Dana"] + names[:39]
    for i, nm in enumerate(names):
        N.sign_in(nm, STREETS[i % len(STREETS)])
    for owner in ("Maya", "Bea", "Jo"):
        N.sign_in(owner, "", agent="notes")
    N.check("forty people and three agents", len(k.things("person")) == 41 and len(k.things("agent")) == 3,
            f"{len(k.things('person'))} persons (Alex and 40 neighbours), {len(k.things('agent'))} agents")
    N.do("Alex", f"role {N.pid['Dana']} leader in={cw}")
    for lens in ("council", "floor"):
        text = (PROOF / "lenses" / f"{lens}.lens").read_text(encoding="utf-8")
        assert N.do("Alex", f"make kind=lens name={lens} text={quoted(text)} in={cw}")["ok"]

    report = N.do("Dana", f'make kind=research title="Staff report, item 7B" '
                          f'url=https://example.org/seabright/council/7B-staff-report.pdf in={cw}')["made"][0]
    r0 = N.records()
    load = N.do("Dana", f"agenda.load in={cw}")
    meeting = next(t for t in k.things("meeting"))
    items = sorted(k.things("item"), key=lambda t: int(k.state.get(t, "order")))
    hearing = next(t for t in items if k.state.get(t, "seats"))
    N.check("the agenda module brings the agenda in as one act", load["ok"] and N.records() == r0 + 1
            and len(items) == 5 and k.log.records[-1]["by"] == k.module_named("agenda")
            and k.log.records[-1].get("for") == N.pid["Dana"],
            f"1 record, {len(items) + 1} things, by the agenda module for Dana")
    refused = N.do("Maya", f"agenda.load in={cw}")
    N.check("only a leader may load an agenda", not refused["ok"] and "leaders" in refused["text"],
            refused["text"].split("\n")[0])

    print("before: carpools and comment slots (3 pm to 5:50 pm)")
    N.clock.set("2026-10-28T22:00Z")
    cars = []
    for driver, frm, lat, lon in (("Omar", "Murray & 5th", 36.9688, -122.0083), ("Lena", "Seabright & Logan",
                                  36.9661, -122.0098), ("Gus", "Mott & Effey", 36.9705, -122.0061)):
        cars.append(N.do(driver, f'make kind=carpool pickup="{frm}" leaves="5:30 pm" seats=3 lat={lat} lon={lon} '
                                 f'in={cw}')["made"][0])
    phone_sc = {nm: N.scene(nm, "council") for nm in names[10:22]}
    with ThreadPoolExecutor(12) as ex:
        rides = list(ex.map(lambda nm: N.press(nm, phone_sc[nm], cars[names.index(nm) % 3], "go"), names[10:22]))
    took = sum(1 for r in rides if r["ok"])
    full = [r for r in rides if not r["ok"]]
    N.check("twelve riders press for nine carpool seats at once", took == 9 and len(full) == 3
            and all("taken" in r["error"] for r in full),
            f"{took} seats taken, {len(full)} told the car is full: {full[0]['error'] if full else ''}")

    signers = names[1:17]                                  # sixteen want to speak; there are twelve slots
    def sign(nm):
        if names.index(nm) % 2:
            return N.do(nm, f"claim {hearing} phone=831-555-{1000 + names.index(nm)}")
        return N.press(nm, N.scene(nm, "council"), hearing, "speak")
    with ThreadPoolExecutor(16) as ex:
        signed = list(ex.map(sign, signers))
    got = [nm for nm, r in zip(signers, signed) if r["ok"]]
    left_out = [nm for nm, r in zip(signers, signed) if not r["ok"]]
    N.check("sixteen sign up at once for twelve two-minute slots", len(got) == 12 and len(left_out) == 4
            and k.shown(N.pid["Maya"], hearing)["claims"] == 12,
            f"12 slots claimed, 4 told it is taken")
    again = N.do(got[0], f"claim {hearing}")
    N.check("once each: a second sign-up is refused", not again["ok"] and "already" in again["text"],
            again["text"].split("\n")[0])
    give_back = N.do(got[1], "undo")
    late_ok = N.do(left_out[0], f"claim {hearing} phone=831-555-2000")
    N.check("undo gives a slot back, and the next neighbour takes it", give_back["ok"] and late_ok["ok"],
            f"{got[1]} gave theirs back; {left_out[0]} took it")
    N.clock.set("2026-10-29T00:50Z")                       # 5:50 pm: sign-up closed at 5:45
    give_back2 = N.do(got[2], "undo")
    closed = N.do(left_out[1], f"claim {hearing}")
    N.check("sign-up closes at a time of day", give_back2["ok"] and not closed["ok"] and "closed" in closed["text"],
            closed["text"].split("\n")[0] + " (a seat was free)")

    bystander = names[30]                                  # signed up for nothing: sees no number, not even their own
    neighbour_look = N.do(bystander, f"look {hearing}")["text"]
    leader_look = N.do("Dana", f"look {hearing}")["text"]
    floor_n = N.scene(bystander, "floor")["text"]
    floor_d = N.scene("Dana", "floor")["text"]
    council_n = N.scene(bystander, "council")["text"]
    N.check("speakers' phone numbers are seen only by leaders",
            "831-555" not in neighbour_look and "831-555" not in floor_n and "831-555" not in council_n
            and "831-555" in leader_look and "Call-backs:" in floor_d and "831-555" in floor_d,
            "absent from a neighbour's look and both of their pages; present in Dana's look and floor page")

    for i in range(5):
        N.do("Ruth", f"post Parking on Murray will be gone by 6, walk if you can ({i + 1})")
    sixth = N.do("Ruth", "post one more thing about parking")
    N.check("the feed is a slow lane", not sixth["ok"] and "5 times today" in sixth["text"],
            sixth["text"].split("\n")[0])

    print("during: thirty phones follow the meeting (6 pm)")
    N.clock.set("2026-10-29T01:00Z")
    followers = [Follower(N, nm) for nm in names[10:40]]
    for f in followers:
        f.ready.wait(10)
    moves = []                                              # (title, when pressed, who)

    def next_item(who, sc=None):
        sc = sc or N.scene(who, "floor")
        t = time.perf_counter()
        r = N.press(who, sc, meeting, "next")
        return r, t

    poll = None
    summaries = {"Maya/notes": {}, "Bea/notes": {}, "Jo/notes": {}}
    WORDS = {  # imagined: what a neighbour's agent drafts for each item (no model is called)
        0: "Roll call: all five present. The mayor read the hearing rules: two minutes each, in sign-up order.",
        1: "Consent calendar passed 5-0 without discussion; nothing on it touches Murray & 5th.",
        2: "Public hearing on 41 homes at Murray & 5th. Most speakers asked about parking and the school crossing; "
           "two spoke for more housing near the bus line.",
        3: "Staff answered the traffic questions only in part; the traffic study is not finished.",
        4: "Council continued the item to 18 Nov, asking staff to return with the traffic study.",
    }
    for step in range(5):
        r, t = next_item("Dana")
        assert r["ok"], r
        title = k.state.get(k.state.get(meeting, "now"), "title")
        moves.append((title, t))
        time.sleep(1.2)                                     # the item is heard; phones catch up
        if step == 2:                                       # the hearing: the pulse poll opens
            poll = N.do("Dana", f'make kind=poll title="Push for continuance?" options="yes no" in={cw}')["made"][0]
            time.sleep(0.5)
            choice = {nm: ("yes" if random.random() < 0.68 else "no") for nm in names}
            def cast(nm):
                if names.index(nm) % 2:
                    return N.do(nm, f"vote {poll} {choice[nm]}")
                sc = N.scene(nm, "council")
                return N.press(nm, sc, poll, "y" if choice[nm] == "yes" else "no")
            with ThreadPoolExecutor(20) as ex:
                cast_out = list(ex.map(cast, names))
            yes = sum(1 for nm in names if choice[nm] == "yes")
            shown = k.shown(N.pid["Ruth"], poll)
            N.check("forty vote at once in a sealed pulse poll",
                    all(c["ok"] for c in cast_out) and shown["votes_yes"] == yes and shown["votes_no"] == 40 - yes,
                    f"yes {shown['votes_yes']} · no {shown['votes_no']}; 20 typed, 20 pressed")
            vote_recs = [rec for rec in k.log.records if rec.get("entry") and k.state.get(rec["entry"], "word") == "vote"]
            leaks = [rec["seq"] for rec in vote_recs if rec.get("by") != "sealed" or any(
                re.search(rf"\b{N.pid[nm]}\b", json.dumps(rec)) for nm in names)]
            look_poll = N.do("Ruth", f"look {poll}")["text"]
            voters = [nm for nm in names if nm != "Dana"]       # Dana made the poll, so her name is on it
            N.check("no record and no view says who voted how", not leaks and "vote:" not in look_poll
                    and not any(re.search(rf"\b{nm}\b", look_poll) for nm in voters),
                    f"{len(vote_recs)} vote records, all by 'sealed', none naming a voter")
            twice = N.do("Bea", f"vote {poll} no")
            change = N.do("Maya", "undo")
            revote = N.do("Maya", f"vote {poll} {'no' if choice['Maya'] == 'yes' else 'yes'}")
            after = k.shown(N.pid["Ruth"], poll)
            N.check("one vote each; undo lets a neighbour change theirs", not twice["ok"] and change["ok"]
                    and revote["ok"] and after["votes"] == 40,
                    f"a second vote: '{twice['text'].split(chr(10))[0]}'; Maya changed hers; still 40 votes")
        # the item just heard: each agent drafts a summary, as the agent of its person
        heard = k.state.get(meeting, "now")
        for ag in (["Maya/notes"] if step != 2 else ["Maya/notes", "Bea/notes", "Jo/notes"]):
            words = WORDS[step] if ag == "Maya/notes" else (
                "Bea's notes: the crossing guard at Murray came up four times." if ag == "Bea/notes"
                else "Jo's notes: two speakers asked for more homes near the 68 bus.")
            made = N.do(ag, f"make kind=summary about={heard} text={quoted(words)} in={cw}")
            summaries[ag][heard] = made["made"][0] if made["ok"] else made["text"]
        if step == 3:                                       # two leaders press Next on one painted page at once
            sc_d, sc_a = N.scene("Dana", "floor"), N.scene("Alex", "floor")
            before_now = k.state.get(meeting, "now")
            with ThreadPoolExecutor(2) as ex:
                both = list(ex.map(lambda w: N.press(w[0], w[1], meeting, "next"), (("Dana", sc_d), ("Alex", sc_a))))
            moved_to = k.state.get(meeting, "now")
            ok_n = sum(1 for b in both if b["ok"])
            N.check("two leaders press Next at once: the meeting moves one item", ok_n == 1
                    and items.index(moved_to) == items.index(before_now) + 1
                    and any("stale" in (b["error"] or "") for b in both),
                    f"one moved it; the other: '{next(b['error'] for b in both if not b['ok'])}'" if ok_n == 1 else
                    f"{ok_n} presses admitted")
            moves.append((k.state.get(moved_to, "title"), time.perf_counter()))
            time.sleep(1.2)
            heard = moved_to
            made = N.do("Maya/notes", f"make kind=summary about={heard} text={quoted(WORDS[4])} in={cw}")
            summaries["Maya/notes"][heard] = made["made"][0]
            break
    not_leader = N.press("Ruth", N.scene("Ruth", "floor"), meeting, "next")
    N.check("a neighbour's Next is refused", not not_leader["ok"] and "leaders" in not_leader["error"],
            not_leader["error"])
    sm = [t for t in k.things("summary")]
    labelled = all(k.state.get(t, "made_by") in k.things("agent") and k.state.get(t, "for") for t in sm)
    council_ruth = N.scene("Ruth", "council")["text"]
    N.check("agents' summaries are labelled as agents", labelled and len(sm) == 7
            and council_ruth.count("agent for Maya · a draft, not the minutes") == 5,
            f"{len(sm)} summaries, each made by an agent for its person; the page says 'agent for Maya' on hers")

    time.sleep(1.5)
    lat = []
    for title, t in moves:
        got_at = [f.seen.get(title) for f in followers]
        lat += [(g - t) * 1000 for g in got_at if g]
    missing = sum(1 for title, _ in moves for f in followers if title not in f.seen)
    N.check("thirty phones follow every 'now speaking'", missing == 0,
            f"{len(moves)} moves × 30 phones; seen within p50 {pct(lat, .5)} ms, p95 {pct(lat, .95)} ms, "
            f"max {round(max(lat), 1) if lat else None} ms; {missing} missed")

    print("after: the outcome, pinned (7:30 pm)")
    N.clock.set("2026-10-29T02:30Z")
    outcome = N.do("Dana", f"post Council continued item 7B to 18 Nov. Staff return with the traffic study. "
                           f"Thank you, all 12 speakers. about={report} in={cw} as=o; pin $o")
    pinned = outcome["ok"] and len(outcome["records"]) == 2
    feed = N.do("Sam", "look")["text"].split("\n")
    first = feed[1] if len(feed) > 1 else ""
    painted = N.scene("Sam", "council")["text"]
    N.check("the outcome is a pinned announcement, with the staff report linked", pinned and "continued item 7B"
            in first and "pinned by Dana" in painted and "see: Staff report, item 7B" in painted,
            f"two records from one line ({', '.join(outcome['records'])}); first in a neighbour's feed")
    other = N.do("Sam", "post Thanks to everyone who drove")["made"][0]
    no_pin = N.do("Sam", f"pin {other}")
    N.check("a neighbour may not pin", not no_pin["ok"] and "leaders" in no_pin["text"], no_pin["text"])
    top = N.do("Sam", "tally.top 2")
    N.check("the tally module (Node) reads the feed as Sam may see it", top["ok"] and "most liked" in top["text"],
            top["text"].split("\n")[0])

    print("the whole: replay and timings")
    snap = k.state.snapshot()
    again = Kernel(N.dir)
    N.check("replaying the log gives the same world", again.state.snapshot() == snap,
            f"{len(k.log.records)} records replayed")
    acts_ms = [x["ms"] for x in N.acts]
    pressed = [x["ms"] for x in N.acts if x["how"] == "pressed"]
    typed = [x["ms"] for x in N.acts if x["how"] == "typed"]
    redraws = sum(f.redraws for f in followers)

    shots = {}
    if a.shots:
        k.dev_sessions = lambda: N.entry.sessions
        # a phone's width (390 px); the neighbour's page is drawn tall so one picture holds all of it
        for who, lens, fn, size in (("Sam", "council", "council-phone.png", "390x2000"),
                                    ("Dana", "floor", "floor-phone.png", "390x844")):
            url = f"{N.url}/dev/signin?token={N.tok[who]}&next=/lens.html%3Flens%3D{lens}%26inspect%3D0"
            r = subprocess.run([PY, str(LAB / "shoot.py"), url, str(out / fn), "--size", size, "--wait", "5"],
                               capture_output=True, text=True, timeout=120)
            shots[fn] = {"who": who, "lens": lens, "size": size, "ok": r.returncode == 0,
                         "said": (r.stdout or r.stderr)[-400:]}
            print(f"  shot {fn}: {'ok' if r.returncode == 0 else r.stderr[-300:]}")

    evidence = {
        "what": "Council night (a13431), run on the kernel over real HTTP on loopback",
        "labels": {"ran": "every check, count and timing below", "imagined": "the people, their words, the agenda "
                   "(modules/agenda/agenda-oct28.json) and the summaries; no model was called"},
        "when": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "world": {"records": len(k.log.records), "persons": len(k.things("person")), "agents": len(k.things("agent")),
                  "modules": ["agenda (Node)", "tally (Node)"], "things": len(k.state.things)},
        "checks": N.checks,
        "passed": sum(c["ok"] for c in N.checks), "of": len(N.checks),
        "timing_ms": {"acts": len(acts_ms), "act_p50": pct(acts_ms, .5), "act_p95": pct(acts_ms, .95),
                      "typed_p50": pct(typed, .5), "pressed_p50": pct(pressed, .5),
                      "follow_p50": pct(lat, .5), "follow_p95": pct(lat, .95), "phone_redraws": redraws,
                      "whole_run_s": round(time.perf_counter() - started, 1)},
        "refused_acts": [x for x in N.acts if not x["ok"]],
        "shots": shots,
    }
    (out / "council-night.json").write_text(json.dumps(evidence, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{evidence['passed']} of {evidence['of']} checks passed · {len(k.log.records)} records · "
          f"acts p50 {evidence['timing_ms']['act_p50']} ms · evidence in {out / 'council-night.json'}")
    if not retain:
        N.srv.shutdown()
        N.host.stop_all()
        shutil.rmtree(N.dir, ignore_errors=True)
    return 0 if evidence["passed"] == evidence["of"] else 1


if __name__ == "__main__":
    sys.exit(main())
