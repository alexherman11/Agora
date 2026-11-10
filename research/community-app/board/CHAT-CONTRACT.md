# Chat contract (kernel side)

*Draft by Claude (kernel builder), 5 Nov 2026, for the Seabright meeting. Kept current while the kernel work lands;
the words live in `research/kernel-lab/kernel/chat.py` and `words.py`.*

All lines go through the door as usual: acts `POST /do {line}`, readings `POST /see {line}`. Every act is an ordinary
record with a receipt and `undo`.

## Words

| line | who | what |
|---|---|---|
| `say <chat> text="<words>" [reply_to=<said>]` | anyone who may say in the chat (guests too) | a new line. `text=` is the whole of the words (send it quoted). |
| `set <said> text="<new words>"` | the line's speaker only | edits it; records `edited` (time). Others refused: "only whoever said the line edits it". |
| `forget <said>` | the speaker, or a leader of the chat's group (stewards lead the place) | removes it. Shows as a `removed` stub only while a visible reply points at it; otherwise gone from the reading. `undo` brings it back. |
| `react <said> emoji=<e>` | anyone who sees the line and is a member (guests too) | toggles the caller's reaction (once per person per emoji). Emoji: 1-16 characters, no spaces. Not sealed: names are shown. |
| `pin <said>` / `pin <said> off=yes` | leaders of the chat's group | pins / unpins a line. |
| `chat <chat> [limit=50] [since=<said>] [before=<said>] [pinned=yes]` | anyone who sees the chat | the reading below. `before=` = older page; `since=` = newer than; `pinned=yes` = only pinned lines. |
| `attach <file> to=<said>` | the line's speaker, a member (not a guest) | after `POST /upload`; the file then shows in that row's `files`. |

Refusals come back as `ok: false` with text `refused: <why>`.
A signed-out visitor's act is refused with text containing **`sign in to send`** (and `/do` answers `"visitor": true`).
A guest whose pass ran out is refused with text containing **`sign in to keep talking`**.
A guest's upload/attach is refused: **`guests can't share files`**.

## The `chat` reading

`rows`, oldest first / newest last, at most `limit` (default 20, max 200). One row per line:

```json
{
  "id": "dk812",
  "kind": "said",
  "chat": "dk40",
  "by": "Maya",                 // display name (kept for older lenses)
  "by_id": "dk77",              // person id ("" for a line imported from outside)
  "name": "Maya",               // display name (same as by)
  "guest": false,               // the speaker joined as a guest
  "badge": "leader",            // "steward" | "leader" | "" (leader of the chat's group)
  "mine": false,                // the reader said it
  "text": "See you at 7 @Sam",  // "" when removed
  "at": "2026-11-05T02:14:09Z", // ISO UTC, as the kernel stamps
  "ts": 1762308849,             // the same time, epoch SECONDS (int)
  "reply_to": "dk800",          // or null
  "reply": {"id": "dk800", "name": "Sam", "text": "first 120 chars…", "removed": false},   // or null
  "edited": 1762309000,         // epoch seconds of the last edit, or null
  "removed": false,
  "pinned": false,
  "reactions": [{"emoji": "👍", "count": 2, "mine": true, "names": ["Maya", "Sam"]}],
  "mentions": ["dk81"],         // person ids @named in the current text
  "files": [{"id": "dk901", "name": "flyer.pdf", "mime": "application/pdf", "size": 48211}],
  "to": ["Sam"], "acts": "", "about": "", "via": "", "from": "",
  "rev": 7                      // changes whenever the line changes (edit, reaction, pin)
}
```

A removed line that still has a visible reply appears as
`{"id", "chat", "removed": true, "text": "", "by": "", "by_id": "", "name": "", "reactions": [], "files": [], ...}`
(same keys, emptied).

Paging: first load `chat <c> limit=50`; scroll up `chat <c> limit=50 before=<first row id>`; catch up
`chat <c> since=<last row id>` (an edit/reaction to an older line does not show in `since=`; re-read the visible
window, or watch `rev`).

## Live

`GET /stream` (server-sent events) sends `event: world` with `{seq}` on **every** record (a say, edit, reaction,
removal, pin), to every open stream, signed in or not. Re-read `chat <c>` on it. `event: happen` carries the word
(`say`, `set`, `react`, `forget`, `pin`) and target for readers who may see that thing.

## Visitors and guests

- Signed out (no session, or an ended one): if the world has a visitor (`visitors on` by a steward), the door reads as
  that visitor. It sees only things opened with `seen-by <thing> everyone` (by a leader), or placed in a group opened
  that way. Chats stay members-only unless a leader opens them. `/see` works; `/do` refuses "sign in to send".
  Without a visitor, the door answers 401 as before. `seen-by` takes only things the whole place sees (not closed
  groups, not narrowed things); `make ... sees=everyone` is refused (make only narrows). The page's own lens,
  component, style and button things need `seen-by <id> everyone` too, or a visitor's painter cannot read them.
  `/upload` and `/api/tiling` answer 401 "sign in to send" for a visitor.
- `who`/person rows and badges: a person thing has `guest: "yes"` and `guest_until: <epoch s>` while a guest.
