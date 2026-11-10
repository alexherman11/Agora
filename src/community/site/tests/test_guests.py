"""Guest passes from a meeting's QR code, keeping a guest's account, the sign-in link CLI,
live mode without SMTP, and the per-IP switch (5 Nov 2026)."""

from __future__ import annotations

import io
import json
import urllib.parse
from datetime import UTC, datetime, timedelta

import pytest

from agora_entry import config, kernel_client
from agora_entry.__main__ import signin_link
from agora_entry.config import Config
from agora_entry.web import App
from conftest import LEADER, Client, last_mail, mail_code, make_config, make_invite

SECRET = "kernel-secret-for-tests"


def utc(*args) -> float:
    return datetime(*args, tzinfo=UTC).timestamp()


@pytest.fixture
def kernel_calls(app, monkeypatch):
    """Stand in for the kernel's /keep/account: record each call, answer one person per account."""
    calls = []

    def keep_account(url, secret, account, name, invite, answers):
        calls.append({"account": account, "name": name, "invite": invite, "answers": answers})
        return {"person": "p_" + account[-6:], "new": len([c for c in calls if c["account"] == account]) == 1}

    monkeypatch.setattr(kernel_client, "keep_account", keep_account)
    app.cfg.kernel_url = "http://127.0.0.1:1"
    app.cfg.kernel_secret = SECRET
    return calls


def meeting(leader: Client, channel: str = "5 Nov meeting", **fields) -> dict:
    data = {"kind": "event", "expires_days": "1", "guest_ok": "1"}
    data.update(fields)
    return make_invite(leader, channel, **data)


def join_as_guest(app, invite: dict, name: str = "Rosa M.", c: Client | None = None):
    c = c or Client(app)
    page = c.get(f"/join/{invite['code']}")
    assert page.status == 200 and "Your name" in page.text, page.text
    r = c.post(f"/join/{invite['code']}/guest", {"name": name})
    return c, r


def check(app, c: Client) -> dict:
    app.cfg.kernel_secret = SECRET
    token = c.cookies[app.cookie["sid"]]
    r = c.request("POST", "/internal/session/check", body=json.dumps({"token": token}).encode(),
                  ctype="application/json", headers={"X-Kernel-Secret": SECRET})
    assert r.status == 200, r.text
    return json.loads(r.text)


# -- guest passes -------------------------------------------------------------
def test_a_guest_joins_with_just_a_name(app, leader, kernel_calls):
    invite = meeting(leader)
    c, r = join_as_guest(app, invite)
    assert r.status == 303 and r.location == app.cfg.home_path == "/"
    assert app.cookie["sid"] in c.cookies and app.cookie["guest"] in c.cookies
    out = check(app, c)
    rec = out["record"]
    assert out["method"] == "guest" and out["account"] == rec["account_id"]
    assert rec["guest"] is True and rec["guest_until"] == app.service.guest_until()
    assert rec["email"] is None and rec["email_verified"] is False and rec["methods"] == ["guest"]
    assert rec["display_name"] == "Rosa M." and rec["answers"] == {"display_name": "Rosa M."}
    assert rec["invited_through"]["invite_id"] == invite["id"]
    # The kernel was told, like any join, with the invite this service counted.
    assert kernel_calls == [{"account": rec["account_id"], "name": "Rosa M.",
                             "invite": {"invite_id": invite["id"], "channel": "5 Nov meeting",
                                        "maker_account_id": invite["maker_id"]},
                             "answers": {"display_name": "Rosa M."}}]
    assert app.service.invite_by_id(invite["id"]).invite["uses"] == 1
    assert "Rosa" in c.get("/home").text
    # Other members' records say guest: false.
    assert check(app, leader)["record"]["guest"] is False


def test_the_guest_page_offers_sign_in_and_a_full_account(app, leader):
    invite = meeting(leader)
    page = Client(app).get(f"/join/{invite['code']}").text
    assert 'href="/signin"' in page and f'/join/{invite["code"]}?account=1' in page
    full = Client(app).get(f"/join/{invite['code']}?account=1").text
    assert 'name="email"' in full and 'name="name"' not in full


def test_invites_without_guest_ok_take_no_guests(app, leader):
    link = make_invite(leader, "Instagram")
    assert not link["guest_ok"]
    c = Client(app)
    assert 'name="email"' in c.get(f"/join/{link['code']}").text
    r = c.post(f"/join/{link['code']}/guest", {"name": "Bot"})
    assert r.status == 303 and r.location.endswith("?account=1")
    assert app.store.one("SELECT COUNT(*) AS n FROM accounts")["n"] == 1  # the leader only
    # A leader can switch guests on for a link later, and off again.
    leader.post(f"/leader/invites/{link['id']}/guests_on")
    assert app.service.invite_by_id(link["id"]).invite["guest_ok"] == 1
    leader.post(f"/leader/invites/{link['id']}/guests_off")
    assert app.service.invite_by_id(link["id"]).invite["guest_ok"] == 0


def test_a_member_cannot_switch_guests_on(app, leader):
    link = make_invite(leader, "Instagram")
    c, _ = join_as_guest(app, meeting(leader))
    assert c.post(f"/leader/invites/{link['id']}/guests_on").status == 403


@pytest.mark.parametrize("name,ok", [("", False), ("   ", False), ("x" * 61, False),
                                     ("  Ana   Lu  ", True), ("x" * 60, True)])
def test_guest_names_are_1_to_60_characters(app, leader, name, ok):
    invite = meeting(leader)
    c = Client(app)
    c.get(f"/join/{invite['code']}")
    r = c.post(f"/join/{invite['code']}/guest", {"name": name})
    assert (r.status == 303) is ok, r.text
    if not ok:
        assert r.status == 400 and "1 to 60" in r.text and app.cookie["sid"] not in c.cookies
    elif name.strip().startswith("Ana"):
        assert check_name(app) == "Ana Lu"


def check_name(app) -> str:
    return app.store.one("SELECT display_name FROM accounts WHERE guest_until IS NOT NULL")["display_name"]


def test_guest_names_are_escaped(app, leader):
    invite = meeting(leader)
    c, _ = join_as_guest(app, invite, name='<script>alert(1)</script>')
    for page in (c.get("/home").text, leader.get(f"/leader/invites/{invite['id']}").text):
        assert "<script>alert" not in page and "&lt;script&gt;" in page


def test_a_guest_pass_ends_at_the_end_of_the_next_day_in_los_angeles(app, leader, clock):
    invite = meeting(leader, expires_days="90")
    clock.t = utc(2026, 11, 6, 3, 0)  # 5 Nov, 7 pm in Seabright (PST, UTC-8)
    c, _ = join_as_guest(app, invite)
    until = check(app, c)["record"]["guest_until"]
    assert until == utc(2026, 11, 7, 7, 59, 59)  # 6 Nov, 23:59:59 PST
    clock.t = until - 60
    assert c.get("/home").status == 200
    clock.t = until
    assert c.get("/home").location == "/signin"
    assert check(app, c) == {"account": None, "method": None, "agent": None, "record": None}


def test_guest_until_follows_summer_time_and_the_zone_setting(app):
    july = utc(2026, 7, 5, 3, 0)  # 4 Jul, 8 pm PDT (UTC-7)
    assert app.service.guest_until(july) == utc(2026, 7, 6, 6, 59, 59)
    app.cfg.timezone = "America/New_York"
    assert app.service.guest_until(july) == utc(2026, 7, 6, 3, 59, 59)  # 4 Jul 11 pm EDT, so 5 Jul ends


def test_freezing_the_invite_ends_its_guests_at_once(app, leader, clock):
    invite = meeting(leader)
    other = meeting(leader, channel="Flyer")
    rosa, _ = join_as_guest(app, invite)
    theo, _ = join_as_guest(app, other, name="Theo")
    leader.post(f"/leader/invites/{invite['id']}/freeze")
    assert rosa.get("/home").location == "/signin"
    assert check(app, rosa)["account"] is None
    assert theo.get("/home").status == 200  # another invite's guests stay
    assert leader.get("/home").status == 200
    # Unfreezing reopens the link for newcomers, but the frozen-out sessions stay ended.
    leader.post(f"/leader/invites/{invite['id']}/unfreeze")
    assert rosa.get("/home").location == "/signin"


def test_guests_are_rate_limited_per_ip_and_per_invite(tmp_path, clock):
    app = App(make_config(tmp_path, limit_overrides={"guest_ip": 3, "guest_invite": 5}), clock=clock)
    leader = Client(app)
    leader.email_signin(LEADER)
    leader.follow_last_link()
    leader.onboard("Alex H.")
    invite = meeting(leader)
    statuses = [join_as_guest(app, invite, name=f"N{i}")[1].status for i in range(4)]
    assert statuses == [303, 303, 303, 429]
    # The server sees every phone as 127.0.0.1 behind its proxy: SITE_IP_LIMITS=off.
    app.cfg.ip_limits = False
    statuses = [join_as_guest(app, invite, name=f"M{i}")[1].status for i in range(3)]
    assert statuses == [303, 303, 429]  # the per-invite cap (5) still holds


def test_ip_limits_and_every_limit_are_settings(tmp_path):
    env = {"SITE_DATA_DIR": str(tmp_path / "d"), "SITE_IP_LIMITS": "off", "SITE_LIMIT_EMAIL_IP": "500",
           "SITE_LIMIT_GUEST_INVITE": "250"}
    cfg = config.from_env(env, dotenv=tmp_path / "none")
    assert cfg.ip_limits is False and cfg.limit_overrides == {"email_ip": 500, "guest_invite": 250}
    app = App(cfg)
    assert app.limits["email_ip"] == (500, 3600) and app.limits["guest_invite"] == (250, 86400)
    assert app.limits["guest_ip"] == (80, 3600)
    assert all(app.allow("email_ip", "1.2.3.4") for _ in range(600))  # off
    assert [app.allow("email_addr", "a@b.c") for _ in range(6)][-1] is False  # per-address stays
    with pytest.raises(ValueError, match="SITE_IP_LIMITS"):
        config.from_env(dict(env, SITE_IP_LIMITS="nope"), dotenv=tmp_path / "none")
    with pytest.raises(ValueError, match="unknown SITE_LIMIT_"):
        App(config.from_env(dict(env, SITE_LIMIT_TYPO="1"), dotenv=tmp_path / "none"))


# -- keeping a guest's account --------------------------------------------------
def test_a_guest_who_signs_up_by_email_keeps_their_account(app, leader, kernel_calls):
    invite = meeting(leader)
    c, _ = join_as_guest(app, invite)
    guest_id = check(app, c)["account"]
    signin = c.get("/signin")
    assert signin.status == 200 and "guest" in signin.text  # not sent away: they're here to sign up
    c.email_signin("rosa@example.com")
    assert "join" in last_mail(app)["subject"]  # a link, not "you'll need an invite"
    r = c.follow_last_link()
    assert r.status == 303 and r.location == app.cfg.home_path
    out = check(app, c)
    assert out["account"] == guest_id and out["method"] == "email"
    rec = out["record"]
    assert rec["guest"] is False and rec["guest_until"] is None and rec["email"] == "rosa@example.com"
    assert rec["methods"] == ["email"] and rec["display_name"] == "Rosa M."
    assert app.cookie["guest"] not in c.cookies
    assert [k["account"] for k in kernel_calls] == [guest_id, guest_id]  # told again, same account
    # No second use of the invite, and freezing it no longer touches a full member.
    assert app.service.invite_by_id(invite["id"]).invite["uses"] == 1
    leader.post(f"/leader/invites/{invite['id']}/freeze")
    assert c.get("/home").status == 200


def test_the_code_path_keeps_the_account_too_even_after_the_pass_ended(app, leader, clock):
    invite = meeting(leader)
    c, _ = join_as_guest(app, invite)
    guest_id = check(app, c)["account"]
    clock.advance(3 * 86400)  # the pass ended, the claim cookie remains
    assert c.get("/home").location == "/signin"
    c.email_signin("rosa@example.com")
    r = c.post("/signin/code", {"code": mail_code(last_mail(app))})
    assert r.status == 303
    assert app.service.account_by_email("rosa@example.com")["id"] == guest_id


def test_the_claim_runs_out_after_14_days(app, leader, clock):
    invite = meeting(leader)
    c, _ = join_as_guest(app, invite)
    until = check(app, c)["record"]["guest_until"]
    clock.t = until + 14 * 86400 + 1
    c.email_signin("rosa@example.com")
    assert "invite" in last_mail(app)["text"] and not last_mail(app)["links"]
    assert app.service.account_by_email("rosa@example.com") is None


def test_an_existing_email_signs_into_that_account_without_merging(app, leader):
    invite = meeting(leader)
    c, _ = join_as_guest(app, invite)
    guest_id = check(app, c)["account"]
    c.email_signin(LEADER)
    c.follow_last_link()
    assert check(app, c)["account"] == app.service.account_by_email(LEADER)["id"] != guest_id
    guest = app.service.account(guest_id)
    assert guest["email"] is None and guest["guest_until"] is not None  # left as it was


def test_only_the_guests_browser_keeps_the_account(app, leader):
    invite = meeting(leader)
    c, _ = join_as_guest(app, invite)
    c.email_signin("rosa@example.com")
    link = last_mail(app)["links"][0]
    other = Client(app)  # the phone's mail app opened the link in its own browser
    token = urllib.parse.parse_qs(urllib.parse.urlsplit(link).query)["t"][0]
    r = other.post("/signin/link", {"t": token})
    assert r.status == 400 and "browser where you joined as a guest" in r.text
    assert app.service.account_by_email("rosa@example.com") is None


def test_signing_out_drops_the_claim(app, leader):
    c, _ = join_as_guest(app, meeting(leader))
    c.post("/signout")
    assert app.cookie["guest"] not in c.cookies and app.cookie["sid"] not in c.cookies


# -- the sign-in link CLI ---------------------------------------------------
def test_the_cli_prints_a_one_time_link_for_a_leader(tmp_path):
    env = {"SITE_DATA_DIR": str(tmp_path / "var"), "SITE_LEADERS": "alex@example.org"}
    out, err = io.StringIO(), io.StringIO()
    assert signin_link(["Alex@Example.org"], env=env, out=out, err=err, dotenv=tmp_path / "none") == 0
    link = out.getvalue().strip()
    assert link.startswith("http://127.0.0.1:8817/signin/link?t=") and "15 minutes" in err.getvalue()
    app = App(config.from_env(env, dotenv=tmp_path / "none"))
    c = Client(app)
    path = urllib.parse.urlsplit(link)
    page = c.get(f"{path.path}?{path.query}")
    assert page.status == 200 and "another device" not in page.text  # no code to type elsewhere
    token = urllib.parse.parse_qs(path.query)["t"][0]
    r = c.post("/signin/link", {"t": token})
    assert r.status == 303 and r.location == "/welcome"
    assert "leader" in app.service.roles(app.service.account_by_email("alex@example.org")["id"])
    assert Client(app).post("/signin/link", {"t": token}).status == 400  # once only
    assert not (tmp_path / "var" / "outbox" / "outbox.jsonl").exists()  # no mail written


def test_the_cli_refuses_strangers_and_links_expire(app, clock):
    with pytest.raises(ValueError, match="SITE_LEADERS"):
        app.service.mint_signin_link("stranger@example.com")
    link = app.service.mint_signin_link(LEADER)
    token = link.split("t=", 1)[1]
    clock.advance(15 * 60)
    assert Client(app).post("/signin/link", {"t": token}).status == 400
    err = io.StringIO()
    assert signin_link([], err=err) == 2 and "usage" in err.getvalue()


# -- live mode without SMTP or Google -----------------------------------------
def test_an_email_form_posted_while_email_is_off_says_ask_a_leader(app):
    c = Client(app)
    c.get("/signin")  # the form from before, say
    app.mailer = None
    r = c.post("/signin/email", {"email": LEADER})
    assert r.status == 503 and "ask a leader" in r.text


def live_config(tmp_path, **over) -> Config:
    cfg = Config(mode="live", base_url="https://seabright.example.org", host="127.0.0.1",
                 data_dir=tmp_path / "live", content_dir=make_config(tmp_path).content_dir,
                 secret_key=b"s" * 32, email_mode="off", leaders=frozenset({LEADER}))
    for k, v in over.items():
        setattr(cfg, k, v)
    cfg.check()
    return cfg


def test_live_mode_starts_without_smtp_and_says_so(tmp_path, clock):
    cfg = config.from_env({"SITE_MODE": "live", "SITE_BASE_URL": "https://seabright.example.org",
                           "SITE_DATA_DIR": str(tmp_path / "live")}, dotenv=tmp_path / "none")
    assert cfg.email_mode == "off" and cfg.google_mode == "off"
    app = App(cfg, clock=clock)
    assert app.mailer is None and app.google is None
    c = Client(app)
    page = c.get("/signin", headers={"Host": "seabright.example.org"})
    assert "Email sign-in isn’t set up yet" in page.text and 'name="email"' not in page.text
    assert "Continue with Google" not in page.text
    assert not (tmp_path / "live" / "outbox").exists()


def test_live_mode_guests_and_the_cli_link_work_without_smtp(tmp_path, clock):
    app = App(live_config(tmp_path), clock=clock)
    leader = Client(app)
    link = app.service.mint_signin_link(LEADER)
    token = link.split("t=", 1)[1]
    origin = {"Origin": "https://seabright.example.org"}
    assert leader.get("/signin/link?t=" + token).status == 200
    assert leader.post("/signin/link", {"t": token}, headers=origin).location == "/welcome"
    leader.post("/welcome", {"q_display_name": "Alex H.", "q_help": ["meetings"]}, headers=origin)
    r = leader.post("/leader/invites", {"channel": "5 Nov meeting", "kind": "event", "max_uses": "",
                                        "expires_days": "1", "guest_ok": "1"}, headers=origin)
    invite = app.service.invite_by_id(r.location.rsplit("/", 1)[1]).invite
    guest = Client(app)
    guest.get(f"/join/{invite['code']}")
    r = guest.post(f"/join/{invite['code']}/guest", {"name": "Rosa"}, headers=origin)
    assert r.status == 303 and r.location == "/"
    cookie = next(v for k, v in r.headers if k == "Set-Cookie" and v.startswith("__Host-agora_session="))
    assert "Secure" in cookie and "HttpOnly" in cookie
    claim = next(v for k, v in r.headers if k == "Set-Cookie" and v.startswith("__Host-entry_guest="))
    assert "Secure" in claim and "HttpOnly" in claim


def test_live_mode_still_refuses_the_unsafe_combinations(tmp_path):
    with pytest.raises(ValueError, match="stand-in"):
        live_config(tmp_path, google_mode="fake")
    with pytest.raises(ValueError, match="https"):
        live_config(tmp_path, base_url="http://seabright.example.org")
    with pytest.raises(ValueError, match="outbox"):
        live_config(tmp_path, email_mode="file")


# -- routes and the store ----------------------------------------------------
def test_the_mission_page_moved_to_about(app, leader):
    assert Client(app).get("/").location == "/about"
    assert Client(app).get("/about").status == 200
    assert leader.get("/").location == "/home"
    assert leader.get("/signin").location == app.cfg.home_path


def test_site_home_is_a_setting(tmp_path, clock):
    cfg = config.from_env({"SITE_DATA_DIR": str(tmp_path / "d"), "SITE_HOME": "/board"},
                          dotenv=tmp_path / "none")
    assert cfg.home_path == "/board"
    with pytest.raises(ValueError, match="SITE_HOME"):
        config.from_env({"SITE_DATA_DIR": str(tmp_path / "d"), "SITE_HOME": "https://evil.example"},
                        dotenv=tmp_path / "none")


def test_an_old_store_is_migrated_so_guests_fit(tmp_path):
    import sqlite3

    from agora_entry.db import Store
    path = tmp_path / "old.sqlite3"
    old = sqlite3.connect(path)
    old.executescript("""
        CREATE TABLE accounts (id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE,
            email_verified INTEGER NOT NULL DEFAULT 1, google_sub TEXT UNIQUE, display_name TEXT,
            suggested_name TEXT, invite_id TEXT, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL,
            onboarded_at INTEGER, disabled_at INTEGER);
        INSERT INTO accounts(id, email, created_at, updated_at) VALUES ('acct_1', 'a@b.c', 1, 1);
        CREATE TABLE invites (id TEXT PRIMARY KEY, code TEXT NOT NULL UNIQUE, maker_id TEXT NOT NULL,
            channel TEXT NOT NULL, kind TEXT NOT NULL DEFAULT 'link', max_uses INTEGER,
            uses INTEGER NOT NULL DEFAULT 0, expires_at INTEGER NOT NULL, frozen_at INTEGER,
            frozen_by TEXT, created_at INTEGER NOT NULL);
    """)
    old.commit()
    old.close()
    store = Store(path)
    assert store.one("SELECT email FROM accounts WHERE id='acct_1'")["email"] == "a@b.c"
    store.run("INSERT INTO accounts(id, email, created_at, updated_at, guest_until) VALUES"
              " ('acct_2', NULL, 1, 1, 5)")
    store.run("INSERT INTO accounts(id, email, created_at, updated_at, guest_until) VALUES"
              " ('acct_3', NULL, 1, 1, 5)")
    cols = {r["name"] for r in store.all("PRAGMA table_info(invites)")}
    assert "guest_ok" in cols
    Store(path)  # opening again changes nothing


def test_guest_claim_cookie_lasts_past_the_pass(app, leader):
    invite = meeting(leader)
    _, r = join_as_guest(app, invite)
    cookies = {v.split("=", 1)[0]: v for v in r.cookies_set()}
    sid_age = int(cookies[app.cookie["sid"]].split("Max-Age=")[1].split(";")[0])
    claim_age = int(cookies[app.cookie["guest"]].split("Max-Age=")[1].split(";")[0])
    assert claim_age - sid_age == 14 * 86400 and "HttpOnly" in cookies[app.cookie["guest"]]
    assert timedelta(seconds=sid_age) <= timedelta(days=2)
