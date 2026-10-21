# Spotify connection diagnosis — 21 October

Worker-a8009; source base bb5be76. **The reported boundary is an unreachable
local page after entering the ID; the historical cause is not established.**
No production status/store/profile, account, device or session-file query was
used. No listener, browser, token exchange, media control or live apply ran.

## What the existing flow supports (read)

`host_verbs._connect` starts `spotify_connect.connect` on an explicit press.
With no saved Client ID it opens a local setup form on a temporary loopback
port. The link in that form opens Spotify's developer dashboard; creating an
app there does not submit its ID back to Agora.

The user must return to that setup form, paste the app's **Client ID**, and press
**Continue to Spotify**. That next step opens Spotify consent using S256 PKCE.
No client secret belongs in Agora. Its requested scopes are
`user-library-read user-library-modify user-read-currently-playing`.

The production callback is `http://127.0.0.1:8797/callback`. The temporary
`/setup?state=...` URL is not the developer app's redirect address.
The code checks callback state, exchanges the code, then saves the sign-in and
Client ID. A Client ID alone is neither consent nor a connected account.

Official sources read:

- [PKCE flow](https://developer.spotify.com/documentation/web-api/tutorials/code-pkce-flow):
  Client ID, S256 challenge/verifier and the same redirect in both requests.
- [Redirect rules](https://developer.spotify.com/documentation/web-api/concepts/redirect_uri):
  HTTP is allowed for explicit loopback IP literals; `localhost` is disallowed.
  The documented dynamic-port exception exists; this implementation defaults
  to the fixed callback above.
- [Quota modes](https://developer.spotify.com/documentation/web-api/concepts/quota-modes):
  development app owner needs Premium; users need allowlisting for API access.
  Neither prerequisite was inspected or changed on Alex's account.

## Proven failure paths, not a diagnosis of Alex (ran/read)

1. The setup form closes after 300 seconds, including time spent creating the
   developer app. Its old browser tab then cannot submit to that server.
   Reproduced in memory by advancing the clock past its deadline.
2. A failed browser-open return value is ignored and becomes the same timeout.
   Reproduced with an opener returning `False`.
3. All exceptions in the host Connect worker become the same public
   “Spotify did not connect” message. Setup timeout and a synthetic OS error
   both reproduce it; raw private exception text remains hidden.
4. The ID is saved only after successful token exchange. Consequently failed
   first consent can require returning to the Client ID form next time.
5. The form has a nonce check. A forged submission is refused; a correct fake
   submission advances to the consent method. A saved fake ID skips setup but
   still invokes consent. The actual PKCE method emits the expected callback,
   scopes and verifier without a secret in the fake exchange.

Command run:
`C:/Projects/Agora4/.venv/Scripts/python.exe research/window-lab/test_spotify_connect_diagnosis.py`

Latest run printed **Ran 11 tests in 0.015s — OK**. All HTTP servers and browser launches were
in-memory doubles. Sockets, HTTP transport and private-store reads/writes were
blocked by assertions; fixture sign-in persistence was mocked. These tests
characterize existing behavior and must be revised alongside a repair.
They are not browser/Guard evidence or evidence of connection on the real PC.

## Alex's answer and the listener boundary

JEFF relayed Alex's answer on c8084 (m8081/e17261): after entering his ID,
he reached a local link that could not be found and suspected its server
was not running. This is user-reported evidence, not a captured HTTP error.
The once-only question has been answered; do not request a callback URL,
which could contain an authorization code.

There are **two different local servers** (read; lifecycle exercised in memory):

| Stage | Opens / closes | Consequence |
| --- | --- | --- |
| Client ID form, random loopback port, `/setup` | Bound before its tab opens; closes after valid POST or after 300 seconds | An old setup tab cannot submit after expiry. A successful POST deliberately closes this server. |
| Spotify return, fixed `127.0.0.1:8797/callback` | Bound after setup closes, **before** Spotify consent opens; closes on a matching response or after another 300 seconds | A late return, reload after completion, or wrong local port may have no listener. |

The normal flow does not open consent before binding the callback. Mocked
callback bind failure proves consent is not launched and no exchange is
attempted. A timeout proves closure without exchange. Wrong path returns
HTTP 404 while the listener is alive; wrong state returns a rejection and
continues waiting. Thus “could not be found” alone cannot distinguish a dead
listener from a live listener's 404 or a different local URL. No mismatch in
Alex's registered redirect was inspected or established. Official redirect
rules require matching the registered redirect (subject to their documented
loopback-port exception); this implementation supplies the fixed address above.

Host route (read): the staged normal/full lenses call `host media.connect`;
`desk-shell/lens.js` requires `window.pywebview.api.host`, `hud.Api.host`
dispatches to `host_verbs.call`, which invokes `_connect`. A plain browser has
no such host bridge. The mock dispatch test confirms duplicate presses do not
create parallel flows and failure releases the process-local lock. **This does
not establish the running HUD's loaded version or availability at the failure.**
An attempted Desk `table witnessed:host` was refused as unsupported selection
syntax; no live capability result was obtained, and no alternate host query ran.

Additional five probes cover the two-listener sequence, callback bind failure,
callback timeout, wrong path/state, and real host dispatch/duplicate/failure
release. They do not recreate Alex's account or developer settings. The
existing socket-based `test_spotify_like.py` was read, not run; no listener was
needed for this diagnosis.

## Smallest repair / next step for JEFF

There is no evidence to justify a dashboard change, client secret, port change
or host restart. The smallest certain repair is diagnostic: replace the host's
single generic failure with allowlisted stage/reason messages, distinguishing
setup expiry, callback bind failure, callback timeout, browser launch failure,
consent refusal, exchange failure and persistence failure. Do not expose raw
exceptions, provider response bodies, URLs, state or codes. Check the opener's
False result and errors; use fixed public wording. Explain the finite expiry
on the setup form and leave a fresh **Connect Spotify** recovery in the panel.
Keep finite listeners and duplicate-flow protection.

**Proposed, not implemented:** these receipts would let one separately
authorised explicit Connect press establish the next failure boundary. Do not
automatically retry, exchange a code, start a listener or restart the host.
JEFF must obtain narrow approval for a real retry. No further fact from Alex
is requested here. No production source change, live UI patch or activation
is included; the black standalone panel and layout are untouched.
