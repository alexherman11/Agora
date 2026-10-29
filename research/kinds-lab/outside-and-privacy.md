# Outside text, outside services, and who a thing is for

> **Draft 2 (28 Oct, after the security review `review/privacy-authority-review.md`).** Draft 1 is kept below.

## Draft 2: fixed tonight, and the design that's left
**Fixed in source tonight, each with a test (ran; uncommitted; live after the next kdesk restart, except the first group, which went live at 22:13Z):**

| Leak | Fix | Where |
|---|---|---|
| A closed-chat line woke people outside the chat (dk1245) | `to` stays inside the chat; delivery re-checks sight | live since 22:13Z |
| A leader could rewrite a member's rule, which ran as the member (C1, critical) | Only a rule's maker changes `on`/`do`/`of_kind`; leaders switch it off or forget it | `words.py` set_ |
| The House merged chats into one turn and said the reply into the last chat, so a Conversation secret was answered in Shop talk (H1) | One turn answers one chat; catch-up wakes once per chat | `house.py` `_begin`, `catch_up` |
| Steward residents (JEFF) read members' refused lines verbatim (H2) | Someone else's row shows the word and its thing only if visible; the reason only when the thing is visible | `refusals.py` (told its owner session) |
| Catch-up checked a chat's `with`, not sight, so group-held chats leaked (M3) | Checks each line through the agent's own door | `house.py` `sees_line` |
| `with="Chris"` silently picked one of two Chrises (M4) | Refused, asking for an id | `chat.py` |
| A reply carried a closed line's id into an open chat (L4) | A reply goes in the chat of the line it answers | `chat.py` |
| Every geocode sent the map's exact centre (for a home map, Alex's address) (H4) | Rounded to 0.1°, which the cache already used | `map.py` `geocode` |
| `map.find` geocoded up to 3 *other* things' private locations on the side (H4) | Searching what the world places sends nothing out; only the typed words may be searched outside | `map.py` `w_find` |

**Design still open (imagined):**
1. **Outside text calling people (M1):**
   - in a module's lines, `@` addresses only names that appear in the caller's own call text;
   - everything else needs `to=`, limited to people the module acts `for`.

   Draft 1's caller exemption let a relay wake JEFF whenever anyone pulled the feed. Today no module says lines (read), so this costs nothing now.
2. **The outside-service test (M2):** not "narrower than the place", but **public**, along the whole `visibility_of` chain, and **per aspect**. A home's `location` can be `sees.location=person` while the home is place-wide.
   - So the kernel's hint is `private_aspects` (names only), and anything going outside checks the aspect it sends.
   - It's advisory: a module process with network access isn't contained (SHAPE §11), so `outside=` grants are an honour system until modules are sandboxed.
3. **Facts derived from a thing carry that thing's visibility (H5).** `map.route` with a private stop made a place-visible route holding the stop's exact coordinates (ran). A general kernel rule would close a class of these:
   - a made thing whose facts were read from a narrower thing is made within it;
   - or the module says `within=`.
4. **Geocode answers are kept in the map's home folder** or on a map-owned public cache thing, never written onto the source thing (M2: writing on draw fires rules and widens a `sees.location`).
5. **Window titles (M5):** `window.desktop` gave every steward, JEFF included, Alex's live native window titles (read, `kd_window.py`).
   - **Interim fix in source tonight:** a steward who isn't the owner gets the program, never the title.
   - The full rule is in JEFF's dk1095 ("only Alex sees a native window unless he shares it"). He folded this in (dk1308).
6. **The House remembers across chats.** Routing can't fix that one model session carries Conversation into Shop talk. Per-audience sessions or the charter can. It's said plainly here, so that "fixed" isn't read as "contained" (review, H1 residual).
   - **One more instance (round 2):** `_begin` puts JEFF's next-steps packet into whichever chat's turn starts, an open chat's included. It's read through his own door, so it holds only what he may see. But the turn's audience may be wider.

## Built, 28 Oct, late (Alex: "Public, or my own")
- **Every row a module reads carries `outside=public|yours|no`.**
  - **public:** everyone in the place sees it, and everything its visibility follows.
  - **yours:** the reader made it, their agent did, or a module made it for them.
  - **`outside_not`** lists the narrower aspects the reader can see.
- **The map** geocodes a row's `location` only when it's allowed, and treats a row without the answer as private.
- **Typed searches** may still go out. Found things never do (`point_of`).
- Code: `kernel.py` `place_sees`, `own`, `outside_marks`; `map.py` `position`. Tests: `tests/test_map_outside.py`.
- **It's an honest-module rule, not a wall:** a module with network access isn't contained (SHAPE §11).

## Draft 2.1: the security review's round 2
**Holes in tonight's fixes, now fixed in source (ran, with tests; live since the 22:47Z restart, 28 Oct):**

| Hole | Fix |
|---|---|
| H2 was fixed in the text only. The `refusals` rows still carried each line, and agents get rows (the MCP adapter hands the model the whole answer) | A member's row, read by a steward, loses `line` and its reason; a `seen` field says the word, and its thing if visible. Stewards' own rows stay whole among stewards, as dk939 asked. Whether Alex's own lines should be redacted from JEFF is his call. |
| A reason was shown whenever the line *named* a thing instead of giving its id. JEFF read the ids and kinds of Pike's private notes | Inverted: someone else's reason shows only if its author vouched for it (`Refused(kept=)`); otherwise just "refused". Errors show their class and code place, never the message |
| A module acting for a member had its refused lines shown in full | Redacted the same way; its faults (died, failed in the kernel) stay readable |
| The "which one?" vouched text repeated the typed name, which can be a title | It says "N things share the name said" |
| `sees_line` fell back to the house's own sight when an agent had no door | It hands nothing on |
| Lines queued behind a busy turn were lost on a restart: the cursor moved at queue time | The cursor moves when a line is said, and never past one still waiting in another chat |

**Design points the round added (imagined):**
1. **`@` only from the caller's own call text.**
   - A painted press fills its line from row values, so "the call text" must count only what was typed, or bound in the button's own line, never values filled from rows.
   - **Not covered:** an agent repeating `@Pike` from a Twitch line in its own words. That's named here, not solved.
2. **`private_aspects` lists only aspects the reader can see.** Aspect names carry data (`contact:<person>`, `answer:<question>`).
3. **Draft 1 §3.3, "`point_of` stops guessing": fixed, live since the 22:57Z restart** (`tests/test_map_outside.py`). It was the biggest live sender (ran with the network stubbed): a found thing's title, an ambiguous name and a hidden id all went out. Now only typed text that names nothing goes out.
   - **Still open:** drawing (`map.layers`, `map.near`) geocodes a row's `location` text whoever it's for. Rows don't carry the thing's audience, so the map can't tell, and the rule is Alex's call (public only, or his own places too).
4. **Derived visibility:**
   - `visibility_of` takes one parent, so a result read from two narrow things fails closed to `sees=me`, for the caller.
   - A `set` that would widen an existing thing (a replanned route through a private stop) is refused, or says what it would widen.
5. **A geocode cache** holds only answers to texts that were allowed out (public, or typed as a search). Otherwise it's a plaintext copy of private places, in backups.

---
# Draft 1 (superseded)

> **Draft 1, by Claude, 28 Oct 2026.** Friction 7 in `trials/FRICTION.md`. Part of it is already fixed (§1). The rest is design, in review, not built.
> - **Labels:** **read** (code, with file:line), **ran** (a number as printed), **imagined** (design).

## 0. The one property this protects
**Words and text reach only the people and places their owner meant.** Three trials and one card found four ways that leaks:

| # | Leak | Status |
|---|---|---|
| 1 | A line in a closed chat naming someone outside it woke them with its text | **fixed in source**, §1 |
| 2 | Outside text (Twitch) relayed by a module wakes JEFF through `@JEFF` | design, §2 |
| 3 | The map sends a thing's text and ids to an outside service | design, §3 |
| 4 | Native window things have no `sees`, so every resident sees Alex's ChatGPT and Discord windows | input to JEFF's dk1095, §4 |

## 1. Closed-chat `to` (fixed today, uncommitted; card dk1245)
**The seam (read):**
- `say` computed who couldn't see a closed chat and told the speaker "the line does not reach them".
- But it stored them in `to` anyway (`kernel/chat.py:74-81`, before the fix).
- The House wakes everyone in `to`, reading the line with its own wide sight (`modules/house/house.py:553-561`, and `catch_up` at 489-503).

**Live (ran, read through the door):** 0 of 171 said lines named anyone outside a closed chat. Nothing had leaked.

**Fix:**
- **`chat.py`:** `to` keeps only people who can see the chat (`k.shown(p, chat)`). A line that names only outsiders still speaks to the chat's own people.
- **`kernel.happening_for`:** delivery keeps only people who may see the line now. That covers older records, and chats whose people changed.
- **`house.py catch_up`:** checks a closed chat's `with` before handing a line on.

**Tests:** 3 new in `tests/test_chat.py`. Kernel suite 202 passed; house tests 58 passed.

**Not done:** a runtime test with a scratch closed chat and a live resident. That waits on Alex approving scratch folders, per the card.

## 2. Outside text must not call people (imagined)
**Found (ran, chats trial §2):**
- A source module granted `say` relayed a Twitch message reading `@JEFF …`.
- `addressed()` (`chat.py:43-56`) took the `@JEFF` as a call, and the House would have woken him.
- Separately, `say` drops the speaker's own name, so every Twitch line reads as "twitch".

**Why `@` parsing is the wrong boundary:** `@name` is how a *person* calls someone. Text a module relays from outside isn't anyone in the world speaking, so nothing in it should call anyone.

**Proposal:**
1. **A line a module says on its own** (`actor.kind == "module"` with no caller) **addresses no one by `@`.**
   - It may name recipients only with an explicit `to=<person>`, and only people the module acts `for`.
   - So a reminders module can still say "your meeting is in 10 min" to Alex, but a relay can't wake JEFF.
2. **A module answering a call** (`actor.caller` set) speaks for its caller, so `@` keeps working as the caller's own words. Its answer lines are the caller's act, narrowed.
3. **Relayed speech carries its speaker:**
   - `say <chat> text=… speaker="xQc" from=twitch` stores `speaker` and `from` as plain facts;
   - lenses show "xQc (Twitch)";
   - `speaker` never resolves to a person, so a Twitch user named "Alex" isn't Alex.

**Open:** should source modules get `say` at all, or their own kind (`twitch-message`), with the chat lens showing both? FRICTION §4 (containers) and §8 (volume) lean to their own kind, kept out of `said`, which the House reads for JEFF's context.

## 3. The map and outside services (imagined, from a read of the code)
**What leaves the machine today (read, `modules/map/map.py`):**
1. **`position` (241-255):** a thing's `location` text, when the local ground has no match, goes to Nominatim, at most 3 new names per call.
   - It runs for **every row** a layer or `map.near` draws, and `map.near` reads `rows any` (439). So drawing is enough to send text out; nobody asks.
2. **`point_of` (279-286):** when `look <text>` finds nothing, the typed text goes to Nominatim.
   - `call.look` swallows refusals (106-120), so an *ambiguous* name ("which Dentist?") and a name the caller can't see both fall through to the outside service.
   - A bare id (`dk901`) does too.
   - So does a thing found by name that has no readable place: its **title** goes out. That was the trial's "Review lease with the landlord".

**Live exposure today (ran):**
- Of 916 things, 2 have `location` text, both `ask-request` UI paths ("shell-dock · root/launcher").
- No private place is in Alex's world yet. The personal calendar (planned) changes that.

**Proposal:**
1. **The kernel tells a reader, in one bit, that a thing is narrower than its place.**
   - Every row `shown()` returns carries `private: yes` when the thing, or anything its visibility follows (`visibility_of`), has a `sees` narrower than the place.
   - A reader who can see the thing learns only that it isn't for everyone, never who it's for.
   - Lenses can show a lock. Any module that talks outside can check before it does.
2. **The map's outside rule:**
   - text goes to an outside service only when a **person typed it as a search** (`map.find`, or a `map.show`/`map.near` argument that names no thing in the world, isn't id-shaped, and isn't ambiguous);
   - or when it's the `location` of a thing that is **not private**.
   - It never sends ids or a found thing's title. Drawing a layer never geocodes a private thing; it shows it as "has a place the map won't look up outside" instead.
3. **`point_of` stops guessing:**
   - it distinguishes "no such thing" from "which one?" from "can't see it" by reading the refusal kind, not swallowing it;
   - only "no such thing" may become a search.
4. **Answers are kept** (today's cache is memory only, map.py:52). A geocode result for a public text can become a fact on the thing (`lat`/`lon` with `placed_by=nominatim`), set by the map for the person who asked. Then it's asked once, not on every draw.

**Bigger question for Alex:** which modules may talk to which outside services, with what? A grant could say it (`outside=nominatim:public-text`), and the kernel would record each outside read the way it records external acts. That's a general "outside services" design; the map is its first case.

## 4. Native window things (input to JEFF's design dk1095)
**Read:** the trial noted that window things, if made today, have no `sees` (`kd_window.py:698,714`). JEFF's dk1095, "Native windows get kinds", is the design, and it waits on Alex.

**What to add there:**
- a window thing is `sees=person:<the desktop's person>` by default, since windows are Alex's screen;
- a resident sees a window only when Alex shares it;
- a by-app kind (`exe=ChatGPT.exe`) is matched case-insensitively and set by the window module, never by a person's note, so writing `exe=ChatGPT.exe` on a note doesn't make it a chat window.

I'll put this to JEFF on dk1095, not design it here.

## 5. What would change my mind
- **If relayed chat stays out of the log** (presence-like, FRICTION §8), §2 shrinks to a rule for reminders.
- **If Alex is fine with his own places going to Nominatim** (many apps send addresses to Google), §3.2 becomes "public or the owner's own" instead of "public only". The `private` bit is still worth having.
