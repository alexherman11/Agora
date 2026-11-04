"""An evening of joining, played in a hidden browser against the real services.

    C:/Projects/Agora4/.venv/Scripts/python.exe research/community-app/site/scenario/evening.py

What happens, in order:
 1. Alex signs in on his phone (emailed link), answers the questions and makes three invites: one link for
    Instagram, a flyer QR code for the meeting at Galt Elementary, and a one-person link for his neighbour Sam.
    He prints the flyer; the flyer's QR code is read back from the poster's pixels, as a phone camera would.
 2. The kernel's world is founded with Alex as its steward (research/kernel-lab, its own process).
 3. Twenty-nine neighbours join at phone width, each in a browser of their own, by Google, by tapping the
    emailed link, or by typing the emailed code; the people at the meeting share the venue's wifi.
 4. A bot finds the Instagram link and floods it. Alex sees it in "who came through", freezes that link alone,
    and the flyer and Sam's link keep working. Rosa, who asked just before the freeze, is turned away and
    comes in by the flyer instead.
 5. Maya signs in on her laptop, opens the email on her phone, and types the code on the laptop.
 6. Everyone's answers are read back from the kernel, through the kernel's own door, as each person.

Nothing appears on screen: a headless browser, no console windows, everything on loopback ports chosen
at random, all data in a temporary folder that is removed afterwards. Screenshots and a report are written to
evidence/evening/.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path
from wsgiref.simple_server import WSGIRequestHandler, make_server

SITE = Path(__file__).resolve().parent.parent
REPO = SITE.parents[2]
KERNEL_LAB = REPO / "research" / "kernel-lab"
OUT = SITE / "evidence" / "evening"
sys.path.insert(0, str(SITE))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import qr_read  # noqa: E402
from cdp import NO_WINDOW, Browser, free_port  # noqa: E402
from kernel import scratch  # noqa: E402

from agora_entry.__main__ import ThreadingServer  # noqa: E402
from agora_entry.config import Config  # noqa: E402
from agora_entry.fake_google import StandIn, serve_in_thread  # noqa: E402
from agora_entry.web import App  # noqa: E402

PHONE, LAPTOP = (390, 844), (1280, 800)
HELP = {"meetings": "Come to meetings", "neighbours": "Talk with neighbours", "research": "Research and reading",
        "online": "Spread the word online", "skills": "Design, writing or tech", "watching": "Just keeping up for now"}

# name shown in chat, email, how they get in, what they tick, neighbourhood
INSTAGRAM = [
    ("Maya R.", "maya.rivera@example.com", "link", ["meetings", "research"], "Seabright"),
    ("Jordan P.", "jordanp@example.org", "google", ["online"], ""),
    ("Priya S.", "priya.s@example.net", "code", ["research", "skills"], "Seabright"),
    ("Luis M.", "luis.m@example.com", "link", ["neighbours"], "Live Oak"),
    ("Hannah K.", "hannahk@example.org", "google", ["meetings"], ""),
    ("Dev A.", "dev.a@example.net", "code", ["skills"], "Seabright"),
    ("Grace L.", "grace.l@example.com", "link", ["watching"], ""),
    ("Omar F.", "omar.f@example.org", "google", ["meetings", "neighbours"], "Seabright"),
    ("Tess W.", "tess.w@example.net", "link", ["online", "research"], ""),
    ("Ken O.", "ken.o@example.com", "code", ["neighbours"], "Seabright"),
    ("Bea N.", "bea.n@example.org", "google", ["meetings"], "Live Oak"),
    ("Sol V.", "sol.v@example.net", "link", ["research"], ""),
]
DURING_FLOOD = [
    ("Ana C.", "ana.c@example.com", "code", ["meetings"], "Seabright"),
    ("Will T.", "will.t@example.org", "google", ["watching"], ""),
]
MEETING = [  # at Galt Elementary, scanning the flyer, on the school's wifi
    ("Carmen D.", "carmen.d@example.com", "code", ["meetings", "neighbours"], "Seabright"),
    ("Pat G.", "pat.g@example.org", "google", ["meetings"], "Seabright"),
    ("Rich B.", "rich.b@example.net", "code", ["neighbours"], ""),
    ("Yuki M.", "yuki.m@example.com", "link", ["research"], "Seabright"),
    ("Abel S.", "abel.s@example.org", "code", ["meetings"], ""),
    ("June H.", "june.h@example.net", "google", ["online", "meetings"], "Seabright"),
    ("Nora E.", "nora.e@example.com", "code", ["watching"], ""),
    ("Felix Q.", "felix.q@example.org", "link", ["skills", "online"], "Live Oak"),
    ("Iris J.", "iris.j@example.net", "code", ["meetings"], "Seabright"),
    ("Marco Z.", "marco.z@example.com", "google", ["neighbours"], ""),
    ("Lena U.", "lena.u@example.org", "code", ["research"], "Seabright"),
    ("Hugo I.", "hugo.i@example.net", "link", ["meetings", "research"], ""),
]
ROSA = ("Rosa G.", "rosa.g@example.com", "code", ["neighbours", "meetings"], "Seabright")
THEO = ("Theo B.", "theo.b@example.org", "code", ["online"], "")
SAM = ("Sam K.", "sam.k@example.net", "link", ["meetings", "neighbours"], "Seabright")
VENUE_IP = "10.9.9.9"


class Run:
    def __init__(self):
        self.t0 = time.time()
        self.lines: list[str] = []
        self.checks: list[tuple[str, bool, str]] = []
        self.shots: list[str] = []

    def say(self, who: str, what: str) -> None:
        line = f"{time.time() - self.t0:6.1f}s  {who:<10} {what}"
        self.lines.append(line)
        print(line, flush=True)

    def check(self, what: str, ok: bool, detail: str = "") -> None:
        self.checks.append((what, bool(ok), detail))
        print(f"        {'PASS' if ok else 'FAIL'}  {what}{(' (' + detail + ')') if detail else ''}", flush=True)


R = Run()


# -- the services ---------------------------------------------------------

class Quiet(WSGIRequestHandler):
    def log_message(self, *a):
        pass


def start_services(tmp: Path):
    ep, gp, kp = free_port(), free_port(), free_port()
    base = f"http://127.0.0.1:{ep}"
    issuer = f"http://127.0.0.1:{gp}"
    secret = secrets.token_hex(24)
    cfg = Config(mode="test", base_url=base, host="127.0.0.1", port=ep, data_dir=tmp / "entry",
                 content_dir=SITE / "content", secret_key=secrets.token_bytes(32),
                 google_mode="fake", google_client_id="stand-in-client", google_client_secret="stand-in-secret",
                 google_auth_url=issuer + "/authorize", google_token_url=issuer + "/token",
                 google_jwks_url=issuer + "/certs", google_issuers=(issuer,), fake_google_port=gp,
                 leaders=frozenset({"alex@example.com"}), proxy_ip_header="X-Test-Client-IP",
                 kernel_secret=secret, kernel_url=f"http://127.0.0.1:{kp}",
                 email_from="Seabright Neighbours <signin@example.com>")
    cfg.check()
    google = serve_in_thread(StandIn("stand-in-client", "stand-in-secret", base + "/auth/google/callback", issuer), gp)
    app = App(cfg)
    server = make_server("127.0.0.1", ep, app, server_class=ThreadingServer, handler_class=Quiet)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return app, server, google, kp, secret


def found_kernel(tmp: Path, port: int, entry_port: int, secret: str, steward: str):
    genesis = {"tag": "sb", "name": "Seabright", "steward": {"account": steward, "name": "Alex H."},
               "invites_counted_by": "entry", "groups": [{"name": "Organizers"}]}
    gpath = tmp / "genesis.json"
    gpath.write_text(json.dumps(genesis), encoding="utf-8")
    log = open(tmp / "kernel.log", "w", encoding="utf-8")  # noqa: SIM115 - closed with the process
    env = dict(os.environ, KERNEL_SHARED_SECRET=secret)
    proc = subprocess.Popen([sys.executable, "-m", "kernel.door", "--world", str(tmp / "world"), "--genesis",
                             str(gpath), "--port", str(port), "--entry", f"http://127.0.0.1:{entry_port}"],
                            cwd=KERNEL_LAB, env=env, stdout=log, stderr=log, creationflags=NO_WINDOW)
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2) as r:
                return proc, json.loads(r.read())
        except OSError:
            time.sleep(0.2)
    raise RuntimeError("the kernel did not start; see kernel.log")


def kernel_see(port: int, token: str, line: str) -> dict:
    req = urllib.request.Request(f"http://127.0.0.1:{port}/see", json.dumps({"line": line}).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as exc:
        return {"status": exc.code, **json.loads(exc.read() or b"{}")}


# -- mail ----------------------------------------------------------------

def mails_to(app: App, email: str) -> list[dict]:
    return [m for m in reversed(app.mailer.recent(10_000)) if m["to"] == email]


async def next_mail(app: App, email: str, before: int) -> dict:
    for _ in range(200):
        got = mails_to(app, email)
        if len(got) > before:
            return got[-1]
        await asyncio.sleep(0.05)
    raise TimeoutError(f"no mail for {email}")


def code_of(mail: dict) -> str:
    m = re.search(r"sign-in page: (\d{3}) (\d{3})", mail["text"])
    return m.group(1) + m.group(2)


# -- people in the browser --------------------------------------------------

async def join(app: App, tab, person, url: str, shots=None) -> str:
    """One newcomer from an invite link to home. -> "home", or what stopped them."""
    name, email, how, ticks, hood = person
    await tab.goto(url)
    text = await tab.text()
    if "invited you to join" not in text.lower():  # the line is capitalised by CSS
        return "closed: " + " ".join(text.split())[:160]
    if shots:
        await shots(tab, "join")
    if how == "google":
        await tab.click("a.btn.google")
        await tab.type("#email", email)
        await tab.type("#name", name.rstrip("."))
        await tab.click("button[value=allow]")
    else:
        before = len(mails_to(app, email))
        await tab.type("#email", email)
        await tab.click('form[action="/signin/email"] button')
        if shots:
            await shots(tab, "check-email")
        mail = await next_mail(app, email, before)
        if how == "link":
            parts = urllib.parse.urlsplit(mail["links"][0])
            await tab.goto(f"{parts.scheme}://{parts.netloc}{parts.path}?{parts.query}")
            await tab.click('form[action="/signin/link"] button')
        else:
            await tab.type("#code", code_of(mail))
            await tab.click('form[action="/signin/code"] button')
    if not (await tab.url()).endswith("/welcome"):
        return "stopped: " + " ".join((await tab.text()).split())[:160]
    if shots:
        await shots(tab, "welcome")
    await answer(tab, person)
    return "home" if (await tab.url()).endswith("/home") else "stopped after the questions"


async def answer(tab, person) -> None:
    name, _, _, ticks, hood = person
    await tab.type("#q_display_name", name)
    for t in ticks:
        await tab.click_text("label.chip", HELP[t], navigates=False)
    if hood:
        await tab.type("#q_neighbourhood", hood)
    await tab.click('form[action="/welcome"] button[type=submit]')


# -- the bot ---------------------------------------------------------------

def bot(app: App, code: str, ips: list[str], stop: threading.Event, tally: dict) -> None:
    """A script that found the Instagram link: it makes accounts as fast as the site lets it."""
    base = app.cfg.base_url
    closed_in_a_row = 0
    for i in range(80):
        if stop.is_set() or closed_in_a_row >= 3:
            break
        ip = ips[i % len(ips)]
        jar = CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        opener.addheaders = [("X-Test-Client-IP", ip), ("User-Agent", "Mozilla/5.0 (bot)")]

        def get(path, opener=opener):
            try:
                with opener.open(base + path, timeout=10) as r:
                    return r.status, r.read().decode()
            except urllib.error.HTTPError as exc:
                return exc.code, exc.read().decode()

        def post(path, fields, opener=opener):
            try:
                with opener.open(base + path, urllib.parse.urlencode(fields, doseq=True).encode(), timeout=10) as r:
                    return r.status, r.read().decode()
            except urllib.error.HTTPError as exc:
                return exc.code, exc.read().decode()

        status, page = get(f"/join/{code}")
        if status != 200:
            closed_in_a_row += 1
            tally["closed"] += 1
            continue
        closed_in_a_row = 0
        csrf = re.search(r'name="csrf" value="([0-9a-f]+)"', page).group(1)
        email = f"promo{i:03d}@deals.example.net"
        before = len(mails_to(app, email))
        status, _ = post("/signin/email", {"csrf": csrf, "email": email, "invite": code})
        if status == 429:
            tally["slowed"] += 1
            continue
        got = mails_to(app, email)
        if len(got) <= before or not got[-1]["links"]:
            tally["no_link"] += 1
            continue
        link = urllib.parse.urlsplit(got[-1]["links"][0])
        status, page = get(f"{link.path}?{link.query}")
        if status != 200:
            tally["refused"] += 1
            continue
        csrf = re.search(r'name="csrf" value="([0-9a-f]+)"', page).group(1)
        token = urllib.parse.parse_qs(link.query)["t"][0]
        status, page = post("/signin/link", {"csrf": csrf, "t": token})
        if "Welcome" not in page:
            tally["refused"] += 1
            continue
        csrf = re.search(r'name="csrf" value="([0-9a-f]+)"', page).group(1)
        post("/welcome", {"csrf": csrf, "q_display_name": f"FREE CRYPTO {i:03d} \U0001f680", "q_help": "online"})
        tally["joined"] += 1
        time.sleep(0.05)


# -- the evening -----------------------------------------------------------

async def evening() -> None:
    tmp = Path(scratch.mkdtemp(prefix="entry-evening-"))
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    app, server, google, kport, secret = start_services(tmp)
    kernel = None
    browser = await Browser().start()
    R.say("setup", f"entry service, Google stand-in and a headless {Path(browser.exe).stem} on loopback; "
                   f"data in a temporary folder")
    people: dict[str, tuple] = {}
    tabs: dict[str, object] = {}
    tokens: dict[str, str | None] = {}

    async def shot(tab, name, selector=None):
        path = await tab.shot(OUT / name, selector)
        R.shots.append(path.name)
        return path

    try:
        # 1. Alex sets up -----------------------------------------------------------
        alex = await browser.person("Alex", "10.0.0.1")
        await alex.goto(app.cfg.base_url + "/")
        await shot(alex, "01-public-site.jpg")
        await alex.goto(app.cfg.base_url + "/signin")
        await alex.type("#email", "alex@example.com")
        await alex.click('form[action="/signin/email"] button')
        mail = await next_mail(app, "alex@example.com", 0)
        await alex.goto(mail["links"][0])
        await alex.click('form[action="/signin/link"] button')
        await answer(alex, ("Alex H.", "", "", ["skills", "meetings"], "Seabright"))
        R.say("Alex", "signed in on his phone by emailed link and answered the questions")
        R.check("Alex lands on home", (await alex.url()).endswith("/home"))

        links = {}
        for channel, kind, uses, days in (("Instagram", "link", "", "30"), ("Flyer, Galt Elementary meeting", "event", "", "7"),
                                          ("Direct: Sam", "link", "1", "7")):
            await alex.goto(app.cfg.base_url + "/leader/invites")
            await alex.type("#channel", channel)
            await alex.click_text("label.chip", "QR code for an event" if kind == "event" else "Link to share", False)
            if uses:
                await alex.type("#max_uses", uses)
            await alex.js(f"document.querySelector('#expires_days').value = '{days}'")
            await alex.click('form[action="/leader/invites"] button')
            links[channel] = (await alex.url(), await alex.value("#link"))
        R.say("Alex", "made three invites: Instagram (no limit), the meeting flyer (QR, 7 days), Sam (one use)")
        flyer_page, flyer_link = links["Flyer, Galt Elementary meeting"]
        await alex.goto(flyer_page + "/qr")
        await shot(alex, "02-flyer-poster.jpg")
        poster_qr = await alex.shot(tmp / "poster-qr.png", ".poster-qr")
        scanned = qr_read.read(poster_qr)
        R.say("phone", f"a camera reads the printed flyer's QR code: {scanned}")
        R.check("the flyer's QR code carries the flyer's invite link", scanned == flyer_link, scanned)
        insta_link, sam_link = links["Instagram"][1], links["Direct: Sam"][1]
        insta_id = links["Instagram"][0].rsplit("/", 1)[1]

        # 2. The kernel's world is founded -------------------------------------------
        alex_id = app.service.account_by_email("alex@example.com")["id"]
        kernel, health = found_kernel(tmp, kport, app.cfg.port, secret, alex_id)
        R.say("kernel", f"world founded with Alex as steward, on its own loopback port: {health}")
        await alex.goto(app.cfg.base_url + "/home")
        R.check("Alex's account is joined to his kernel person (the steward)",
                bool(app.service.account_by_email("alex@example.com")["kernel_person"]))

        # 3. Neighbours join ---------------------------------------------------------
        async def settle(person, tab, keep=False):
            """Their phone keeps its session; this run keeps only the cookie, and closes the browser."""
            people[person[1]] = person
            tokens[person[1]] = (await tab.cookies()).get("agora_session")
            if keep:
                tabs[person[1]] = tab
            else:
                await tab.close()

        async def newcomer(person, url, ip, size=PHONE, keep=False, shots=None):
            tab = await browser.person(person[0], ip, size)
            outcome = await join(app, tab, person, url, shots)
            await settle(person, tab, keep)
            return tab, outcome

        async def maya_shots(tab, step):
            names = {"join": "03-maya-join.jpg", "check-email": "04-maya-check-email.jpg",
                     "welcome": "05-maya-welcome.jpg"}
            await shot(tab, names[step])

        for i, p in enumerate(INSTAGRAM):
            tab, outcome = await newcomer(p, insta_link, f"10.1.0.{10 + i}", keep=i == 0,
                                          shots=maya_shots if i == 0 else None)
            R.say(p[0], f"Instagram link, {p[2]}: {outcome}")
            R.check(f"{p[0]} gets in through Instagram", outcome == "home", outcome)
            if i == 0:
                await shot(tab, "06-maya-home.jpg")
        for p in MEETING[:6]:
            tab, outcome = await newcomer(p, scanned, VENUE_IP)
            R.say(p[0], f"scanned the flyer at the meeting, {p[2]}: {outcome}")
            R.check(f"{p[0]} gets in through the flyer", outcome == "home", outcome)
        tab, outcome = await newcomer(SAM, sam_link, "10.2.0.5")
        R.say("Sam", f"Alex's direct link: {outcome}")
        R.check("Sam gets in through his direct link", outcome == "home", outcome)
        friend = await browser.person("Sam's friend", "10.2.0.6")
        await friend.goto(sam_link)
        used_up = "used as many times as it allows" in await friend.text()
        await shot(friend, "07-sams-link-used-up.jpg")
        R.say("Sam's friend", "opens the link Sam forwarded: it has been used")
        R.check("a one-use link turns away a second person", used_up)

        # 4. The flood -----------------------------------------------------------
        code = insta_link.rsplit("/", 1)[1]
        tally = {"joined": 0, "closed": 0, "slowed": 0, "refused": 0, "no_link": 0}
        stop = threading.Event()
        bot_thread = threading.Thread(target=bot, args=(app, code, ["203.0.113.7", "203.0.113.8"], stop, tally))
        bot_thread.start()
        R.say("bot", "finds the Instagram link and starts making accounts")
        for i, p in enumerate(DURING_FLOOD):
            tab, outcome = await newcomer(p, insta_link, f"10.1.1.{10 + i}")
            R.say(p[0], f"Instagram link during the flood, {p[2]}: {outcome}")
            R.check(f"{p[0]} still gets in while the bot is at it", outcome == "home", outcome)
        rosa = await browser.person("Rosa", "10.1.2.10")
        await rosa.goto(insta_link)
        await rosa.type("#email", ROSA[1])
        await rosa.click('form[action="/signin/email"] button')
        R.say("Rosa", "asks for a sign-in email on the Instagram link")
        while tally["joined"] < 12 and bot_thread.is_alive():
            await asyncio.sleep(0.1)
        await alex.goto(app.cfg.base_url + "/leader/invites")
        await shot(alex, "08-leader-sees-the-flood.jpg")
        busy = await alex.js("""(() => { const hot = document.querySelector('.sub.hot'); if (!hot) return null;
            const r = hot.getBoundingClientRect(); return [hot.closest('a').innerText, r.bottom <= innerHeight]; })()""")
        R.say("Alex", f"opens Invites on his phone: {' '.join(busy[0].split()) if busy else 'no link marked busy'}")
        R.check("the flooded link is marked busy on the first screen, without scrolling", bool(busy and busy[1]))
        await alex.goto(links["Instagram"][0])
        await shot(alex, "09-who-came-through-instagram.jpg")
        seen = await alex.text()
        R.say("Alex", f"opens Instagram's invite: {seen.count('FREE CRYPTO')} 'FREE CRYPTO' names among who came through")
        await alex.click('form[action$="/freeze"] button')
        frozen_at = time.time()
        await shot(alex, "10-instagram-frozen.jpg")
        R.say("Alex", "freezes the Instagram link")
        bot_thread.join(timeout=60)
        stop.set()
        state = app.service.invite_by_id(insta_id)
        R.say("bot", f"gives up: {tally}")
        bots_in = sum(1 for p in app.service.invite_people(insta_id) if p["display_name"].startswith("FREE CRYPTO"))
        R.check("the bot is stopped by the freeze: it meets a closed link", tally["closed"] >= 1, str(tally))
        late_bots = [p for p in app.service.invite_people(insta_id) if p["at"] > frozen_at + 1]
        R.check("nobody comes in through Instagram after the freeze", not late_bots, f"{len(late_bots)} late")
        R.check("Instagram shows as frozen", state.status == "frozen")

        mail = (mails_to(app, ROSA[1]))[-1]
        await rosa.type("#code", code_of(mail))
        await rosa.click('form[action="/signin/code"] button')
        rosa_text = await rosa.text()
        await shot(rosa, "11-rosa-turned-away.jpg")
        said = " ".join(rosa_text.split())
        R.say("Rosa", "types her code after the freeze: " + said[said.find("We couldn"):][:110])
        R.check("Rosa's request from before the freeze is turned away", "invite link has closed" in rosa_text)
        outcome = await join(app, rosa, ROSA, scanned)
        await settle(ROSA, rosa)
        R.say("Rosa", f"a neighbour shows her the flyer; she scans it: {outcome}")
        R.check("Rosa gets in through the flyer instead", outcome == "home", outcome)
        theo = await browser.person("Theo", "10.1.2.11")
        await theo.goto(insta_link)
        theo_text = await theo.text()
        await shot(theo, "12-theo-finds-instagram-paused.jpg")
        R.check("a newcomer on the frozen link is told it is paused", "paused by the group" in theo_text)
        outcome = await join(app, theo, THEO, scanned)
        await settle(THEO, theo)
        R.say("Theo", f"Instagram says paused; he uses the flyer: {outcome}")
        R.check("Theo gets in through the flyer", outcome == "home", outcome)
        for p in MEETING[6:]:
            tab, outcome = await newcomer(p, scanned, VENUE_IP)
            R.say(p[0], f"scanned the flyer after the freeze, {p[2]}: {outcome}")
            R.check(f"{p[0]} gets in through the flyer after the freeze", outcome == "home", outcome)

        # 5. Maya on two devices ---------------------------------------------------
        phone = tabs["maya.rivera@example.com"]
        laptop = await browser.person("Maya's laptop", "10.1.0.10", LAPTOP, mobile=False)
        await laptop.goto(app.cfg.base_url + "/signin")
        before = len(mails_to(app, "maya.rivera@example.com"))
        await laptop.type("#email", "maya.rivera@example.com")
        await laptop.click('form[action="/signin/email"] button')
        mail = await next_mail(app, "maya.rivera@example.com", before)
        R.say("Maya", "on her laptop asks for a sign-in email; opens it on her phone")
        await phone.goto(mail["links"][0])
        phone_text = await phone.text()
        await shot(phone, "13-maya-link-on-the-other-device.jpg")
        R.check("the phone says the laptop can use the code instead", "Signing in on another device?" in phone_text)
        await laptop.type("#code", code_of(mail))
        await laptop.click('form[action="/signin/code"] button')
        await shot(laptop, "14-maya-laptop-signed-in.jpg")
        R.say("Maya", "types the code on the laptop")
        R.check("the laptop is signed in", (await laptop.url()).endswith("/home"))
        await phone.goto(app.cfg.base_url + "/home")
        R.check("the phone is still signed in too", (await phone.url()).endswith("/home"))
        phone_token = (await phone.cookies())["agora_session"]
        R.check("both devices answer to the kernel as Maya",
                kernel_see(kport, phone_token, "look").get("as") ==
                kernel_see(kport, (await laptop.cookies())["agora_session"], "look").get("as") == "Maya R.")

        # 6. The kernel reads the answers --------------------------------------------
        right = 0
        for email, person in people.items():
            account = app.service.account_by_email(email)
            token = tokens.get(email)
            pid = account["kernel_person"]
            seen = kernel_see(kport, token, f"look {pid}") if pid and token else {}
            rows = seen.get("rows") or [{}]
            got = rows[0].get("answers", {})
            # choices are kept in the question's own order, whatever order they were ticked in
            want = {"display_name": person[0], "help": [k for k in HELP if k in person[3]]}
            if person[4]:
                want["neighbourhood"] = person[4]
            ok = all(got.get(k) == v for k, v in want.items()) and (
                bool(person[4]) or got.get("neighbourhood", "") == "")
            right += ok
            if not ok:
                R.check(f"the kernel holds {person[0]}'s answers", False, json.dumps(seen)[:200])
        R.say("kernel", f"read back each person's answers as that person: {right} of {len(people)} match")
        R.check("every neighbour's answers are facts the kernel holds", right == len(people), f"{right}/{len(people)}")
        alex_token = (await alex.cookies())["agora_session"]
        maya_pid = app.service.account_by_email("maya.rivera@example.com")["kernel_person"]
        as_alex = kernel_see(kport, alex_token, f"look {maya_pid}")
        bea_token = tokens["bea.n@example.org"]
        as_bea = kernel_see(kport, bea_token, f"look {maya_pid}")
        R.say("kernel", f"Alex (a leader) reads Maya: {as_alex.get('text', as_alex)}")
        R.say("kernel", f"Bea (a member) reads Maya: {as_bea.get('text', as_bea)}")
        R.check("a leader sees a member's answers", "answers:" in as_alex.get("text", ""))
        R.check("another member does not", "answers:" not in as_bea.get("text", "answers:"))

        # 7. Sign out everywhere ------------------------------------------------------
        await laptop.goto(app.cfg.base_url + "/account")
        await laptop.click_text("button", "Sign out on every device")
        await phone.goto(app.cfg.base_url + "/home")
        R.check("signing out on every device ends the phone's session", (await phone.url()).endswith("/signin"))
        await asyncio.sleep(31)  # the kernel caches a session's answer for 30 s
        after = kernel_see(kport, phone_token, "look")
        R.say("kernel", f"Maya's old phone session, 31 s later: {after}")
        R.check("the kernel stops honouring it within its 30 s cache", after.get("status") == 401)

        # The count -------------------------------------------------------------
        humans = len(people)
        joined = {inv["channel"]: inv["uses"] for inv in app.service.invites()}
        R.say("count", f"{humans} neighbours plus Alex; uses per link: {joined}; bots that got in before the freeze: {bots_in}")
        persons = sum(1 for a in app.store.all("SELECT kernel_person FROM accounts") if a["kernel_person"])
        R.check("every account that answered the questions has a kernel person",
                persons == len(app.store.all("SELECT id FROM accounts WHERE onboarded_at IS NOT NULL")),
                f"{persons} persons")
        R.bots_in, R.humans, R.joined, R.tally = bots_in, humans, joined, tally
    finally:
        await browser.close()
        if kernel:
            kernel.terminate()
            kernel.wait(timeout=10)
        server.shutdown()
        server.server_close()
        google.shutdown()
        google.server_close()
        log = tmp / "kernel.log"
        if not all(ok for _, ok, _ in R.checks) and log.exists():
            R.kernel_log = log.read_text(encoding="utf-8", errors="replace")[-4000:]
        shutil.rmtree(tmp, ignore_errors=True)
    write_report()


def write_report() -> None:
    passed = sum(1 for _, ok, _ in R.checks if ok)
    lines = [
        "> Written by `scenario/evening.py` (sign-in story a13313). Every line below was printed by the run; "
        "nothing is edited by hand. **ran**, " + time.strftime("%d %b %Y %H:%M") + ".",
        "",
        "# An evening of joining",
        "",
        f"**{passed} of {len(R.checks)} checks passed.** {getattr(R, 'humans', '?')} neighbours joined at phone width "
        f"in a hidden browser, each in a browser of their own; a bot flooded one link "
        f"({getattr(R, 'bots_in', '?')} bot accounts got in before the freeze); the kernel read everyone's answers back.",
        "",
        "## Checks",
        "",
        *[f"- {'PASS' if ok else '**FAIL**'}: {what}" + (f" ({detail})" if detail else "") for what, ok, detail in R.checks],
        "",
        "## What happened",
        "",
        "```",
        *R.lines,
        "```",
        "",
        *(["## The kernel's log (kept because a check failed)", "", "```", R.kernel_log, "```", ""]
          if getattr(R, "kernel_log", "") else []),
        "## Screenshots",
        "",
        *[f"- [{name}]({name})" for name in R.shots],
        "",
    ]
    (OUT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\n{passed}/{len(R.checks)} checks passed; report at {OUT / 'report.md'}")


if __name__ == "__main__":
    asyncio.run(evening())
    sys.exit(0 if all(ok for _, ok, _ in R.checks) else 1)
