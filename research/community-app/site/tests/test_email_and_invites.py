"""Joining by invite, signing in by emailed link or code, and the leaders' invite tools."""

from __future__ import annotations

import re

from conftest import LEADER, Client, last_mail, mail_code, make_invite


def test_public_page_is_plain_and_marked_draft(app):
    c = Client(app)
    r = c.get("/")
    assert r.status == 200
    assert "Seabright Neighbours" in r.text
    assert "Draft wording" in r.text
    assert "How to join" in r.text
    # Nothing loaded from anywhere else, no scripts on the public page.
    assert not re.search(r'(src|href)="https?://', r.text)
    assert "<script" not in r.text
    csp = r.header("Content-Security-Policy")
    assert "default-src 'none'" in csp and "frame-ancestors 'none'" in csp


def test_newcomer_joins_through_an_invite_by_emailed_link(app, leader):
    invite = make_invite(leader, "Nextdoor")
    maya = Client(app)
    r = maya.get(f"/join/{invite['code']}")
    assert r.status == 200
    assert "Alex H. invited you to join" in r.text
    maya.email_signin("Maya@Example.com ", invite["code"])
    mail = last_mail(app)
    assert mail["to"] == "maya@example.com"
    assert "join Seabright Neighbours" in mail["subject"]

    # Opening the link only shows a button: mail scanners open links too.
    link = mail["links"][0]
    path = link.split("8817", 1)[1]
    r = maya.get(path)
    assert r.status == 200 and "Continue" in r.text
    assert app.service.account_by_email("maya@example.com") is None

    r = maya.follow_last_link()
    assert r.status == 303 and r.location == "/welcome"
    r = maya.get("/welcome")
    assert "Your name, as neighbours will see it" in r.text
    maya.onboard("Maya R.", ["meetings", "research"])
    r = maya.get("/home")
    assert r.status == 200 and "Hi, Maya" in r.text

    account = app.service.account_by_email("maya@example.com")
    assert account["display_name"] == "Maya R."
    assert app.service.answers(account["id"]) == {
        "display_name": "Maya R.", "help": ["meetings", "research"], "neighbourhood": "Seabright"}
    state = app.service.invite_by_id(invite["id"])
    assert state.invite["uses"] == 1
    people = app.service.invite_people(invite["id"])
    assert [p["email"] for p in people] == ["maya@example.com"]
    page = leader.get(f"/leader/invites/{invite['id']}")
    assert "Maya R." in page.text and "<svg" in page.text


def test_code_works_in_the_tab_that_asked_and_only_there(app, leader, clock):
    invite = make_invite(leader)
    asker, other = Client(app), Client(app)
    asker.email_signin("sam@example.com", invite["code"])
    code = mail_code(last_mail(app))
    # Another browser has no pending request, so the code means nothing there.
    r = other.post("/signin/code", {"code": code})
    assert r.status == 303 and r.location == "/signin"
    r = asker.post("/signin/code", {"code": code[:3] + " " + code[3:]})
    assert r.status == 303 and r.location == "/welcome"


def test_wrong_codes_run_out(app, leader):
    invite = make_invite(leader)
    c = Client(app)
    c.email_signin("sam@example.com", invite["code"])
    good = mail_code(last_mail(app))
    wrong = "000000" if good != "000000" else "111111"
    for _ in range(5):
        r = c.post("/signin/code", {"code": wrong})
        assert r.status == 400
    r = c.post("/signin/code", {"code": good})
    assert r.status == 400 and "Too many tries" in r.text
    assert app.service.account_by_email("sam@example.com") is None


def test_link_is_single_use_and_expires(app, leader, clock):
    invite = make_invite(leader)
    c = Client(app)
    c.email_signin("sam@example.com", invite["code"])
    link = last_mail(app)["links"][0]
    token = link.split("t=", 1)[1]
    assert c.post("/signin/link", {"t": token}).status == 303
    again = Client(app).post("/signin/link", {"t": token})
    assert again.status == 400 and "expired or was already used" in again.text

    c2 = Client(app)
    c2.email_signin("kim@example.com", invite["code"])
    token2 = last_mail(app)["links"][0].split("t=", 1)[1]
    clock.advance(16 * 60)
    assert c2.post("/signin/link", {"t": token2}).status == 400
    assert c2.get("/signin/link?t=" + token2).status == 400


def test_a_new_request_cancels_the_older_link(app, leader):
    invite = make_invite(leader)
    c = Client(app)
    c.email_signin("sam@example.com", invite["code"])
    first = last_mail(app)["links"][0].split("t=", 1)[1]
    c.email_signin("sam@example.com", invite["code"])
    assert c.post("/signin/link", {"t": first}).status == 400
    assert c.follow_last_link().status == 303


def test_no_invite_means_no_account_and_the_page_does_not_tell(app, leader):
    member, stranger = Client(app), Client(app)
    r1 = member.post("/signin/email", {"email": LEADER})
    r2 = stranger.post("/signin/email", {"email": "nobody@example.com"})
    assert (r1.status, r1.location) == (r2.status, r2.location) == (303, "/signin/check")
    p1, p2 = member.get("/signin/check"), stranger.get("/signin/check")
    assert p1.status == p2.status == 200
    same = lambda t: re.sub(r'name="csrf" value="[0-9a-f]+"', "", t)  # noqa: E731 - per browser
    assert same(p1.text.replace(LEADER, "X")) == same(p2.text.replace("nobody@example.com", "X"))
    mail = last_mail(app)
    assert mail["to"] == "nobody@example.com" and mail["links"] == []
    assert "joining is by invite" in mail["text"]
    # The code box does nothing for a request that had no way in.
    assert stranger.post("/signin/code", {"code": "123456"}).status == 400
    assert app.service.account_by_email("nobody@example.com") is None
    # And the form cannot be used to flood someone with these notes.
    before = len(app.mailer.recent(100))
    Client(app).post("/signin/email", {"email": "nobody@example.com"})
    assert len(app.mailer.recent(100)) == before


def test_freezing_one_link_leaves_the_others(app, leader):
    insta = make_invite(leader, "Instagram")
    flyer = make_invite(leader, "Flyer")
    c = Client(app)
    c.email_signin("ana@example.com", insta["code"])  # asked before the freeze
    r = leader.post(f"/leader/invites/{insta['id']}/freeze")
    assert r.status == 303
    assert Client(app).get(f"/join/{insta['code']}").status == 410
    assert Client(app).get(f"/join/{flyer['code']}").status == 200
    r = c.follow_last_link()
    assert r.status == 400 and "invite link has closed" in r.text
    assert app.service.account_by_email("ana@example.com") is None
    assert app.service.invite_by_id(insta["id"]).invite["uses"] == 0

    leader.post(f"/leader/invites/{insta['id']}/unfreeze")
    c.email_signin("ana@example.com", insta["code"])
    assert c.follow_last_link().location == "/welcome"


def test_invite_use_count_and_expiry(app, leader, clock):
    once = make_invite(leader, "One person", max_uses="1", expires_days="1")
    a, b = Client(app), Client(app)
    a.email_signin("a@example.com", once["code"])
    b.email_signin("b@example.com", once["code"])  # both asked while it was open
    link_b = last_mail(app)["links"][0].split("t=", 1)[1]
    a_link = app.mailer.recent()[1]["links"][0].split("t=", 1)[1]
    assert a.post("/signin/link", {"t": a_link}).location == "/welcome"
    r = b.post("/signin/link", {"t": link_b})
    assert r.status == 400 and "closed" in r.text
    assert Client(app).get(f"/join/{once['code']}").status == 410

    day = make_invite(leader, "Meeting", kind="event", expires_days="1")
    clock.advance(86400 + 1)
    r = Client(app).get(f"/join/{day['code']}")
    assert r.status == 410 and "expired" in r.text


def test_existing_member_needs_no_invite(app, leader):
    leader.post("/signout")
    c = Client(app)
    c.email_signin(LEADER)
    assert c.follow_last_link().location == "/home"


def test_leaders_only(app, leader):
    invite = make_invite(leader)
    c = Client(app)
    c.email_signin("pat@example.com", invite["code"])
    c.follow_last_link()
    c.onboard("Pat L.")
    assert c.get("/leader/invites").status == 403
    assert c.post("/leader/invites", {"channel": "x", "kind": "link", "expires_days": "1"}).status == 403
    assert c.post(f"/leader/invites/{invite['id']}/freeze").status == 403
    assert app.service.invite_by_id(invite["id"]).open
    assert "Invites" not in c.get("/home").text


def test_invite_form_checks_its_fields(app, leader):
    for fields, message in [({"channel": ""}, "channel a name"),
                            ({"max_uses": "lots"}, "whole number"),
                            ({"max_uses": "0"}, "between 1"),
                            ({"expires_days": "3"}, "expiry choices")]:
        data = {"channel": "Flyer", "kind": "link", "max_uses": "", "expires_days": "30"}
        data.update(fields)
        r = leader.post("/leader/invites", data)
        assert r.status == 400 and message in r.text, (fields, r.text[-400:])


def test_printable_qr_and_public_join_button(app, leader):
    invite = make_invite(leader, "Galt meeting", kind="event", expires_days="1")
    r = leader.get(f"/leader/invites/{invite['id']}/qr")
    assert r.status == 200 and "Scan to join" in r.text and "<svg" in r.text
    assert app.invite_url(invite) in r.text
    assert Client(app).get("/join").status == 200  # no public link yet: explains invites
    leader.post(f"/leader/invites/{invite['id']}/public")
    r = Client(app).get("/")
    assert f'/join/{invite["code"]}' in r.text
    assert Client(app).get("/join").location == f"/join/{invite['code']}"
    leader.post(f"/leader/invites/{invite['id']}/freeze")
    assert f'/join/{invite["code"]}' not in Client(app).get("/").text


def test_names_are_escaped_everywhere(app, leader):
    invite = make_invite(leader, '<b>Insta</b>')
    c = Client(app)
    c.email_signin("x@example.com", invite["code"])
    c.follow_last_link()
    c.onboard('<script>alert(1)</script>')
    for page in (c.get("/home").text, leader.get(f"/leader/invites/{invite['id']}").text,
                 leader.get("/leader/invites").text):
        assert "<script>alert" not in page and "<b>Insta" not in page
    assert "&lt;script&gt;" in leader.get(f"/leader/invites/{invite['id']}").text


def test_bad_email_is_explained(app):
    r = Client(app).post("/signin/email", {"email": "not-an-address"})
    assert r.status == 400 and "look like an email address" in r.text


def test_racing_for_the_last_uses_lets_in_exactly_that_many(app, leader):
    import threading

    invite = make_invite(leader, "Three seats", max_uses="3", expires_days="1")
    tokens = []
    for i in range(10):
        Client(app).email_signin(f"r{i}@example.com", invite["code"])
        tokens.append(last_mail(app)["links"][0].split("t=", 1)[1])
    results, gate = [], threading.Barrier(10)

    def redeem(token):
        gate.wait()
        try:
            app.service.redeem_token(token)
            results.append("in")
        except Exception as exc:  # noqa: BLE001
            results.append(type(exc).__name__)

    threads = [threading.Thread(target=redeem, args=(t,)) for t in tokens]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert results.count("in") == 3, results
    assert results.count("SignInRefused") == 7, results
    assert app.service.invite_by_id(invite["id"]).invite["uses"] == 3
    assert len(app.service.invite_people(invite["id"])) == 3
