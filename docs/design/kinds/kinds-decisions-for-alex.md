# What waits on Alex from the kinds work

> Claude, 28 Oct 2026, late. Each item comes from a design that other agents reviewed, in the world and outside it (`review/`). Each one is a short answer.
> - **Labels:** **ran**, **read**, **imagined**.
> - **Nothing below is built** unless it says so.

## Alex's answers (28 Oct, late, asked in the session; his words kept as written)
1. **Spellings:** "the system should hold all the kinds, things coming into the system can declare what kinds they support, and it is the job of the system to handle duplicates in the on system dictionary. That is why there has to be an intelligence layer to support multiple kinds. It is literally essential for agora to function."
   - This is a new direction, wider than the producer spellings proposed below. It's being designed slowly, with reviewers, in [[kinds-intelligence]].
2. **Child kinds:** "Children by declaration". Built and live since 03:31Z, 29 Oct.
3. **Rules hear:** "You, your agents, leaders". Built and live: new rules are `by=maker`; your existing five rules have no `by` and keep hearing everyone. Sealed acts fire only `by=anyone`.
4. **Outside services:** "Public, or my own". Built and live: the map sends a place text only when it's public or the asker's own.

## Design calls

### 1. Who reconciles vocabularies: readers, or the app that owns the words?
- **Today, every reader lists every spelling:** `start|dtstart|begins`.
- **The proposal:** the kind that owns a vocabulary says once how its words map:

  `set <ical-item kind> spells="start=dtstart:time title=summary"`

- **Three reviewers and the prior art** (Palantir interfaces, Apple App Intents) independently landed here.
- **It also gives two other designs their home:**
  - the value maps for "done": `means=`, below;
  - which things count as a "meeting": point 2.
- **Lean:** yes.
- **Why it's yours:** it moves part of today's "things fit kinds by structure" to declarations.
- **Detail:** [[shape-reads]] §6.

### 2. Child kinds by declaration
- **The problem:** `meeting extends=event needs=place` made all 300 board events meetings. A card's timestamp put it on the calendar, and a window's screen position put it on the map.
- **Lean:**
  - parents (`event`) stay structural, for lists;
  - children (`meeting`) hold only things declared or marked as such.
- **This changes your rule** "has the same plus more sits inside", for children only.
- **Detail:** [[containers-and-overmatching]].

### 3. Rules hear whose acts?
- **The problem (ran):** a rule runs as its maker. Any member can make a thing of your kind `taskboard-task`, so your rule then acted *as you* on their thing.
- **Proposal:** a rule says `by=`.
  - **The default:** you, your agents, and the group's leaders.
  - **`by=anyone`** is said on purpose and shown.
  - **Existing rules** keep hearing everyone until changed.
- **Alternative:** a rule fired by someone else runs with only the rights you both have. That's safer, but your announcement rules may break.
- **Lean:** `by=`, unless most of your rules are announcements meant to hear everyone.
- **Detail:** [[authority-and-shared-kinds]].

### 4. What "done" means across apps
- **First step only: read-only, about 300–450 lines.** Each app's kind says what its values mean:

  `means="state: open=open closed=closed"`

  The stages are not-started, active, done and dropped, under open and closed.
- **Lists and filters read the stage,** so case and spelling stop mattering: 24 of 37 cancelled items found becomes 37 of 37.
- **Words that act refuse "unknown",** so a paid worker never starts on a guess.
- **Writes use the app's own words.** Nothing invents a value.
- **Two things the review moved out of the stages:**
  - **"Held"** (paused, waiting on you, blocked, needs approval) is a second axis with many authors. It comes later, as its own things.
  - **"Verified"** is an attestation, your own act.
- **It depends on point 1.**
- **Detail:** [[values]] draft 2.

### 5. What may go to outside services
- **Today (read):** the map sends place text to Nominatim.
- **Proposal:** only text that is public, checked per aspect, or that a person typed as a search. Everything else stays home.
- **Your call:** are your own places OK to send (most apps send addresses to Google), or public only?
- **The honest limit:** a module with network access isn't contained. Until modules are sandboxed, this is an honour rule.
- **Detail:** [[outside-and-privacy]].

## Smaller calls
6. **`who=Alex` on cards stays text** for now. Making owners ids later needs a migration of your cards. OK to plan that?
7. **A `closes` written as a bare date is read as UTC,** and the receipt says so. OK?
8. **A lens can't say "chats I'm in".** A chat's `with` lists its people, but a lens compares the whole list, so `prop:with=$me` matches nothing.
   - **Lean:** treat `with` like `owner`, which already matches any of the listed people. Later, typed aspects make this general.
   - It changes the lens language, so it's yours. Detail: [[containers-and-overmatching]], "Correction and proposal".
   - "Newest N first" already works (`clamp last N`); the trial missed it.
9. **The AGENTS.md charter block** still points at the old desk's `a6529`, whose generator is gone. Agents keep trying to read it.
   - Options: retire the block, or point it at a charter in the new world.
   - It says "never hand-edit", so it's yours.

## Housekeeping
10. **Commit:** done on your yes, as 39f996a3b on main (only my files, and only my hunk of kd_window.py). Not pushed.

## Changes you'll notice
- **"Verified" is yours alone now:**
  - `task.verify` and `task.review` refuse an agent or module acting for the reviewer;
  - an agent can no longer make a card read "verified by Alex", whether through the word or a plain `set`.
- **Members' refused lines are redacted for stewards:**
  - JEFF sees the word, its thing if he can see it, a reason only when its author marked it shareable, and an error's class and code place;
  - he doesn't see the typed line;
  - your lines and your agents' stay whole for him, as dk939 asked: stewards share one readable log.
- **Your call:** should your own lines be redacted from JEFF too?

## What's live (ran)
- **Live since 22:13Z:** the closed-chat fix (dk1245) and the shapes built today.
- **Live since the 22:47Z restart (uncommitted):**
  - the security fixes from both review rounds: House turns per chat, the refusals log, catch-up, names, replies, the map, window titles, rule switch-on and undo, queued lines on restart;
  - the shape fixes;
  - closed kind declarations;
  - verification by agents;
  - a module reader crash found in the desktop log.
- **Live since the 22:57Z restart:**
  - the map no longer sends a found thing's title, an ambiguous name or an id to Nominatim;
  - `status` alone says to name a module;
  - kdesk.log stamps each start with its time.

## Where each friction point stands
- **Waiting on you:** 1, 2, 3, 6, the rest of 7 (points 1–5 above).
- **Done:** 5 (folded into 1) and 9.
- **Handed on:** 8, to the Twitch card dk1140, with the "outside text calls no one" point.
- **4:** "newest N" already works (`clamp last N`; the trial missed it). "Chats I'm in" is a lens-language change, call 8.
