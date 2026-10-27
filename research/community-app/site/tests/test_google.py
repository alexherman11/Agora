"""Continue with Google, against the local stand-in over real HTTP on loopback."""

from __future__ import annotations

import urllib.parse

import pytest

from agora_entry import jwt_rs256
from agora_entry.fake_google import StandIn, serve_in_thread
from agora_entry.web import App
from conftest import LEADER, Client, free_port, make_config, make_invite


@pytest.fixture(scope="module")
def other_key():
    return jwt_rs256.generate_key(2048)


@pytest.fixture
def google(tmp_path, clock):
    port = free_port()
    issuer = f"http://127.0.0.1:{port}"
    cfg = make_config(tmp_path, google_mode="fake", google_client_id="stand-in-client",
                      google_client_secret="stand-in-secret", google_auth_url=issuer + "/authorize",
                      google_token_url=issuer + "/token", google_jwks_url=issuer + "/certs",
                      google_issuers=(issuer,))
    stand_in = StandIn("stand-in-client", "stand-in-secret", cfg.base_url + "/auth/google/callback",
                       issuer, clock=clock)
    server = serve_in_thread(stand_in, port)
    app = App(cfg, clock=clock)
    yield app, stand_in
    server.shutdown()
    server.server_close()


def start(c: Client, invite_code: str = "") -> dict:
    r = c.get("/auth/google/start" + (f"?invite={invite_code}" if invite_code else ""))
    assert r.status == 303
    url = urllib.parse.urlsplit(r.location)
    return dict(urllib.parse.parse_qsl(url.query))


def google_signin(app, stand_in, c: Client, email: str, name: str = "Maya Rivera",
                  invite_code: str = "", state: str | None = None):
    q = start(c, invite_code)
    code = stand_in.issue_code(q["nonce"], q["code_challenge"], email, name)
    return c.get(f"/auth/google/callback?state={state or q['state']}&code={code}")


def test_start_asks_for_code_flow_with_pkce_state_and_nonce(google):
    app, _ = google
    q = start(Client(app))
    assert q["response_type"] == "code" and q["code_challenge_method"] == "S256"
    assert set(q["scope"].split()) == {"openid", "email", "profile"}
    assert len(q["state"]) >= 32 and len(q["nonce"]) >= 32 and len(q["code_challenge"]) == 43
    assert q["redirect_uri"] == "http://127.0.0.1:8817/auth/google/callback"
    assert "code_verifier" not in q


def test_newcomer_continues_with_google(google):
    app, stand_in = google
    leader = Client(app)
    leader.email_signin(LEADER)
    leader.follow_last_link()
    leader.onboard("Alex H.")
    invite = make_invite(leader, "Instagram")
    c = Client(app)
    assert "Continue with Google" in c.get(f"/join/{invite['code']}").text
    r = google_signin(app, stand_in, c, "Maya@Example.com", invite_code=invite["code"])
    assert r.status == 303 and r.location == "/welcome", r.text
    assert 'value="Maya Rivera"' in c.get("/welcome").text  # prefilled from Google, theirs to change
    account = app.service.account_by_email("maya@example.com")
    assert account["google_sub"] and account["invite_id"] == invite["id"]
    c.onboard("Maya R.")
    c.post("/signout")
    r = google_signin(app, stand_in, c, "maya@example.com")  # back again, no invite needed
    assert r.location == "/home"


def test_google_without_invite_is_refused(google):
    app, stand_in = google
    r = google_signin(app, stand_in, Client(app), "stranger@example.com")
    assert r.status == 400 and "invite" in r.text
    assert app.service.account_by_email("stranger@example.com") is None


def test_google_joins_an_existing_email_account(google):
    app, stand_in = google
    c = Client(app)
    c.email_signin(LEADER)
    c.follow_last_link()
    before = app.service.account_by_email(LEADER)
    c.post("/signout")
    r = google_signin(app, stand_in, c, LEADER)
    after = app.service.account_by_email(LEADER)
    assert r.status == 303 and after["id"] == before["id"] and after["google_sub"]


def test_callback_must_come_back_to_the_browser_that_started(google):
    app, stand_in = google
    c, attacker = Client(app), Client(app)
    q = start(c)
    code = stand_in.issue_code(q["nonce"], q["code_challenge"], LEADER, "Alex")
    # Login CSRF: the attacker's callback URL opened in someone else's browser.
    r = attacker.get(f"/auth/google/callback?state={q['state']}&code={code}")
    assert r.status == 400
    r = c.get(f"/auth/google/callback?state=wrong&code={code}")
    assert r.status == 400
    assert app.service.account_by_email(LEADER) is None


def test_flow_is_single_use_and_short_lived(google, clock):
    app, stand_in = google
    c = Client(app)
    q = start(c)
    flow_cookie = c.cookies[app.cookie["flow"]]
    code = stand_in.issue_code(q["nonce"], q["code_challenge"], LEADER, "Alex")
    assert c.get(f"/auth/google/callback?state={q['state']}&code={code}").status == 303
    c.cookies[app.cookie["flow"]] = flow_cookie
    assert c.get(f"/auth/google/callback?state={q['state']}&code={code}").status == 400

    d = Client(app)
    q = start(d)
    clock.advance(11 * 60)
    code = stand_in.issue_code(q["nonce"], q["code_challenge"], LEADER, "Alex")
    assert d.get(f"/auth/google/callback?state={q['state']}&code={code}").status == 400


def test_cancel_at_google_is_gentle(google):
    app, _ = google
    c = Client(app)
    q = start(c)
    r = c.get(f"/auth/google/callback?state={q['state']}&error=access_denied")
    assert r.status == 200 and "cancelled" in r.text


@pytest.mark.parametrize("tamper", [
    {"claims": {"aud": "someone-else"}},
    {"claims": {"iss": "https://evil.example"}},
    {"claims": {"exp": 1}},
    {"claims": {"iat": 9_999_999_999}},
    {"claims": {"nonce": "replayed"}},
    {"claims": {"email_verified": False}},
    {"claims": {"azp": "someone-else"}},
    {"alg_none": True},
    {"kid": "unknown-kid"},
    "other_key",
], ids=["aud", "iss", "exp", "iat", "nonce", "unverified", "azp", "alg-none", "kid", "forged"])
def test_bad_id_tokens_are_refused(google, other_key, tamper):
    app, stand_in = google
    stand_in.tamper = {"key": other_key} if tamper == "other_key" else tamper
    r = google_signin(app, stand_in, Client(app), LEADER)
    assert r.status == 502, r.text
    assert app.service.account_by_email(LEADER) is None


def test_wrong_pkce_verifier_is_refused_by_the_provider(google):
    app, stand_in = google
    c = Client(app)
    q = start(c)
    code = stand_in.issue_code(q["nonce"], "A" * 43, LEADER, "Alex")  # someone else's challenge
    assert c.get(f"/auth/google/callback?state={q['state']}&code={code}").status == 502


def test_google_button_hidden_without_keys(app):
    r = Client(app).get("/signin")
    assert "Continue with Google" not in r.text
    assert Client(app).get("/auth/google/start").status == 404
