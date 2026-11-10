"""Sessions, sign-out, CSRF, rate limits, headers, the questions as data, and settings."""

from __future__ import annotations

import json

import pytest

from agora_entry import config, questions
from agora_entry.config import Config
from agora_entry.web import App
from conftest import LEADER, Client, make_config, make_invite


def test_cookies_are_httponly_lax_and_secure_on_https(tmp_path, clock):
    app = App(make_config(tmp_path), clock=clock)
    assert Client(app).get("/about").cookies_set() == []  # the front page sets nothing
    r = Client(app).get("/signin")
    cookie = r.cookies_set()[0]
    assert "HttpOnly" in cookie and "SameSite=Lax" in cookie and "Secure" not in cookie

    live = Config(mode="live", base_url="https://seabright.example.org", host="127.0.0.1",
                  data_dir=tmp_path / "live", content_dir=app.cfg.content_dir, secret_key=b"s" * 32,
                  email_mode="smtp", smtp_host="smtp.example.com", email_from="x@example.com")
    live.check()
    live_app = App(live, clock=clock, mailer=app.mailer)
    r = Client(live_app).get("/signin")
    cookie = r.cookies_set()[0]
    assert cookie.startswith("__Host-entry_csrf=") and "Secure" in cookie and "Path=/" in cookie
    assert "Domain" not in cookie
    assert r.header("Strict-Transport-Security")


def test_every_response_has_safety_headers(app, leader):
    for path in ("/", "/about", "/signin", "/nope", "/home", "/leader/invites", "/entry-static/site.css"):
        r = leader.get(path)
        assert r.header("X-Content-Type-Options") == "nosniff", path
        assert r.header("Referrer-Policy") == "no-referrer", path
        assert r.header("X-Frame-Options") == "DENY", path
        assert r.header("Content-Security-Policy"), path
    assert leader.get("/home").header("Cache-Control") == "no-store"


def test_posts_need_the_csrf_token_and_our_origin(app, leader):
    invite = make_invite(leader)
    r = leader.post(f"/leader/invites/{invite['id']}/freeze", csrf=False)
    assert r.status == 403
    r = leader.post(f"/leader/invites/{invite['id']}/freeze", {"csrf": "0" * 64})
    assert r.status == 403
    r = leader.post(f"/leader/invites/{invite['id']}/freeze", headers={"Origin": "https://evil.example"})
    assert r.status == 403
    assert app.service.invite_by_id(invite["id"]).open
    # A token from another browser is no good either.
    other = Client(app)
    r = leader.post(f"/leader/invites/{invite['id']}/freeze", {"csrf": other.csrf()})
    assert r.status == 403
    assert leader.post(f"/leader/invites/{invite['id']}/freeze").status == 303


def test_sign_in_requests_are_rate_limited(app):
    c = Client(app)
    for _ in range(5):
        assert c.post("/signin/email", {"email": LEADER}).status == 303
    assert c.post("/signin/email", {"email": LEADER}).status == 429
    # Many addresses from one place run into the per-address-of-sender limit.
    d = Client(app, remote="10.0.0.9")
    statuses = [d.post("/signin/email", {"email": f"p{i}@example.com"}).status for i in range(65)]
    assert statuses.count(303) == 60 and statuses[-1] == 429  # 60: a meeting's whole room shares one wifi


def test_rate_limit_window_resets(app, clock):
    c = Client(app)
    for _ in range(5):
        c.post("/signin/email", {"email": LEADER})
    assert c.post("/signin/email", {"email": LEADER}).status == 429
    clock.advance(3600)
    assert c.post("/signin/email", {"email": LEADER}).status == 303


def test_sign_out_and_sign_out_everywhere(app, leader):
    phone = Client(app)
    phone.email_signin(LEADER)
    phone.follow_last_link()
    assert phone.get("/home").status == 200
    leader.post("/signout")
    assert leader.get("/home").location == "/signin"
    assert phone.get("/home").status == 200
    laptop = Client(app)
    laptop.email_signin(LEADER)
    laptop.follow_last_link()
    laptop.post("/signout", {"everywhere": "1"})
    assert phone.get("/home").location == "/signin"
    assert laptop.get("/home").location == "/signin"


def test_session_cookie_from_before_sign_out_is_dead(app, leader):
    sid = leader.cookies[app.cookie["sid"]]
    leader.post("/signout")
    thief = Client(app)
    thief.cookies[app.cookie["sid"]] = sid
    assert thief.get("/home").location == "/signin"


def test_sessions_end_when_idle_or_old(app, leader, clock):
    clock.advance(29 * 86400)
    assert leader.get("/home").status == 200  # touching it keeps it alive
    clock.advance(29 * 86400)
    assert leader.get("/home").status == 200
    clock.advance(31 * 86400)
    assert leader.get("/home").location == "/signin"  # 31 idle days

    c = Client(app)
    c.email_signin(LEADER)
    c.follow_last_link()
    for _ in range(4):
        clock.advance(25 * 86400)
        r = c.get("/home")
    assert r.location == "/signin"  # 100 days: past the 90-day limit even when used


def test_a_fresh_session_each_sign_in(app, leader):
    before = leader.cookies[app.cookie["sid"]]
    leader.email_signin(LEADER)
    leader.follow_last_link()
    assert leader.cookies[app.cookie["sid"]] != before


def test_welcome_needs_a_name_and_drops_unknown_choices(app, leader):
    invite = make_invite(leader)
    c = Client(app)
    c.email_signin("n@example.com", invite["code"])
    c.follow_last_link()
    r = c.post("/welcome", {"q_display_name": "   ", "q_help": ["meetings"]})
    assert r.status == 400 and "Please fill this in" in r.text
    assert 'checked' in r.text  # their choice is kept
    assert c.get("/home").location == "/welcome"
    r = c.post("/welcome", {"q_display_name": "Nia", "q_help": ["meetings", "sneaky"]})
    account = app.service.account_by_email("n@example.com")
    assert app.service.answers(account["id"])["help"] == ["meetings"]
    r = c.post("/welcome", {"q_display_name": "x" * 61})
    assert c.get("/account").status == 200


def test_member_can_change_their_details(app, leader):
    r = leader.post("/account", {"q_display_name": "Alex Herman", "q_help": ["skills"]})
    assert r.location == "/account?saved=1"
    page = leader.get("/account?saved=1").text
    assert "Saved." in page and 'value="Alex Herman"' in page


def test_questions_are_data_and_never_ask_where_you_live(tmp_path):
    base = json.loads((make_config(tmp_path).content_dir / "questions.json").read_text(encoding="utf-8"))
    questions.parse(base)
    for bad in ({"key": "home", "label": "Your home address", "type": "text"},
                {"key": "street", "label": "Which street?", "type": "text"},
                {"key": "spot", "label": "Spot", "type": "text", "help": "Where do you live?"},
                {"key": "zip", "label": "ZIP", "type": "text"}):
        doc = json.loads(json.dumps(base))
        doc["questions"].append(bad)
        with pytest.raises(questions.QuestionsError, match="never ask where someone lives"):
            questions.parse(doc)
    no_name = {"questions": [q for q in base["questions"] if q["key"] != "display_name"]}
    with pytest.raises(questions.QuestionsError, match="display_name"):
        questions.parse(no_name)


def test_a_leader_can_reword_questions_without_code(tmp_path, clock):
    content = tmp_path / "content"
    content.mkdir()
    src = make_config(tmp_path).content_dir
    for name in ("site.json", "privacy.json"):
        (content / name).write_text((src / name).read_text(encoding="utf-8"), encoding="utf-8")
    (content / "questions.json").write_text(json.dumps({"version": 2, "intro": "One thing.", "questions": [
        {"key": "display_name", "label": "What should we call you?", "type": "text", "required": True},
        {"key": "pronouns", "label": "Pronouns", "type": "choice",
         "options": [{"value": "she", "label": "she/her"}, {"value": "they", "label": "they/them"}]},
    ]}), encoding="utf-8")
    app = App(make_config(tmp_path, content_dir=content), clock=clock)
    c = Client(app)
    c.email_signin(LEADER)
    c.follow_last_link()
    assert "What should we call you?" in c.get("/welcome").text
    c.post("/welcome", {"q_display_name": "Alex", "q_pronouns": "they"})
    account = app.service.account_by_email(LEADER)
    assert app.service.answers(account["id"]) == {"display_name": "Alex", "pronouns": "they"}


def test_settings_refuse_unsafe_combinations(tmp_path):
    good = dict(base_url="http://127.0.0.1:8817", data_dir=tmp_path, secret_key=b"x" * 32)
    with pytest.raises(ValueError, match="loopback"):
        Config(mode="test", host="0.0.0.0", **good).check()
    with pytest.raises(ValueError, match="https"):
        Config(mode="live", email_mode="smtp", smtp_host="h", email_from="f", **good).check()
    live = dict(good, base_url="https://seabright.example.org")
    with pytest.raises(ValueError, match="stand-in"):
        Config(mode="live", google_mode="fake", email_mode="smtp", smtp_host="h", email_from="f", **live).check()
    with pytest.raises(ValueError, match="EMAIL_SMTP_HOST"):
        Config(mode="live", email_mode="smtp", **live).check()
    with pytest.raises(ValueError, match="never to the outbox"):
        Config(mode="live", email_mode="file", **live).check()  # live mode writes no mail anywhere
    Config(mode="live", email_mode="off", **live).check()  # no SMTP yet is allowed (5 Nov)
    with pytest.raises(ValueError, match="SITE_HOME"):
        Config(mode="test", home_path="//evil.example", **good).check()
    with pytest.raises(ValueError, match="SITE_TIMEZONE"):
        Config(mode="test", timezone="Mars/Olympus", **good).check()
    with pytest.raises(ValueError, match="secret"):
        Config(mode="test", base_url="http://127.0.0.1:1", data_dir=tmp_path, secret_key=b"").check()


def test_settings_from_env_and_dotenv(tmp_path):
    dotenv = tmp_path / ".env"
    dotenv.write_text("# Alex writes this\nGOOGLE_CLIENT_ID=abc.apps.googleusercontent.com\n"
                      "GOOGLE_CLIENT_SECRET='shh'\nSITE_LEADERS=A@x.com, b@y.com\n", encoding="utf-8")
    cfg = config.from_env({"SITE_DATA_DIR": str(tmp_path / "d")}, dotenv=dotenv)
    assert cfg.google_mode == "real" and cfg.google_client_secret == "shh"
    assert cfg.google_auth_url.startswith("https://accounts.google.com/")
    assert cfg.leaders == {"a@x.com", "b@y.com"}
    assert (tmp_path / "d" / "secret.key").is_file()
    again = config.from_env({"SITE_DATA_DIR": str(tmp_path / "d")}, dotenv=dotenv)
    assert again.secret_key == cfg.secret_key  # kept across restarts, so sessions survive
    stand_in = config.from_env({"SITE_DATA_DIR": str(tmp_path / "d")}, dotenv=tmp_path / "none")
    assert stand_in.google_mode == "fake" and stand_in.google_auth_url.startswith("http://127.0.0.1:8818")
    assert stand_in.leaders == {"leader@example.com"}


def test_outbox_page_is_test_mode_and_loopback_only(app):
    assert Client(app).get("/dev/outbox").status == 200
    assert Client(app, remote="192.168.1.20").get("/dev/outbox").status == 404


def test_mail_is_written_as_eml(app):
    Client(app).post("/signin/email", {"email": LEADER})
    files = list((app.cfg.data_dir / "outbox").glob("*.eml"))
    assert len(files) == 1
    raw = files[0].read_bytes()
    assert b"To: leader@example.com" in raw and b"multipart/alternative" in raw


def test_tokens_stay_out_of_the_store(app, leader):
    leader.email_signin(LEADER)
    mail = app.mailer.recent()[0]
    token = mail["links"][0].split("t=", 1)[1]
    code = "".join(ch for ch in mail["text"].split("sign-in page: ")[1][:7] if ch.isdigit())
    sid = leader.cookies[app.cookie["sid"]]
    raw = b"".join(p.read_bytes() for p in app.cfg.data_dir.glob("entry.sqlite3*"))
    assert b"leader@example.com" in raw  # the files do hold the data we looked through
    for secret in (token, sid):
        assert secret.encode() not in raw
    rows = app.store.all("SELECT code_hash FROM email_requests")
    assert all(code not in (r["code_hash"] or "") for r in rows)


def test_other_host_names_are_sent_to_the_one_address(app):
    r = Client(app).get("/join/abc?x=1", headers={"Host": "localhost:8817"})
    assert r.status == 308 and r.location == "http://127.0.0.1:8817/join/abc?x=1"
    assert Client(app).get("/about", headers={"Host": "127.0.0.1:8817"}).status == 200


def test_privacy_page_is_there_for_googles_consent_screen(app):
    r = Client(app).get("/privacy")
    assert r.status == 200 and "What we never keep" in r.text
    assert 'href="/privacy"' in Client(app).get("/about").text
