# What three interoperability trials found

> Claude, 28 Oct 2026, for Alex. He asked for trials "that actually demonstrate real life like interoperability, make them intentionally hard … what if someone redeveloped this whole thing with different words, or what if someone wants to show this thing on the map".
> - Three trial agents each worked on a copy of the live desktop log, with no source edits; their reports are `*/FINDINGS.md` in this folder.
> - Labels: **ran**, **read**, **imagined**.

## The three trials (ran)

| Trial | What it built on a copy of Alex's world | Board cards it serves |
|---|---|---|
| [Calendars and the map](map-calendars/FINDINGS.md) | 300 Seabright board events, 300 iCal-style feed items (`summary`, `dtstart`, `location`) made by a member, 100 private meetings (`when`, `where`), 50 spots. The real `board.py` and `map.py` code ran in-process. | the Seabright calendar and map |
| [Chats from anywhere](chats-from-anywhere/FINDINGS.md) | 3,000 Twitch messages in Twitch's words across 4 channels (10 hostile), 20 native windows, 310 said lines | dk1031 "Native windows get kinds", dk1140 "Twitch chat in the new world" |
| [Task board rebuilt](tasks-rebuilt/FINDINGS.md) | Alex's 58 real cards retyped as a Tracker app (`issue`: name, status, assignee…) and GitHub issues (`gh-issue`: title, state, body…), 2,174 task-like things in all | "what if someone redeveloped this with different words"; the House building a `task_thing` |

## What held (ran)
- **One `rows` across vocabularies works.**
  - `rows task` listed all 2,174 cards, issues and GitHub issues, each with its reason.
  - A `message` kind listed 3,417 said lines and Twitch messages together, and filters worked.
- **No real thing in Alex's world fitted a task shape by accident.**
- **Grants held:** `only=kind:` still blocks a module from things that merely gained a shape.
- **Members stayed fenced:** they couldn't declare kinds with needs, mark or edit others' things, or widen grants.
- **Hostile Twitch text was stored as plain data** and gained no reach.
- **Speed is fine at these sizes:**
  - `rows` 27–122 ms;
  - `actions` 9–27 ms;
  - dispatch 1–26 ms;
  - lens compile 25–610 ms (610 ms when drawing 2,174 cards).

## Fixed today (ran: 32 shape tests, full suite 194 passed)
These were mistakes inside the approved design, not new design. Each has a test in `src/agora/tests/test_shapes.py`.

1. **A member's verb could take over `done` for everyone,** and it ran with Alex's rights (`forget`). Now a member's word answers a plain word only for its maker. Words made by the kernel, a module, a steward or the group's leader answer everyone. Anyone may still say a word by its full name. A group's words answer only in that group and below.
2. **A second declaration of a kind silently replaced the first.** That's how a member hid the steward's `issue`, and how the steward dodged widen-only. Now there's one declaration per name per scope; a second is refused, pointing at `set`.
3. **The kernel's own kinds could be given shapes.** `said needs="text|message chat|channel"` put 3,004 foreign things into `rows said`, which the House reads for JEFF's context. Now refused, including `extends=said`.
4. **`acts_on=chat` refused things whose own kind is chat.** Now `acts_on` is met exactly as `rows` and lenses meet a kind: its own kind, a kind extending it, or its shape. The word's own `needs` are what its code reads besides.
5. **Opening a closed kind was refused as "narrowing"**, so the board's `event` (dk333) could never feed a calendar. Opening now counts as widening.
   - **New guard:** dropping a need is refused while a word acts on the kind without declaring that need itself. Dropping `status` from `issue` had let `issue.close` close a lane.
6. **`set`'s spelling refusal blocked real work.** It refused the House's `status=paused` hold and advised a write that would have hidden the card. Now `set` writes what it's told and adds a note naming the other spelling.
7. **Refusals named things the reader can't see.** A member's private lens was named to the steward. Now such things are counted ("1 thing you can't see"), not named.
8. **A typo in `acts_on` was accepted silently** and the word then refused everything. Now refused.
9. **A word made for a thing's own kind lost to any word with a shape.** `close <ChatGPT window>` ran `chat.close`, which left the window open. Now `window.*`-style words compete as the thing's own kind's word.
10. **Wording:** "a issue", "as what it hasn:".

## What needs your call (the deeper friction)

### 1. Reaching isn't working when code reads raw names (all three trials)
A shape tells the kernel what a word needs, but module code still reads the thing's raw facts.
- **The House:** widened to issues, `builders.py` would read no `title` on 1,058 of them. It would also treat 507 closed ones as buildable, and skip the owner check for 1,255 (they say `assignee`).
- **The map:** reads things through `look`, which never fills spellings, and `look <post>` returns a summary without title, start or place. So `map.show` refused 6 of 6 events.
- **Formats:** `board.calendar` got `start` in eight formats. One became invalid calendar text silently; one became a Python error.

**What I'd propose (imagined):** a module word is handed the thing *read as its word's shape*: names filled from spellings, and values in the type the kind declares. dk333 already carries `field_types` saying `start` is a datetime. Then a widened word works as well as it reaches.

**The cost:**
- a kernel change to how module calls carry their thing;
- an optional `start:datetime` in the needs grammar.

### 2. Values don't translate
Spellings make `lane`, `status` and `state` one name, but `Done`, `closed` and `CLOSED` stay different.
- `move <issue> to=Done` writes `status=Done`, a value the Tracker never uses.
- Status filters find 24 of 37 cancelled items, because of case.

**Options:**
- **(a)** Each app brings its own word (`issue.close`). That's what exists now, and dispatch picks it.
- **(b)** Value maps on a kind (`status: closed=Done open=Now`).
- **(c)** The trial's world-level answer: lane things carrying each vocabulary's value. It reads correctly, at 528 ms for 2,174 cards.

I lean to (a) for writing and (c) for reading. I'd want you to see it on the board first.

### 3. Rules and grants on a shared kind silently match nothing
Authority stays with a thing's own kind, as decided. But when a steward points an existing rule at the shared kind (`of_kind=task`), Alex's own Done announcements stop, and `only=kind:task` admits nothing.

**Options:**
- leave it, but refuse `of_kind=`/`only=kind:` naming a kind that nothing *is*;
- or allow an explicit `fits:task`, made only by a leader.

### 4. Containers and members
A chat is a container; its lines are things. Twitch's container is the channel. Shapes describe one thing at a time:
- `say` and `chat` check the kind exactly;
- a verb can't follow a link (`say $chat` came out empty);
- "conversations I'm in" can't be said in a lens.

This needs its own design turn.

### 5. Optional aspects can't have spellings
A kind lists only required needs, so `end|dtend` can't be said. The calendar showed 0 of 221 feed end times.

**A small grammar addition:** `reads="end|dtend"`, for optional aspects with spellings.

### 6. Structural matching over-reaches
- `meeting extends=event needs=place` made all 300 board events meetings by shape.
- A task card's `when` (a timestamp) joined the calendar.
- A window's `at=2301,582` (a screen position) was "placed" on the map.

Your rule ("has the same plus more sits inside") does this by design. The counter is markers (`happening=yes`) or typed aspects (`at` means a place vs a screen point). That's what aspect entries' `means=`/`points_at=` were kept for.

### 7. Outside text and agents (not about shapes, but found here)
- **A Twitch message reached JEFF.** A source module granted `say` turned `@JEFF …` into a line addressed to him.
  - **Proposal:** a line a module says on its own addresses no one, and source modules never get `say`.
- **`map.show` sends private titles out.** On a private meeting it sent the title to Nominatim (stubbed in the trial). That's an outside service, so it's a privacy leak in the map today.
- **Native window things have no `sees`.** JEFF and residents would see Alex's ChatGPT, Claude and Discord windows. This matters before dk1031 lands.

### 8. Volume
- **Twitch in the log:** 12.4 ms and about 970 bytes per message.
- **Hearing:** each message is heard by four modules, and the House does a `look` per message.
- **Choice:** keep chat streams as presence (outside the log) or as records.

### 9. Names among repeats
`done "Dentist"` matches 17 things. The question asks back, but doesn't list ids to pick from.

## What would change my mind
- **If importers normalize on the way in** (ISO times, `start`/`end`, `lat`/`lon`), most of 1, 2 and 5 is "write a good importer", not kernel work.
- **If apps converge on shared names when they see others' kinds** (the commons research says vocabularies converge through presets and use), spellings matter less than I think.
- **If the shape-filled thing handed to modules (1) doesn't remove most module-side failures in a rerun,** shapes are the wrong layer for interoperability, and translation belongs in adapters.

## Where each friction point stands (28 Oct, evening)
Alex asked for each point to be designed slowly, with reviewers inside and outside the world. Reviews are in `../review/`.

| # | Friction | Status | Where |
|---|---|---|---|
| 1 | Reaching isn't working | Shape-reads **draft 2.1**; its bug fixes are live. Alex answered §6 with a wider direction: the system holds the kinds, producers declare what they support, and an intelligence layer reconciles. That's **[[kinds-intelligence]] draft 1**, after two reviews and JEFF's; three questions wait on Alex. | [[shape-reads]], [[kinds-intelligence]] |
| 2 | Values don't translate | **Draft 2.** Its two source holes are fixed and live. v1 (`means=`, read-only) waits on the kinds-intelligence answers, since meanings live in producer declarations. | [[values]] |
| 3 | Rules and grants on a shared kind | **Built and live (03:31Z, 29 Oct), as Alex chose:** rules hear `by=maker` (maker, their agents, leaders) by default, `by=anyone` on purpose. Older rules hear everyone. Not built: `only=maker:` on grants. | [[authority-and-shared-kinds]] |
| 4 | Containers and members | Framing note: mostly the held graph work and Alex's producer-declaration call. "Newest N" already works (`clamp last N`, `by -made`; the trial missed it, corrected). "I'm in this list" is a lens-language change, proposed to Alex (decisions note, call 8). Container points are on the Twitch card dk1140. | [[containers-and-overmatching]] |
| 5 | Optional spellings | Folded into shape-reads (`reads=`) | [[shape-reads]] |
| 6 | Structural over-matching | **Built and live, as Alex chose:** child kinds hold only what's declared (`mark` → `is.<kind>`); parents stay structural. | [[containers-and-overmatching]] |
| 7 | Outside text and privacy | **Draft 2.1.** The closed-chat leak (dk1245) is fixed and live since 22:13Z. Fixed in source and live since the 22:47Z restart:<br>• round 1's nine leaks: House turns per chat, the refusals display, catch-up, names, replies, the map's centre and side geocoding, window titles;<br>• round 2's holes: refusal rows and reasons, module lines, `sees_line` with no door, queued lines lost on restart.<br>The map's `point_of` no longer sends found titles, ambiguous names or ids outside (live since 22:57Z). **Built and live, as Alex chose ("Public, or my own"):** modules read `outside=public|yours|no` on every row; the map honours it, including saved route and layer text. Open design: `@` in module lines, derived visibility. | [[outside-and-privacy]] |
| 8 | Volume | The clutter session's view: outside chat is presence until someone acts on it. A ring buffer and a per-source file; promoted to a record (marked outside text) on reply, quote or pin; plus a per-stream digest. **Put on the Twitch card dk1140** (`design_inputs`, with friction 7's "outside text calls no one" and friction 4's channel-isn't-a-chat). | `review/volume-clutter.md` |
| 9 | Names among repeats | **Fixed in source:** the question lists the things with the fact that tells them apart | `kernel.py` `choices` |

## Not verified
- Running modules end to end.
- Painted presses through the door.
- Kits carrying kinds between worlds.
- The live desktop runs all of this since the 03:31Z restart, 29 Oct (ran: 18 windows live, 11 modules, no errors since start). Committed as 39f996a3b on main, not pushed.
