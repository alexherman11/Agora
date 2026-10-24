"""RS256 checking, the QR encoder, and the seam the kernel reads."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from agora_entry import jwt_rs256, qr
from agora_entry.web import App
from conftest import LEADER, Client, make_config, make_invite


@pytest.fixture(scope="module")
def key():
    return jwt_rs256.generate_key(2048)


def keys_of(key, kid="k1"):
    return {kid: jwt_rs256.jwk_to_key(jwt_rs256.public_jwk(key, kid))}


def test_rs256_round_trip_and_tampering(key):
    token = jwt_rs256.sign({"sub": "1", "n": 1}, key, "k1")
    assert jwt_rs256.verify(token, keys_of(key)) == {"sub": "1", "n": 1}
    head, body, sig = token.split(".")
    forged_body = jwt_rs256.b64url_encode(json.dumps({"sub": "2", "n": 1}).encode())
    for bad in (f"{head}.{forged_body}.{sig}", f"{head}.{body}.{sig[:-4]}AAAA", f"{head}.{body}.",
                f"{head}.{body}", "x.y.z"):
        with pytest.raises(jwt_rs256.TokenError):
            jwt_rs256.verify(bad, keys_of(key))


def test_rs256_refuses_alg_swaps(key):
    # HS256 with the public key as the HMAC secret is the classic confusion attack.
    token = jwt_rs256.sign({"sub": "1"}, key, "k1")
    _, body, sig = token.split(".")
    for alg in ("HS256", "none", "RS512", "rs256"):
        head = jwt_rs256.b64url_encode(json.dumps({"alg": alg, "kid": "k1"}).encode())
        with pytest.raises(jwt_rs256.TokenError, match="only RS256"):
            jwt_rs256.verify(f"{head}.{body}.{sig}", keys_of(key))


def test_rs256_refuses_small_keys():
    small = {"kty": "RSA", "n": jwt_rs256.b64url_encode((2 ** 1023 + 1).to_bytes(128, "big")),
             "e": "AQAB"}
    with pytest.raises(jwt_rs256.TokenError, match="too small"):
        jwt_rs256.jwk_to_key(small)


def test_reed_solomon_matches_the_standards_worked_example():
    # ISO/IEC 18004 Annex I: "01234567" as version 1-M.
    data = [0x10, 0x20, 0x0C, 0x56, 0x61, 0x80, 0xEC, 0x11, 0xEC, 0x11, 0xEC, 0x11, 0xEC, 0x11, 0xEC, 0x11]
    assert qr.rs_remainder(data, 10) == [0xA5, 0x24, 0xD4, 0xC1, 0xED, 0x36, 0xC7, 0x87, 0x2C, 0x55]


FORMAT_M = ["101010000010010", "101000100100101", "101111001111100", "101101101001011",
            "100010111111001", "100000011001110", "100111110010111", "100101010100000"]


@pytest.mark.parametrize("mask", range(8))
def test_format_bits_match_the_published_table(mask):
    m = qr.encode("hi", version=1, mask=mask).modules
    # The copy around the top-left finder, as (x, y), most significant bit first.
    cells = [(0, 8), (1, 8), (2, 8), (3, 8), (4, 8), (5, 8), (7, 8), (8, 8), (8, 7),
             (8, 5), (8, 4), (8, 3), (8, 2), (8, 1), (8, 0)]
    assert "".join("1" if m[y][x] else "0" for x, y in cells) == FORMAT_M[mask]
    # The second copy: bits 0..7 down the right of the top row, 8..14 along the bottom-left.
    n = len(m)
    second = [(8, n - 1 - k) for k in range(7)] + [(n - 8 + k, 8) for k in range(8)]
    assert "".join("1" if m[y][x] else "0" for x, y in second) == FORMAT_M[mask]


def test_tables_are_consistent():
    for ver in range(1, 11):
        ec, groups = qr.BLOCKS_M[ver]
        blocks = sum(n for n, _ in groups)
        assert qr.raw_data_modules(ver) // 8 == qr.data_capacity(ver) + ec * blocks


def test_invite_links_fit_and_draw():
    url = "https://seabright.example.org/join/" + "Ab3dEf9hJkLm"
    sym = qr.encode(url)
    assert sym.ver == 4 and sym.size == 33
    svg = qr.svg(url)
    assert svg.startswith("<svg") and 'viewBox="0 0 41 41"' in svg
    with pytest.raises(ValueError):
        qr.encode("x" * 300)


ARASE = Path("C:/Projects/AgoraMobile/mobile/node_modules/qrcode-terminal/vendor/QRCode")


@pytest.mark.skipif(not (ARASE.is_dir() and shutil.which("node")),
                    reason="needs node and Arase's encoder (in AgoraMobile's node_modules)")
def test_symbols_match_an_independent_encoder():
    script = Path(__file__).with_name("arase_qr.js")
    texts = ["https://seabright.example.org/join/Ab3dEf9hJkLm", "http://127.0.0.1:8817/join/x"]
    jobs = []
    for ver in range(1, 11):
        cap = qr.data_capacity(ver) - (3 if ver >= 10 else 2)  # mode and length bits
        for text in texts + ["~" * cap]:
            jobs += [[ver, mask, text[:cap]] for mask in range(8)]
    out = subprocess.run(["node", str(script), str(ARASE)], input=json.dumps(jobs),
                         capture_output=True, text=True, check=True).stdout
    theirs = json.loads(out)
    assert len(theirs) == len(jobs) == 240
    for (ver, mask, text), rows in zip(jobs, theirs, strict=True):
        mine = ["".join("1" if b else "0" for b in row)
                for row in qr.encode(text, version=ver, mask=mask).modules]
        assert rows == mine, (ver, mask, text)


# -- the seam -----------------------------------------------------------------

@pytest.fixture
def seam_app(tmp_path, clock):
    return App(make_config(tmp_path, kernel_secret="kernel-test-secret"), clock=clock)


def call(c: Client, method: str, path: str, secret: str | None, body: dict | None = None):
    headers = {"Authorization": f"Bearer {secret}"} if secret else {}
    raw = json.dumps(body).encode() if body is not None else None
    return c.request(method, path, headers=headers, body=raw,
                     ctype="application/json" if raw is not None else None)


def test_session_check_turns_a_session_into_a_verified_account(seam_app):
    app = seam_app
    leader = Client(app)
    leader.email_signin(LEADER)
    leader.follow_last_link()
    leader.onboard("Alex H.", ["skills"])
    invite = make_invite(leader, "Flyer")
    maya = Client(app)
    maya.email_signin("maya@example.com", invite["code"])
    maya.follow_last_link()
    maya.onboard("Maya R.", ["meetings"])
    kernel = Client(app)
    sid = maya.cookies[app.cookie["sid"]]
    r = call(kernel, "POST", "/internal/session/check", "kernel-test-secret", {"token": sid})
    assert r.status == 200
    reply = json.loads(r.text)
    assert reply["method"] == "email" and reply["agent"] is None
    record = reply["account"]
    assert record["account_id"].startswith("acct_") and record["email"] == "maya@example.com"
    assert record["email_verified"] is True and record["display_name"] == "Maya R."
    assert record["answers"] == {"display_name": "Maya R.", "help": ["meetings"], "neighbourhood": "Seabright"}
    assert record["invited_through"]["channel"] == "Flyer"
    assert record["invited_through"]["maker_account_id"] == app.service.account_by_email(LEADER)["id"]
    assert "roles" not in record  # what you may do is the kernel's, not ours to hand over

    gone = {"account": None, "method": None, "agent": None}
    r = call(kernel, "POST", "/internal/session/check", "kernel-test-secret", {"token": "nope"})
    assert json.loads(r.text) == gone
    maya.post("/signout")
    r = call(kernel, "POST", "/internal/session/check", "kernel-test-secret", {"token": sid})
    assert json.loads(r.text) == gone

    r = call(kernel, "GET", "/internal/events?after=0", "kernel-test-secret")
    kinds = [e["kind"] for e in json.loads(r.text)["events"]]
    for k in ("account.created", "account.signed_in", "account.onboarded", "invite.made",
              "invite.used", "account.signed_out"):
        assert k in kinds
    last = json.loads(r.text)["events"][-1]["seq"]
    r = call(kernel, "GET", f"/internal/events?after={last}", "kernel-test-secret")
    assert json.loads(r.text)["events"] == []
    text = json.dumps(json.loads(call(kernel, "GET", "/internal/events?after=0", "kernel-test-secret").text))
    assert sid not in text  # no secrets in the event feed


def test_seam_trusts_only_the_secret_on_loopback(seam_app, app):
    for client, secret in ((Client(seam_app), None), (Client(seam_app), "wrong"),
                           (Client(seam_app, remote="10.1.2.3"), "kernel-test-secret"),
                           (Client(app), "anything")):  # no secret configured: seam is shut
        r = call(client, "POST", "/internal/session/check", secret, {"token": "x"})
        assert r.status == 403
        assert call(client, "GET", "/internal/events", secret).status == 403
