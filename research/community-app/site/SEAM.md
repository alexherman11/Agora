> Draft by Claude, sign-in story (Board a13313), 23 October 2026, for the kernel story (a13310) to answer under "Notes from the kernel" at the end. Written after reading the kernel's `SHAPE.md` (section 3 and Appendix A) and `kernel.py`'s `join`, both uncommitted on 23 Oct. Claims are labelled **ran**, **read** or **imagined**.

# The seam between signing in and the kernel

**Sign-in says who you are. The kernel says what you may do.** An account is proof that someone controls an email address or a Google identity. A person is who they are inside the place. The entry service holds accounts; the kernel holds persons and keeps only the map from account id to person.

The kernel's proposal (SHAPE, Appendix A) and what I built mostly agree. Below, each point says whether it is **built** here, **agreed** but waiting for the kernel's side, or **open**.

## 1. Who holds what

| The entry service holds | The kernel holds |
|---|---|
| accounts: id, email, Google subject, name, answers | persons, groups, roles, the world |
| sign-in requests, Google flows, sessions | account id → person (its part of the keep) |
| invites, for now (section 5) | invites, once it can (section 5) |
| the `roles` table, a stand-in for `may` (section 6) | who may use which word |

Neither stores the other's secrets. Emails stay in the entry store and never enter the world log unless a person adds one. The entry store is the sign-in half of what the kernel calls the keep, and it is never copied by a fork.

## 2. What a verified account hands over (built)

```json
{
  "account_id": "acct_k3m9…",
  "email": "maya@example.com",
  "email_verified": true,
  "display_name": "Maya R.",
  "answers": {"display_name": "Maya R.", "help": ["meetings"], "neighbourhood": "Seabright"},
  "questions_version": 1,
  "onboarded": true,
  "disabled": false,
  "created_at": 1790000000,
  "invited_through": {"invite_id": "inv_…", "channel": "Nextdoor", "maker_account_id": "acct_…"},
  "methods": ["email", "google"],
  "issuer": "https://seabright.example.org"
}
```

- `account_id` is `acct_` and 20 random characters. It never changes and is never reused, even when the email address or name changes. Bind persons to it, never to the email.
- `email` is lower-cased and proven: by a link or code sent to it, or by Google saying `email_verified`. A Google sign-in with the same address as an existing account joins that account.
- `display_name` is the real name shown in chat, from the first question. Leaders can reword the questions (`content/questions.json`); `display_name` is the one key that must exist.
- `answers` are keyed by question key. Values are strings or lists of option values. `questions_version` says which wording they answered.
- `invited_through` is null for leaders who came in through `SITE_LEADERS`.
- `methods` lists the ways this account can sign in. An emailed link always works.
- There are no roles in the record. What someone may do is the kernel's to say (**ran**: a test asserts `roles` is absent).

## 3. How the kernel trusts it (built)

- **Only through `/internal/`, only from loopback, only with the shared secret** (`Authorization: Bearer <KERNEL_SHARED_SECRET>`, compared in constant time). With no secret set, the seam is shut. The public proxy must never forward `/internal/*`.
- **Never from the browser.** The kernel reads the session cookie and asks; anything a page puts in its body (`as=`) is ignored, as SHAPE already says.
- The cookie is `__Host-entry_sid` on https (`entry_sid` in test mode): HttpOnly, SameSite=Lax, Path=/, so the kernel on the same origin receives it. Sessions last 90 days at most and end after 30 idle days, at sign-out, at "sign out on every device", or when the account is switched off.
- Caching the answer for at most 30 s, as the kernel proposes, is fine: sign-out reaches the kernel within 30 s.

| Endpoint | Answer |
|---|---|
| `POST /internal/session/check {"token": "<cookie value>"}` | `{"account": record, "method": "email" or "google", "agent": null}`, or all three null |
| `GET /internal/accounts/<account_id>` | `{"account": record}` |
| `GET /internal/events?after=<seq>&limit=<n>` | events, oldest first: `account.created`, `account.signed_in`, `account.onboarded`, `account.updated`, `account.linked`, `account.signed_out`, `invite.made`, `invite.used`, `invite.frozen`, `invite.unfrozen`, `site.public_invite`. No tokens, cookies or IP addresses in them. |

The path is the kernel's `/session/check`, put under `/internal/` so the proxy can block one prefix.

**ran**: `tests/test_crypto_qr_seam.py` signs a person in, checks their session through the seam, signs them out and sees `null`; reads the event feed and finds no session token in it; and gets 403 with no secret, a wrong secret, a non-loopback address, or when the service has no secret set.

## 4. Joining (agreed, not built)

The kernel proposes `POST /keep/account {account, name, invite, answers}` → `{person, new}` or a refusal, called by the entry service. Agreed, with one change of moment: the call happens **when the welcome questions are answered**, not at first sign-in, because before then there is no name and no answers. Until the kernel says yes, the account exists (the proof) and the person does not. A refusal is shown to the person in the kernel's words, which are already written for people ("invite frozen: a leader has stopped this link").

I will build the call once the kernel serves the route; today `join` is a Python method and no HTTP route exists (**read**: `kernel.py`, 23 Oct). Building a client against my guess of the route would only test my guess.

## 5. Invites (open: who counts)

The kernel proposes invites as world things, so a leader freezes a link with a word and the trust web is visible. I agree; it is the better home. Two things have to hold through the move:

1. **Exactly one side counts uses.** Today the entry service counts a use when it creates the account, in the same transaction, so two people racing for the last use cannot both get in (**ran**: ten threads redeeming sign-in links at once on a three-use invite let exactly 3 in, in each of 3 runs). The kernel's `join` also decrements `uses_left` on its own invite thing (**read**: `kernel.py`). If both count, every join counts twice.
2. **A signed-out stranger must see the invite before any account exists**: whether it is open, and the maker's name ("Alex H. invited you to join").

So, two phases:

- **Now:** the entry service owns invites. `/keep/account` carries `invite: {"invite_id", "code", "channel", "maker_account_id"}` that the entry service has already checked and counted; the kernel records `joined_via` and does not count.
- **Later**, when the kernel's invites exist: the entry service asks `POST /keep/invite {code}` → `{status: open|frozen|expired|full|missing, maker_name}` before showing the join page, stops counting, and the kernel counts in `join`. The leaders' pages (make, freeze, QR) become kernel words and views; the entry service keeps the join page and the QR drawing.

The kernel builder decides when to switch.

## 6. Who may (built as a stand-in)

The entry service asks one question, `may(account, word)`, for four words: `invite.list`, `invite.make`, `invite.freeze`, `site.public_invite`. Today the local `roles` table answers it, and only `SITE_LEADERS` puts anyone in it (`seam.py`). When the kernel can answer, either `POST /keep/may {account, word}` → `{may}`, or the leaders' pages move into the kernel (section 5, later), and this table goes away.

## 7. Agents (a correction, and open)

The kernel's notes say the entry service keeps "agent sessions too" (SHAPE section 3). It doesn't, and my naming caused that reading: the `sessions.agent` column held the browser's User-Agent string. It is now `user_agent`. There are no agent sessions yet, so `session/check` always answers `"agent": null`.

A proposal (**imagined**): a person makes a key for their agent on their account page, labelled ("Maya's helper"); the entry service stores the key's hash, and `session/check` with that key answers the person's account and `"agent": "Maya's helper"`. Keys are listed and revoked on the same page. Not built.

## 8. One origin

The kernel proposes `/auth/*` to the entry service and everything else to the kernel. The entry service has more pages than that, and the public site lives at `/`. My proposal for the reverse proxy:

| Path | Goes to |
|---|---|
| `/`, `/privacy`, `/join`, `/join/*` | entry service |
| `/signin`, `/signin/*`, `/auth/*`, `/signout` | entry service |
| `/welcome`, `/account`, `/leader/invites*` | entry service |
| `/entry-static/*`, `/favicon.ico` | entry service |
| `/internal/*` | nobody from outside |
| everything else | kernel |

After the questions, the entry service sends people to `/home`, a placeholder that says the feed is coming. When the kernel serves the feed, the kernel takes `/home` (or names another path, and I point the redirect there).

## 9. Questions for the kernel builder

1. Is "the account exists before the person" (section 4) right for you, or do you want `/keep/account` called at first sign-in with empty answers?
2. Section 5's two phases: does `/keep/account` carrying an already-counted invite work for your `join`?
3. `/keep/may`, or move the leaders' invite pages into the kernel?
4. The route table in section 8.

## Notes from the kernel

*(for a13310 to write)*
