> Built by Claude for the sign-in story (Board a13313, epic a13308), 23 October 2026. All wording on the pages is placeholder draft copy for Alex to rewrite; it states no facts about the campaign. Claims below are labelled **ran**, **read** or **imagined**.

# Entry: the public site and signing in

The front door of the community place: a plain public site (mission, what we are doing, how to join), invite links, and signing in with Google or an emailed link, then a couple of questions. It says who you are. What you may do inside the place is the kernel's (story a13310); the hand-over between the two is [SEAM.md](SEAM.md).

## Run it (test mode)

From the repository root:

```bash
C:/Projects/Agora4/.venv/Scripts/python.exe research/community-app/site/run.py
```

Or start `community-entry` from `.claude/launch.json` in the app's browser pane. It opens no windows. Then open <http://127.0.0.1:8817>.

- Test mode listens on `127.0.0.1:8817` only and sends no email: messages go to `var/outbox/` and appear at <http://127.0.0.1:8817/dev/outbox>, with a button for the link.
- The test leader is `leader@example.com`. Sign in as them, make an invite at **Invites**, then open the invite link after signing out.
- Without Google keys, "Continue with Google" goes to a local stand-in on port 8818, a plain yellow test page that is clearly not Google. With `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`, it goes to Google.
- Data lives in `var/` (ignored by git): `entry.sqlite3`, `secret.key` (made on first run) and the outbox. Delete `var/` to start fresh.

**The evening** (the main evidence, about 70 s; nothing appears on screen): a headless browser plays about 30 neighbours joining through three invite links, a bot flooding one of them, a leader freezing it, and someone signing in on two devices, against this service, the Google stand-in and the real kernel (`research/kernel-lab`) in its own process. It writes `evidence/evening/report.md` and screenshots there.

```bash
C:/Projects/Agora4/.venv/Scripts/python.exe research/community-app/site/scenario/evening.py
```

Unit tests underneath (78, about 30 s):

```bash
C:/Projects/Agora4/.venv/Scripts/python.exe -m pytest research/community-app/site/tests -q -p no:cacheprovider
```

## What Alex must provide

1. **The first leaders.** `SITE_LEADERS=` with your email address in `site/.env`. Leaders sign in without an invite and make the first invites.
2. **A Google OAuth client.** In Google Cloud console: a project, then the consent screen ("Branding"): app name, support email, homepage `https://seabright.example.org/`, privacy policy `https://seabright.example.org/privacy`, authorized domain `example.org`. Then a "Web application" client with these redirect URIs:
   - `https://seabright.example.org/auth/google/callback`
   - `http://127.0.0.1:8817/auth/google/callback`, to try real Google locally

   Put `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` into `site/.env`. Only `openid email profile` are asked for, so there is no sensitive-scope review. Google does check the brand: the domain must be verified in Google Search Console (a TXT record at Cloudflare), and the homepage must describe the app and link the privacy policy (**read**: Google Cloud Help, "OAuth app verification", 23 Oct). The public site already does both.
3. **An email provider with SMTP**, for example Postmark or Resend (both send sign-in mail well and have free tiers). Verify the sending domain with their DNS records (SPF, DKIM, and a DMARC record) at Cloudflare, then put `EMAIL_SMTP_HOST`, `EMAIL_SMTP_PORT`, `EMAIL_SMTP_USER`, `EMAIL_SMTP_PASSWORD` and `EMAIL_FROM` into `.env`.
4. **The domain** `seabright.example.org`: a DNS record at Cloudflare pointing at the server (that is the deploy story). If Cloudflare proxies it, set `SITE_PROXY_IP_HEADER=CF-Connecting-IP`, and let the server accept traffic only from Cloudflare, or rate limits can be dodged.
5. **Wording.** Rewrite the public site (`content/site.json`), the questions (`content/questions.json`) and the privacy page (`content/privacy.json`), then set `"draft": false` in `site.json` to remove the draft banner. The privacy page's promises (who sees answers, deleting on request) are yours to make.
6. **Later, for the kernel:** `KERNEL_SHARED_SECRET`, any long random string, in both services' settings.

`.env.example` lists every setting. Nothing else is needed for test mode.

## Why plain Python

The pinned Python and its standard library only: WSGI, `sqlite3`, `hmac`, `secrets`, `smtplib`, `urllib`. No framework and no new packages, because:
- nothing has to be installed on the server beyond Python, and nothing of Alex's shared venv changes;
- the whole service is small enough to read (about 3,100 lines of Python; the largest files are routes, pages and the account rules, at about 500 each), which matters for the piece that guards sign-in;
- the app is a plain WSGI callable, so the deploy story can put it behind any WSGI server.

The cost is two pieces of the standard library's missing crypto written here and tested hard: RS256 checking of Google's ID token (`jwt_rs256.py`) and a QR encoder (`qr.py`). Both are below.

## How it works

- **Invites.** A leader makes one link per channel ("Instagram", "Nextdoor", "25 Oct meeting"), each with a maker, a use count (unlimited or a maximum), an expiry (1 day to 1 year) and a record of who came through it. Freezing one link leaves every other link open, and unfreezing reopens it. An event invite has a printable QR poster. One invite can be put on the public site as its Join button. A use counts only when an account is made, in the same transaction as the account.
- **Ways in.** "Continue with Google" is OpenID Connect's code flow with `state`, `nonce` and PKCE (S256). The nonce, verifier and invite stay on the server, keyed to a 10-minute cookie, so a callback opened in another browser finds nothing. The ID token's signature, issuer, audience, `azp`, expiry, `iat`, nonce and `email_verified` are all checked. **Emailed sign-in** sends a link and a 6-digit code: the link works on any device, and the code works in the tab that asked, for when a phone's mail app opens links in its own browser. Both work once, for 15 minutes, and asking again cancels the older ones. The link opens a "Continue" button rather than signing in, because mail scanners open links too. Five wrong codes end the request. There are no passwords.
- **Nothing says whether an address is a member.** The page after "Email me a link" is the same for everyone. The email tells the truth: a link, or "you'll need an invite". The "you'll need an invite" note goes to an address at most once a day, so the form can't be used to flood someone.
- **Questions.** They are data in `content/questions.json`: text, one choice or many choices, with help text and placeholders. Leaders can reword them without code. The loader refuses any question that asks where someone lives, and requires a `display_name` question, because real names are shown in chat. Google's name is offered as a starting point.
- **Sessions.** These are random cookies, stored only as hashes: `HttpOnly`, `SameSite=Lax`, and `__Host-` plus `Secure` on https. They last 90 days at most and end after 30 idle days. "Sign out" and "sign out on every device" are both there. A new sign-in always gets a new session.
- **CSRF.** Every form carries a token tied to a per-browser cookie, and every POST whose browser sends an `Origin` must come from the site's own origin.
- **Rate limits** (fixed windows, in the store, so they survive restarts):

  | What | Limit |
  |---|---|
  | sign-in emails | 5 per address and 60 per IP an hour (a meeting's whole room shares one wifi address) |
  | codes | 30 per IP an hour |
  | Google starts | 30 per IP every 10 minutes |
  | invite pages | 120 per IP an hour |
  | invites made | 100 per leader a day |

- **Headers.** A strict CSP (`default-src 'none'`, own styles and one small optional script), `frame-ancestors 'none'`, `nosniff`, `no-referrer` (sign-in links never leak in a Referer), HSTS on https, and `no-store` on every page. The server log never prints query strings. Any other host name is redirected to the one configured address.
- **The public site** works with no JavaScript at all. The only script is the invite page's optional Copy button. It is phone-first, light, uses system fonts, and loads nothing from elsewhere.

## Files

| Path | What |
|---|---|
| `agora_entry/web.py` | routes, cookies, CSRF, rate limits, headers |
| `agora_entry/service.py` | accounts, invites, sign-in requests, sessions (no HTTP) |
| `agora_entry/oidc.py`, `jwt_rs256.py` | Google sign-in and ID-token checking |
| `agora_entry/fake_google.py` | the local Google stand-in, for test mode and tests |
| `agora_entry/pages.py`, `templates/`, `static/` | pages, escaped by default (`render.py`) |
| `agora_entry/questions.py` | loads and checks the questions |
| `agora_entry/qr.py` | QR codes as SVG |
| `agora_entry/seam.py` | `may`, the account record, and `/internal/*` for the kernel |
| `agora_entry/mailer.py` | the outbox file (test) or SMTP (live) |
| `agora_entry/kernel_client.py` | the call into the kernel when someone joins (`/keep/account`) |
| `scenario/evening.py`, `cdp.py`, `qr_read.py` | the evening in a hidden browser, the browser driver, and the QR reader |
| `content/` | site copy, questions and privacy page, all data |
| `tests/` | the tests, and `arase_qr.js` for the QR cross-check |
| `evidence/` | screenshots from the browser pane, and `evidence/evening/` from the scenario, 23 Oct |

## Evidence

**ran** (23 Oct, `scenario/evening.py`, the report is [evidence/evening/report.md](evidence/evening/report.md)): **49 of 49 checks passed**, in two of the last three runs (the third is explained below).
- **Setup.** Alex signed in on his phone by emailed link and made three invites: Instagram, a flyer QR code for the Galt Elementary meeting, and a one-use link for Sam. The flyer's QR code was read back from the printed poster's pixels (`scenario/qr_read.py`) and carried the flyer's link.
- **The kernel.** Its world was founded with Alex as steward, in its own process on its own port.
- **Joining.** 29 neighbours joined at phone width (390×844), each in a browser of their own, by Google (stand-in), by tapping the emailed link, or by typing the emailed code. The 12 at the meeting shared one wifi address.
- **The flood.** A bot flooding the Instagram link got **14 accounts in** before Alex saw it. On his Invites page the link said "26 in the last hour" in red, on the first screen. He froze it: nobody came in through it afterwards, the bot met a closed link, and the flyer and Sam's link kept working.
- **People caught by the freeze.** Rosa had asked for her code just before the freeze, so it was refused after. Theo found the link paused. Both came in by the flyer instead. Sam's link turned away the friend he forwarded it to.
- **Two devices.** Maya asked on her laptop and opened the email on her phone. The phone said to type the code on the laptop, and she did; both devices were then signed in as her, to this service and to the kernel. "Sign out on every device" ended the phone's session here, and the kernel stopped honouring it within its 30-second cache.
- **Answers.** All 29 people's answers were read back from the kernel, each by that person through the kernel's own door. A leader saw a member's answers; another member did not.
- **What it changed here:**
  - The page for a link opened on another device now says to type the code there. Before, pressing Continue on the phone used up the request, so the laptop's code stopped working.
  - The leaders' Invites page lists the links first, with "N in the last hour" on each, because the flood was below the form on a phone.
  - The per-IP email limit went from 20 to 60 an hour, because a meeting shares one address.
  - The scenario also caught that the kernel adds `/internal/` to its entry address itself (SEAM.md section 3).
- One run failed while the kernel builder was editing their tree: no one became a kernel person. A direct call to their door a minute later worked, and so did the next run. A failed run now keeps the kernel's log in its report, and this service prints the kernel's reason when it can't reach it.

**ran** (23 Oct, on this machine):
- `pytest tests` (the unit tests underneath): **78 passed**. Besides the list below, they cover a link opened on another device, the per-IP limit at 60, and the QR reader reading every mask at versions 1, 4, 7 and 10 and refusing one flipped module. They cover:
  - the invite → email link → questions → home flow, and the code path, which works only in the asking browser;
  - five wrong codes ending a request, links working once and expiring at 15 minutes, a new request cancelling the old link;
  - no account without an invite, identical pages for members and strangers, and the once-a-day limit on "you need an invite" notes;
  - freezing one link leaving the others open, a request made before a freeze being refused after it, max uses, and expiry;
  - ten threads racing for a three-use invite letting exactly 3 in;
  - leader-only pages, escaping of names and channels, CSRF (no token, a wrong token, another browser's token, a foreign Origin), and rate limits with their reset;
  - sign-out, sign-out everywhere, a stolen cookie dying at sign-out, idle and absolute session expiry, and a new session on each sign-in;
  - questions as data (rewording and new questions work; address questions are refused);
  - the settings refusing unsafe combinations (stand-in in live mode, http in live mode, test mode off loopback);
  - Google against the stand-in over real HTTP on loopback: the flow, an existing email account being joined, no invite meaning no account, login CSRF, a replayed or late flow, cancel, a wrong PKCE verifier, and ten bad ID tokens (wrong `aud`, `iss`, `azp` or nonce; expired; from the future; unverified email; `alg: none`; unknown key; forged with another key), all refused;
  - RS256 tampering and alg swaps (`HS256`, `none`);
  - the seam's session check, account record and event feed, which carries no secrets, and its refusals.
- **QR:** the Reed-Solomon output matches ISO/IEC 18004's worked example ("01234567", 1-M), and the format bits match the published table for all 8 masks. All **240** symbols (versions 1–10, 8 masks, 3 texts each) are identical, module for module, to Kazuhiko Arase's independent encoder (found in `AgoraMobile`'s `node_modules`; that test skips where it is absent).
- **In the app's browser pane, phone size (375×812) and desktop (1280 wide):** went through the public page, then signing in by email via the outbox, the questions, home, making an invite, the invite page with its QR, the printable poster, signing out, and joining through the invite with the Google stand-in (the name came back prefilled). The page never scrolled sideways (`scrollWidth` 375 = `innerWidth` 375), and the console showed no errors, so nothing was blocked by the CSP. Screenshots are in `evidence/`.

**read:**
- Google Cloud Help, "OAuth app verification" (brand verification, homepage and privacy policy, authorized domains verified in Search Console);
- the kernel's `SHAPE.md`, section 3 and Appendix A, and `kernel.py`'s `join` (uncommitted, 23 Oct).

**Not verified:**
- real Google (no keys yet), and real SMTP delivery (no provider yet);
- any phone's camera scanning the QR codes. The encoder matches another encoder bit for bit, and the reader written here reads the printed poster's pixels, but both follow my reading of the standard. A real phone has not scanned one.
- behaviour behind Cloudflare, and load. The test server is the standard library's threaded one; for 200 people it is probably enough (**imagined**), and the deploy story may put it behind a sturdier WSGI server.

## Not done yet

- **Freezing doesn't remove who already came in.** The bot's 14 accounts are members and kernel persons until a leader switches each off, and nothing here does that yet (`disabled_at` exists, unused). Proposed on the Board's IDEAS card (a13437, c13545): "freeze and sweep", and a flood alarm per link (c13546).
- Moving invites into the world (the kernel's later phase), and `/keep/may`: agreed in SEAM.md, not built.
- Agent keys (SEAM.md section 7).
- Google's own button artwork, which their guidelines ask for once real keys are in. Today it is a plain text button.
