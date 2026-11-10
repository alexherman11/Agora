"""test_spotify_like.py: Like, against a fake Spotify (fake_spotify.py), never the real one (a6443). 17 Oct 2026.

    python src/desktop/test_spotify_like.py

The whole route: connect (PKCE, the consent page answered by a stand-in browser), the heart's state, like, unlike,
an expired token renewed, a revoked sign-in, Premium's 403, another song on the account, another player, and the host
verbs media.like / media.unlike as the home base answers them. The store is a scratch folder; every address is the
fake's (checked first), so nothing reaches Spotify or Alex's library.
"""
import shutil
import sys
import os
import uuid
import urllib.parse
import urllib.request
import re
import threading
from unittest.mock import patch
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fake_spotify      # noqa: E402
import host_verbs        # noqa: E402
import media             # noqa: E402
import spotify_like as sl  # noqa: E402
import spotify_connect

fails = []


def check(what, ok, got=""):
    print(("ok   " if ok else "FAIL ") + what + ("" if ok else f"   (got {got!r})"))
    if not ok:
        fails.append(what)


fake = fake_spotify.Fake()
store = HERE / ".tmp-agora" / ("spotify-like-" + uuid.uuid4().hex)
os.makedirs(store, exist_ok=True)
lib = sl.Library(store=store, api=fake.url + "/v1", accounts=fake.url, fresh=0)
assert lib.api.startswith("http://127.0.0.1") and lib.accounts.startswith("http://127.0.0.1"), "not the fake"
CID = "0123456789abcdef0123456789abcdef"
T, A = "Night Drive", "Stand-in Band"
try:
    st = lib.state_of(T, A)
    check("before connecting, the heart is unknown and says so in one line", st == ("unknown", sl.SHORT), st)
    try:
        lib.set(T, A, True)
        check("before connecting, a like is refused", False, "liked")
    except sl.Refused as e:
        check("before connecting, a like is refused", "not connected" in str(e), str(e))
    try:
        lib.connect(fake_spotify.browser, "not an id", port=0)
        check("a wrong client id is refused", False)
    except sl.Refused as e:
        check("a wrong client id is refused", "client id" in str(e), str(e))
    def setup_browser(url):
        if "/setup?" not in url:
            return fake_spotify.browser(url)
        page = urllib.request.urlopen(url, timeout=10).read().decode()
        state = re.search(r'name="state" value="([^"]+)"', page)[1]
        target = url.split("?", 1)[0]
        bad = urllib.parse.urlencode({"state": "wrong", "client_id": CID}).encode()
        try:
            urllib.request.urlopen(target, bad, timeout=10)
            check("setup rejects a forged form", False)
        except urllib.error.HTTPError as e:
            check("setup rejects a forged form", e.code == 400)
        form = urllib.parse.urlencode({"state": state, "client_id": CID}).encode()
        urllib.request.urlopen(target, form, timeout=10).read()

    said = spotify_connect.connect(lib, setup_browser, port=0, wait=10)
    check("connect: consent, code traded with the PKCE verifier", said.startswith("connected") and lib.connected(), said)
    tok = (store / "token.json").read_text()
    check("the tokens are in the house's store only", "refresh_token" in tok and lib.client_id() == CID)
    check("connect asked for exactly the three scopes",
          any(c[1] == "/authorize" and c[2].get("scope") == sl.SCOPES and c[2].get("code_challenge_method") == "S256" for c in fake.calls))

    check("an unliked song reads no", lib.check(T, A)["liked"] == "no")
    check("like: saved to Liked Songs", lib.set(T, A, True) == "saved to Liked Songs" and "spotify:track:fake0001" in fake.liked, fake.liked)
    check("it was a PUT /me/library with the URI", ("PUT", "/v1/me/library", {"uris": "spotify:track:fake0001"}) in fake.calls)
    check("a liked song reads yes", lib.check(T, A)["liked"] == "yes")
    check("like again says already", lib.set(T, A, True).startswith("already"))
    check("unlike: removed", lib.set(T, A, False) == "removed from Liked Songs" and not fake.liked, fake.liked)

    # Refuse at the actual write after both preceding reads succeeded.
    old_call = lib.call
    def reject_write(method, path, *args, **kwargs):
        if method == "PUT":
            raise sl.Refused("Spotify refused the write")
        return old_call(method, path, *args, **kwargs)
    with patch.object(lib, "call", reject_write):
        try:
            lib.set(T, A, True)
            check("a failed write cannot fill the heart", False)
        except sl.Refused:
            check("a failed write cannot fill the heart", lib.known[(T, A)]["liked"] == "no" and not fake.liked)

    fake.expire()
    check("an expired token is renewed and the call goes on", lib.check(T, A)["liked"] == "no"
          and any(c[0] == "POST" and c[2].get("grant_type") == "refresh_token" for c in fake.calls))
    fake.fail = [403]
    k = lib.check(T, A)
    check("Premium's 403 is said plainly", k["liked"] == "unknown" and "Premium" in k["why"], k)
    fake.playing = {**fake.playing, "name": "Another Song", "uri": "spotify:track:fake0002"}
    k = lib.check(T, A)
    check("another song on the account: unknown, never a guess", k["liked"] == "unknown" and "another song" in k["why"], k)
    try:
        lib.set(T, A, True)
        check("...and a like then is refused", False)
    except sl.Refused:
        check("...and a like then is refused", "spotify:track:fake0002" not in fake.liked)
    fake.playing = {**fake.playing, "name": "Night Drive (2024 Remaster)", "uri": "spotify:track:fake0001"}
    check("a different remaster refuses to guess", lib.check(T, A)["liked"] == "unknown")
    fake.playing = {**fake.playing, "name": T, "artists": [{"name": "Other Artist"}]}
    check("same title with a different artist refuses to guess", lib.check(T, A)["liked"] == "unknown")
    try:
        lib.set(T, A, True)
        check("wrong artist cannot modify the library", False)
    except sl.Refused:
        check("wrong artist cannot modify the library", not fake.liked)
    fake.playing = {**fake.playing, "artists": [{"name": A}]}
    check("another player: unknown, says which", lib.state_of(T, A, "Edge") == ("unknown", "the song is playing in Edge; Liked Songs is Spotify's"))

    # the host verbs, as the home base answers them, with a stand-in session (what Windows says is playing)
    class Ses:
        def start(self):
            return True

        def state(self, wait=0):
            return {"ok": True, "s": {"app": "Spotify.exe", "title": T, "artist": A, "status": "Playing"}}

    class Hud:
        said = 0

        def say_desktop(self):
            Hud.said += 1

    media.SESSION, media.LIKES = Ses(), lib
    r = host_verbs.call(Hud(), "media.like")
    check("host media.like saves it", r == "ok saved to Liked Songs" and "spotify:track:fake0001" in fake.liked, r)
    r = host_verbs.call(Hud(), "media.unlike")
    check("host media.unlike removes it", r == "ok removed from Liked Songs" and not fake.liked, r)
    lib.forget()
    r = host_verbs.call(Hud(), "media.like")
    check("signed out, host media.like is refused with the steps", r.startswith("ERR") and "developer.spotify.com" in r, r)
    # state_of answers at once and asks in the background
    lib2 = sl.Library(store=store, api=fake.url + "/v1", accounts=fake.url)
    lib2.connect(fake_spotify.browser, CID, port=0, wait=10)
    first = lib2.state_of(T, A)
    time.sleep(0.5)
    check("state_of answers at once (asking), then knows", first == ("unknown", "asking Spotify") and lib2.state_of(T, A)[0] == "no",
          (first, lib2.state_of(T, A)))
    lib2.known[(T, A)]["at"] = 0
    check("a stale heart becomes unknown while refreshed", lib2.state_of(T, A) == ("unknown", "asking Spotify"))
    time.sleep(0.1)

    # The actual host Connect button returns immediately. No real browser opens.
    entered, release, done = threading.Event(), threading.Event(), threading.Event()
    def connect_stub(library, browser):
        entered.set()
        release.wait(3)
        return "connected"
    class ConnectHud:
        def say_desktop(self):
            done.set()
    with patch.object(spotify_connect, "connect", connect_stub):
        r = host_verbs.call(ConnectHud(), "media.connect")
        check("host Connect starts the explicit flow", r == "ok opening Spotify connection" and entered.wait(1), r)
        r = host_verbs.call(ConnectHud(), "media.connect")
        check("double Connect cannot open two flows", "already open" in r, r)
        release.set()
        check("Connect refreshes the panel when finished", done.wait(2))

    # A revoked refresh token must not leave a trusted green heart.
    fake.refresh.clear()
    fake.expire()
    revoked = lib2.check(T, A)
    check("revoked consent is unknown with a reconnect explanation",
          revoked["liked"] == "unknown" and "connect again" in revoked["why"])
finally:
    lib.stop()
    fake.close()
    shutil.rmtree(store, ignore_errors=True)

print(f"{'all ok' if not fails else str(len(fails)) + ' failed'}: like, against the fake Spotify")
sys.exit(1 if fails else 0)
