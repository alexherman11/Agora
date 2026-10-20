# Music panel — source ready, visual acceptance pending

20 Oct 2026, worker-a6443. This branch resumed at 8b28248; no live panel,
real Spotify account, sign-in profile, media key or desktop shortcut was used.
JEFF's round-3 assembly is landed; his instruction c6981 replaces the original
moving progress requirement with static position updates on playback events.

The PowerShell WinRT helper reads Windows' existing system media session without
installing anything. Album artwork uses the new read-only `media picture` paint
word. The compact and filled lenses use the same event-reported position, time,
transport controls and Like state. No music lens uses `live`, animation or scrolling.
No volume control: the SMTC session interface exposes no volume method.

Like uses Spotify Web API with PKCE and the scopes `user-library-read`,
`user-library-modify`, `user-read-currently-playing`. Each write checks currently
playing metadata again; a title, artist, player or version mismatch refuses it.
Failed writes never fill the heart. Expired cached states become unknown.
Duplicate titles/artist names are not unique identifiers: this conservatively
checks Windows metadata against Spotify's currently-playing URI, not a track search.
The desktop shortcut route was rejected because it would need real modifier input
and Spotify focus; it was never tried. No alternative Windows API offers Spotify
library membership, so there is no truthful account-free Like route here.

Connect is an explicit host action, not a startup action. It opens a nonce-protected
loopback form for the app's Client ID, then Spotify consent with S256 PKCE.
The private store is the ignored `research/text-desk-lab/notation/house-state/spotify/`.
The client ID is public; authorization codes and access/refresh tokens never enter
the world or chat. The fake tests override both endpoints and the store.

After JEFF's go, the only account setup Alex must do:

1. Create a Web API app in [Spotify's dashboard](https://developer.spotify.com/dashboard)
   and add redirect `http://127.0.0.1:8797/callback`.
2. Press **Connect Spotify** in Music, paste the app's **Client ID** (no secret),
   and approve Spotify's consent page.

Development Mode requires the app owner to have Premium. No password is entered
into Agora. No real Connect attempt has been made; live Like is unverified and
unavailable until app registration and consent.

## Ran

- `test_spotify_like.py`: all ok, loopback fake only. Includes setup/CSRF, PKCE,
  private scratch store, scopes, read/like/unlike/idempotency, failed write,
  refresh/revocation, 403, title/artist/remaster/player mismatches, stale state,
  real host Like/Unlike and stubbed asynchronous Connect/duplicate suppression.
- `test_media.py --logic-only`: 0 failed. Static positions, wall-clock invariance,
  seek/pause/unknown duration, artwork path, capabilities, shuffle/repeat.
- `home-music/test_panel.py`: all ok. Both forms compile in a fresh in-memory
  desk, with real allowed-folder generated PNG, three heart states and four
  playback positions (0, 60, 150, end). Empty states compile. No clock/scroll.
- `test_scene.test_live_words_now_and_newest_first`: passed, including media picture.
- Full `test_scene.py`: first 31 tests passed, then Windows PermissionError
  writing `base@walk.pickle` inside tempfile's owner-only system-temp directory.
  This is not a full scene-suite pass.
- `stage.py frontier-try --as worker-a6443 --lens home-music --size 2560x1440
  shot screen-music-compact.png`: fake session/backend started; screen.py failed
  before browser launch at copytree into system-temp `screen-door-.../desk-shell`,
  WinError 5. **No shot exists; no browser or pixel acceptance is claimed.**
  This old branch predates main's shared inherited-ACL temp repair.
- `health.py frontier-try`: **failed**, world e13652, 13644 events, total 86.2s.
  Python and JavaScript parsing passed; 93 help notes true to code; frozen
  worlds 0 differ in the golden form. Many suites hit system-temp ACL errors;
  door timed out, textedit lock timed out, paint checks failed without a page.
  `test_reach` separately reported 4 failures. Live-copy lenses: 66 compile,
  3 unexpected refusals (home-base/home-search/home-tiling need `arrows`,
  which is on newer main), 1 expected refusal. This is **not** a whole-host pass;
  the house must merge main and judge these independently of the music tests.

## Remaining verification and apply

The house must merge current main and run its checks. Browser-capable reviewer:
run `home-music/stage.py` on `frontier-try`, `--as worker-a6443`, `--size 2560x1440`,
`--scale 1.5`, with `--lens home-music` and `--lens home-music-full`; also run
`--empty`, `--signed-out`. The stage installs the draft lenses into its throwaway
copy before painting. Press Like/Unlike against fake Spotify and use
`js "stage({position: 150})"`; confirm static position changes, no clocks/scrollbars,
artwork, focus guard and no layout overflow. The stage refuses `--live` and
`--on-screen`, and blocks Connect so it cannot open Alex's browser.

Source first, then JEFF applies the world lenses/styles. `put.py` rebuilds edits
from the text it reads and refuses an unfamiliar filled-panel body. Its updated
boundary preserves the scrolling commission's `share 1 / scroll scroll` and
uses the larger music form only for the actually filled panel, not pinned panels.
Re-read and save the current live notes immediately before any apply; the live
tiling boundary was read, not changed, on this commission.

## Read

- [Spotify PKCE](https://developer.spotify.com/documentation/web-api/tutorials/code-pkce-flow)
- [Library saves](https://developer.spotify.com/documentation/web-api/reference/save-library-items)
- [2026 migration](https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide)
- [Redirect rules](https://developer.spotify.com/documentation/web-api/concepts/redirect_uri)
- [Windows session interface](https://learn.microsoft.com/en-us/uwp/api/windows.media.control.globalsystemmediatransportcontrolssession)

SMTC helper code and API surface were read. Real SMTC metadata/art/control calls,
real consent, real Spotify library writes and Alex's screen were **not run**.
