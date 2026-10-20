"""test_spotify_like.py: Like, against a fake Spotify (fake_spotify.py), never the real one (a6443). 17 Oct 2026.

    python research/window-lab/test_spotify_like.py

The whole route: connect (PKCE, the consent page answered by a stand-in browser), the heart's state, like, unlike,
an expired token renewed, a revoked sign-in, Premium's 403, another song on the account, another player, and the host
verbs media.like / media.unlike as the home base answers them. The store is a scratch folder; every address is the
fake's (checked first), so nothing reaches Spotify or Alex's library.
"""
import shutil
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fake_spotify      # noqa: E402
import host_verbs        # noqa: E402
import media             # noqa: E402
import spotify_like as sl  # noqa: E402

fails = []


def check(what, ok, got=""):
    print(("ok   " if ok else "FAIL ") + what + ("" if ok else f"   (got {got!r})"))
    if not ok:
        fails.append(what)


fake = fake_spotify.Fake()
store = Path(tempfile.mkdtemp(prefix="spotify-like-"))
lib = sl.Library(store=store, api=fake.url + "/v1", accounts=fake.url, fresh=0)
assert lib.api.startswith("http://127.0.0.1") and lib.accounts.startswith("http://127.0.0.1"), "not the fake"
CID = "0123456789abcdef0123456789abcdef"
T, A = "Night Drive", "Stand-in Band"
try:
    st = lib.state_of(T, A)
    check("before connecting, the heart is unknown and says the steps", st[0] == "unknown" and "developer.spotify.com" in st[1], st)
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
    said = lib.connect(fake_spotify.browser, CID, port=8799, wait=10)
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
    check("a remaster's tail still matches", lib.check(T, A)["liked"] == "no")
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
    lib2.connect(fake_spotify.browser, CID, port=8799, wait=10)
    first = lib2.state_of(T, A)
    time.sleep(0.5)
    check("state_of answers at once (asking), then knows", first == ("unknown", "asking Spotify") and lib2.state_of(T, A)[0] == "no",
          (first, lib2.state_of(T, A)))
finally:
    fake.close()
    shutil.rmtree(store, ignore_errors=True)

print(f"{'all ok' if not fails else str(len(fails)) + ' failed'}: like, against the fake Spotify")
sys.exit(1 if fails else 0)
