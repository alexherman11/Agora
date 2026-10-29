# Security and privacy review of outside-and-privacy.md and authority-and-shared-kinds.md draft 1, by a review agent for Claude, 28 Oct 2026.

> **What this is.** A review of [[outside-and-privacy]] (friction 7) and [[authority-and-shared-kinds]] (friction 3), against the working tree today (the dk1245 closed-chat fix is uncommitted there). No repository file was edited, the live world was not touched, no pickle or exported log was read, and the map's network calls were stubbed.
> - **Read:** both drafts; `trials/FRICTION.md`; `SHAPE.md` §6, §7, §17; `kernel/chat.py` (all); `kernel/kernel.py` (`_sees`, `shown`, `step`, `may`, `_may_person`, `reaches`, `_commit`, `announce`, `happening_for`, `module_hears`, `run`, `_rule_matches`, `_fire_rules`), and its diff; `kernel/kinds.py` (all); `kernel/refusals.py` (all); `kernel/blobs.py` (`upload`, `attach`); `kernel/words.py` (`make`, `set_`, `role`, RESERVED); `modules/house/house.py` (Agent waking and speaking, `catch_up`, `in_chat`, `happen`) and its diff; `modules/house/builders.py` `hear`; `modules/map/map.py` (all words, `position`, `point_of`, `geocode`, `placed`, routes, layers); `modules/map/tiles.py` UA; `modules/reminders/reminders.py`; `window-lab/kernel-desktop/kd_window.py` (`window.desktop`, `_owner_only`), `native_shell.py` 108-114.
> - **Ran:** five scratch scripts on fresh temporary worlds, in `C:/Users/Alex/AppData/Local/Temp/claude/C--Projects-Agora4/e6d17725-6072-416c-9336-f572113f9a0e/scratchpad/review-security/` (`probe_chat.py`, `probe_map.py`, `probe_names.py`, `probe_rule_set.py`, `probe_rule_attach.py`); `tests/test_chat.py` (8 passed, none skipped). House probes use the same stub pattern as `tests/test_next_steps.py` (`Agent.__new__`, a door that records lines).
> - **Labels:** **read** (file:line), **ran** (as printed), **imagined**.

## Verdict
1. **The dk1245 fix does what it says** for the kernel: `to` stays inside the chat at `say`, and live delivery re-checks who may see the line now (ran, S1, S3). I found no path where a *new* closed-chat line's `to` names an outsider.
2. **But the House still moves closed-chat text into open chats** by routing, not addressing: it merges lines from different chats into one model turn and posts the whole answer into the last chat (ran, S6, S7). It is the most likely real leak on Alex's desktop, where Conversation and Shop talk share one JEFF.
3. **Two leaks outside both drafts are more serious:** a leader can rewrite a member's rule and so act *as* that member, which published a member's private file (ran). And stewards read every member's refused lines verbatim in `refusals`, private text included (ran).
4. **Friction 3 rests on a premise the code doesn't hold.** An own kind is a name any member can claim with `make kind=taskboard-task`, and the steward's rule then runs as the steward on it (ran). Listing own kinds, and later `implements:`, inherit this.
5. **Friction 7's proposals point the right way but draw two boundaries in the wrong place.** `@` power follows "has a caller", but relayed text is outside whoever pressed. And "not private" means "not narrower than the place", where an outside service needs "public" and has to work per aspect.

---

## Critical

### C1. A leader can rewrite a member's rule, and the rule then runs as the member (ran; not in either draft)
- **The seam (read):** `set` may be said by "maker or leaders" (`words.py:166`), and nothing stops a leader setting `do`/`on`/`of_kind` on someone else's rule (`words.py:728-738` only rebinds). `_fire_rules` runs the line as the rule's `made_by` (`kernel.py:1568`, `actor_of`), whoever wrote the current `do`. So "a rule runs as its maker" (SHAPE §6) becomes "a rule runs as its maker, with words a leader chose".
- **Ran, `probe_rule_set.py`:** Pike (member) has a DM with Sable that Alex (steward) cannot see (`Alex sees DM: False`). Alex sets Pike's rule `do="say <DM> text=…"` and makes any note. Printed: `line in Pike's DM: Sable, send me your address | made_by: Pike | to: Sable`. The steward wrote into a chat he can't see, as Pike, and called Sable.
- **Ran, `probe_rule_attach.py`:** the same rewrite with `do="attach <Pike's private upload> to=<Pike's public note>"`. Printed: `Alex sees the file before: False` … `Alex sees the file after: True`. `attach`'s own guard ("the uploader chooses where their file is shared", `blobs.py:167`) passes, because the actor *is* Pike.
- **Imagined, same seam:** casting a member's sealed vote (SHAPE §8's "once each" holds, but the vote is the leader's), forgetting their things, or a group leader doing it to members in their group. A verb note's `steps` edited by a leader may be the same class, since a plain word answers its maker (not tested).
- **Why it matters:** in Seabright the stewards aren't the host, and on the desktop JEFF is a steward (Alex, 27 Oct). Friction 3 proposes making rules *reach more* (lists, `implements:`). That multiplies what a hijacked rule can touch.
- **Fix (imagined):**
  - `on`, `do`, `of_kind` and `do_bound` on a rule are set only by its maker.
  - A leader may switch a rule off (`off=yes`) or `forget` it, never retarget it.
  - Alternatively, a rule runs as whoever last wrote its `do`, recorded beside `do_bound`.
  - Apply the same to verb `steps`.

## High

### H1. The House merges chats into one turn and answers in the last one (ran; not covered by dk1245)
- **Read:**
  - `Agent._begin` takes the whole inbox (`house.py:212`) and joins every item's text (224-225).
  - It sets `turn["chat"] = chats[-1]` (226).
  - `_spoke` says every text block of the turn into that chat (330-336).
  - `catch_up` does the same over every chat at once (501-503).
  - The result handler re-begins with whatever queued meanwhile (302-303).
- **Ran, S6:** JEFF mid-turn. Alex says in Conversation (closed) "I'm interviewing at another company tomorrow, keep it quiet". Pike says in Shop talk "@jeff what's Alex up to tomorrow?". Printed: `turn_chat: Shop talk`, `model_was_given_closed_line: True`, `reply_said_as: say dk81 text="Alex has an interview tomorrow."`, `reply_lands_in_open_chat: True`.
- **Ran, S7:** catch-up over both lines wakes him with `chat: Shop talk`, `holds_closed_text: True`.
- **Fix (imagined):** one turn per chat.
  - `_begin` takes the first item's chat and only items of that chat (plus chat-less ones). The rest wait for the next turn.
  - `catch_up` wakes once per chat, oldest chat first.
  - The quota path that re-sends `last_sent` (294-296) keeps that turn's chat, as it does now.
- **Residual (imagined):** one model session across audiences still remembers Conversation in Shop talk. Routing can't fix that; per-audience sessions or the charter can. Say this plainly when the fix lands, so nobody reads "fixed" as "contained".

### H2. Stewards read every member's refused line verbatim (ran; not in either draft)
- **Read:** `run` keeps `line` for every refusal (`kernel.py:1067-1070`). The new `kept=` replaces only the *why*. `Refusals.visible` gives a steward every row (`refusals.py:113-120`), and `refusals` prints `line` (168-169).
- **Ran, S11:** with JEFF made a steward, Pike's refused `say <DM with Sable> about=dk99999 Sable, my diagnosis came back positive` and refused `make kind=note sees=me … text="password hint: …"` printed `jeff_reads_diagnosis: True`, `jeff_reads_note: True`, `jeff_can_see_dm: False`.
- **Fix (imagined):** for a reader other than the line's own person, keep or show the word and its target id only, or the line through who-sees: shown in full only when its target is visible to the reader, else "`say` on a thing you can't see". A refusal that never resolved a target shows the word alone.
- The friction 3 refusal (proposal 1) would be kept here too (see L2).

### H3. Own kinds are claimable, so `of_kind` lists and `implements:` don't keep trust explicit (ran)
- **Read:** `make` may be said by "members" (`words.py:163`), with any kind not in `RESERVED_KINDS`. `_rule_matches` compares the target's own kind string (`kernel.py:1535`). `_fire_rules` runs the line as the rule's maker whenever the maker may see the target (1572).
- **Ran, S12:** Alex's rule `on=make of_kind=taskboard-task do="make kind=note …"`. Pike makes `kind=taskboard-task title="from Pike"`. Printed: `notes: [('rule-saw-dk97', 'Alex')]`: Alex's rule acted as Alex on Pike's thing. The list rule `of_kind="taskboard-task issue"` didn't fire, which confirms the draft's finding.
- **So:**
  - "Each kind is named by whoever writes the rule, so trust stays explicit" (authority draft, proposal 2) is false.
  - The refusal's advice "include those you trust" names kinds, not people.
  - `implements:` widens to "any member who makes a thing of a kind someone declared". It is a step towards `fits:`, not away from it.
  - Imagined harm: a steward rule `on=make of_kind=taskboard-task do="house.build $target"` would start a Codex builder on a stranger's card with Alex's rights.
- **Fix (imagined; a design point for Alex):** the missing condition is *whose act*. Options:
  - **(a)** `by=` on rules: whose acts fire it. The default is the maker, their agents, and the leaders of the rule's group. `by=anyone` is said on purpose.
  - **(b)** A rule fired by someone else's act runs with the maker's rights ∩ the trigger's, the way a module answers its caller.
  - (a) keeps today's automation and is cheap. (b) is safer and may break Alex's own announcement rules.

### H4. The map leaks more than §3 lists (ran with the network stubbed)
`probe_map.py`, the map centred at `36.97123,-122.01456`, Alex's things `sees=me`:

| Word | Sent to Nominatim (as printed) |
|---|---|
| `map.show Review lease with the landlord` | `('Review lease with the landlord', None)`: the private title, as the draft found |
| `map.layers` (drawing only) | `('Dr Ames psychiatry, 14 Oak St', (36.97123, -122.01456))` |
| `map.find coffee` | `('Harbor shelter intake, 5 Elm', …)` **and** `('coffee', …)` |

- **New 1, `map.find` isn't only "what a person typed".** `w_find` runs `placed()` over `rows spot/structure/event` (`map.py:395-400`), which geocodes up to three *other* things' `location` per call. The draft's outside rule treats `map.find` as the safe case.
- **New 2, every geocode carries the map's centre exactly.** `viewbox` is centre ±0.6°/0.5° (`map.py:354-355`), so its midpoint is the centre to six decimals. For a home map, that's Alex's address, sent with each query. Round `near` to 0.1° (the cache key already does, 249/345), or drop it for private-origin text.
- **New 3, tiles (imagined, read `tiles.py:37-38`, `map.py:153-167, 428, 555`).** `map.where`/`map.place` fetch tiles around a private thing's own coordinates from OpenFreeMap/Overture, and a map window turned by `map.show` does too. That's coarse (a z14 tile), cached, and has no text. An "outside services" grant should still name tile hosts, not only Nominatim.
- **Routes:** routing is local (`ground.py:237`). Their leak is inside the world, M1 below.

### H5. `map.route` publishes a private stop's exact coordinates to the place (ran; not in the draft)
- **Read:** `w_route` writes `stops`, `stop_points` and `path` (`map.py:686-697`) on a `make kind=route` that has no `sees`, so it gets the place default (`words.py:647-660`). `w_add` with free text copies `lat`/`lon` the same way (613-616).
- **Ran:** Alex's `Home` (`sees=me`, `lat=36.970123 lon=-122.012345`). `map.route name=Walk stops="Home > 36.975,-122.02"` (its answer line run as Alex). Pike printed `stop_points: '36.970123,-122.012345 36.975000,-122.020000'`, and `Pike can see Home itself: False`.
- **Fix (imagined), a general rule the draft could adopt:** facts derived from a thing carry that thing's visibility. Here, a route whose stops include a thing narrower than the place is made `within=` that thing (or `sees=me`). The same rule governs §3.4 (M2).

## Medium

### M1. Friction 7 §2's caller exemption lets outside text call people (ran; imagined consequence)
- **Ran, S9:** a relay on its own: `ok say dk92 … in Shop talk · to JEFF`, the baseline the draft fixes.
- **Ran, S10:** the same relay *answering Alex's call*: `to: ['JEFF']`. Under proposal 2.2 this stays.
- **Imagined:** relays run on calls (a lens refresh, a button, a rule run as its maker), so a Twitch user wakes JEFF whenever anyone pulls the feed. The text's origin is outside however the module was invoked.
- **Fix:** in a module's lines, `@` addresses only names that appear in the caller's own call text (`args.words`/`kv`). Everything else needs `to=`.
- **Still open (imagined):** JEFF quoting outside text with `@Pike` in his own words. The House says his text as him (`house.py:336`), so it calls Pike. Provenance (a turn woken by a `from=` line) is the only handle, and it belongs in the "own kind for relayed messages" question, not here.
- **Legitimate uses aren't broken (read):** `reminders.py` never says anything (it makes `sees=me` reminders, 47, 60), and the House never speaks as itself: agents speak through their own door sessions (`house.py:72`, 336). No module in `modules/` or `kernel-desktop` produces `say` lines today. So 2.1 costs nothing now.
- **Watch:** "only people the module acts `for`" means a module with no `for` can address no one. That's right for relays, and worth saying.

### M2. The `private` bit: what it leaks, and why it's not yet the right test (read; imagined)
- **What it leaks is small.** A reader who already sees the thing learns only "narrower than the place". `shown` strips `sees`/`sees_when` today (`kernel.py:458`), so that is new information, but never who.
  - A hidden group's existence isn't revealed. To see a `visibility_of` child, the reader must see every parent (438-448), so they are in the group already.
  - Sealed votes aren't touched, as long as the bit is computed from `sees`/`sees_when`/`visibility_of`, never from `vote:`/`like:` aspects.
  - With `sees_when`, it does say a condition exists. Acceptable.
- **But the test is wrong for outside services, in two ways:**
  1. **Place isn't public.** In Seabright a member-only event's "Jane's, 12 Oak St" is not narrower than the place, so it would go to Nominatim. The draft's §5 says "public only", but §3.2's mechanism says "not private". The outside rule should be `sees=public` along the whole `visibility_of` chain.
  2. **It has to work per aspect.** SHAPE §7 makes a home's *location* `person` while the thing is place-wide (`sees.<aspect>`, applied at `kernel.py:462-464`). A per-thing bit calls that thing "not private" and sends its hidden location. Make it `private_aspects` (names only), or have the outside check take the aspect it sends.
- **§3.4 (keeping answers as facts) has three problems.**
  - It makes drawing write into others' things as the viewer, which fires rules (H3) and needs set rights the viewer may lack.
  - New `lat`/`lon` facts would be wider than a `sees.location` they came from.
  - Keep the cache in the module's home folder, or on a map-owned `sees=public` cache thing, never on the source thing.
- **Imagined:** the bit is advisory. A module process with network access isn't contained (SHAPE §11, `map.py:26-27`), so `outside=` grants are an honour system until modules are sandboxed. Say that in the "outside services" design.

### M3. Catch-up checks `with`, not who may see the line now (ran)
- **Read:** `in_chat` returns True for any chat without `with` (`house.py:511-519`), and catch-up reads `rows said` with the House's (Alex's) sight (493).
- **Ran, S4:** a group-held chat. Pike is in the team when Alex says `@pike salary bands…`, then removed. Printed: `kernel_delivery_now: []`, `pike_can_see_line_now: False`, `catch_up_woke_pike: True`.
- **Ran, S5:** a pre-fix record naming Sable (never in the team) in that chat. Printed: `catch_up_woke_sable: True`.
- **Fix:** check each line with the agent's own door (`a.door.post("/see", "look <said>")` must answer), or have the kernel give catch-up the same `happening_for` filter. That covers groups, `sees_when`, and a `with` cleared by `set` (S3b).

### M4. A name shared by two people picks the first silently, in `with=` (ran)
- **Read:** `people_named` takes `hits[0]` (`chat.py:26-30`), and `addressed` likewise (48-51).
- **Ran, `probe_names.py`:** with two people called Chris, `make kind=chat name=DM with="Pike, Chris"` printed `second Chris sees the DM: False | first Chris: True`, with no question asked.
- **Harm:** at 200 Seabright members, a private chat goes to the wrong person.
- **Fix:** refuse with `choices()` (`kernel.py:562`) when two people share the name, as `resolve_name` now does for things.

### M5. Window titles already reach steward residents (read; input to §4 / dk1095)
- **Read:** `window.desktop` returns live native titles (`native_shell.py:108-114`, `name=title`) to the owner *and stewards* (`kd_window.py:786-800, 828-838`). JEFF is a steward.
- So §4's "a resident sees a window only when Alex shares it" has to cover this word as well as window things' `sees`. Otherwise every steward resident reads Alex's ChatGPT, Discord and mail titles live. `window.list all` already promises no titles (read, its help at `kd_window.py:712-714`); `window.desktop` could do the same for anyone but the owner.

## Low

### L1. `of_kind` lists (authority proposal 2): safe to parse, with two guards (read)
- **Kind names can't hold a space or comma.** `make` requires `^[a-z][a-z0-9_-]{0,31}$` (`words.py:592`), so splitting can't change what any valid existing rule means.
- **Guard 1:** an empty list (`of_kind=","`) must match nothing, not "no filter". Today `not r.get('of_kind')` is False for `","` (1535), so a careless split-then-`any` stays closed, but a split-then-"empty means all" would open it.
- **Guard 2:** never reuse `_matches` (glob, `kernel.py:772`). `of_kind=*` would reach `said`, `person` and `grant`. Refuse kernel kinds in the list, as `validate_decl` does (`kinds.py:409-413`).

### L2. The proposed refusal (authority proposal 1) can leak, through the refusals log and `is_open` (read; imagined)
- **List only from things the rule's maker sees.** Pass `kept=` with no kind names, since stewards read the log (H2). Otherwise a member's private-group kinds reach the steward.
- **"Nothing visible is X" must be read as the maker,** so the outcome can't become an oracle for hidden things. The draft's wording already says "visible". Keep it.
- **`is_open` reads every scope's declarations** (`kinds.py:184`). So "task is a shape" can be true at the place only because a hidden group declared `x extends=task`, and the refusal then says so. Use the scope-aware `decl`/`shape` there.
- **Related (read):** `check_acts_on` and `usage_kind` test "anything is one" over all things, unfiltered (`kinds.py:387`, `kernel.py:554`). They are small existence oracles for a word-maker. Low.

### L3. `implements:` (authority step 3), if it ever comes (imagined)
- **Who may declare it:** leaders of the *rule's* scope or above, never a sub-group leader for a place rule.
  - `decl` resolves names nearest first (`kinds.py:138-151`), so a group can declare its own `task`.
  - Resolve it from the rule's `lives`.
- **Bind at make/set time**, as `do_bound` binds words: keep the resolved own-kind list on the rule and show it. A later `implements` declaration then doesn't silently widen a rule already written.
- **Refuse `implements=` naming kernel kinds** (`said`, `person`, …).
- **It still needs H3's fix.** Otherwise it widens to every member who makes the declared kind.

### L4. Smaller chat notes (ran/read)
- **`reply_to` across chats (ran, S8):** an insider's open-chat line carries a closed line's id (`pike_sees_reply_to: dk89`). Pike's `look` is refused, so only the id shows. Requiring `reply_to` in the same chat (`chat.py:69-71`) removes the question for every lens that quotes replies.
- **The receipt "X cannot see this chat" (`chat.py:105-106`)** tells the speaker whether X passes the chat's `sees`/`sees_when`. That can mean a predicate's outcome for X. Low; "the line does not reach some people named" would do.
- **`with` is settable while `sees` isn't (ran, S3):**
  - Adding Pike to `with` didn't let him see or say (`no thing called dk80`); good.
  - Clearing `with` makes the chat read as open to `say` and to `in_chat`, while `sees` stays closed.
  - No leak today, because `to` is filtered. Either make `with` kernel-kept (RESERVED) or keep `sees` in step with it.
- **Attachments (read, `blobs.py:137-176`):** upload is `sees=person:<uploader>` until `attach`, which sets `visibility_of` its parent, so a file attached to a closed-chat line follows the chat. Sound, except through C1.

---

## What I verified, and what I didn't
- **Ran:**
  - S1/S3: closed chat `to` and delivery stay inside.
  - S4/S5: catch-up leak.
  - S6/S7: inbox merge.
  - S8: `reply_to`.
  - S9/S10/S10b: module `@`; a module installed for Alex, acting on its own, is refused in his closed chat.
  - S11: refusals.
  - S12: own-kind claim.
  - Map M1-M3 and the route.
  - Duplicate names.
  - Rule rewrite (two probes).
  - `tests/test_chat.py`: 8 passed (the group test was not skipped).
- **Not run:**
  - The door's SSE stream (`door.py:156`; read: it filters by the chat target and the new `to` filter).
  - Modules end to end as processes.
  - A real model in the House.
  - Group chats with `sees_when`.
  - Verb-step rewriting by leaders (C1's last bullet).
  - Anything on the live desktop.
  - Persons with narrowed visibility (none can be made today: `person` is a reserved kind).
- **The house probes stub the model and door;** the routing they show is the House's own code path.

## What would change my mind
- **On H1:** if the House already serialises per chat somewhere I didn't read (another inbox path, or JEFF's MCP refusing cross-chat `say`), H1 drops to the residual memory-bleed note. I read `_begin`, `wake`, `_event` and `_spoke`, and found none.
- **On C1:** if Alex wants stewards able to re-aim members' rules (moderation), C1 becomes "re-aimed rules run as the steward". The impersonation is the defect, not the moderation.
- **On H3:** if Seabright never lets members make arbitrary kinds (an allow-list of kinds per group), H3 shrinks to the desktop, where the members are Alex's residents.

---

# Round 2 (28 Oct, late): tonight's fixes rerun, holes in them, and the two drafts 2

> **Ran:** the round 1 probes rerun on the current tree. One correction to the harness: the stub agent's door now answers `/see` as its person, as the real `Door` does; round 1's stub answered every post with ok and no rows, which `sees_line` would read as "can't see". Two new scripts in the same scratch folder, `probe_round2.py`/`probe_round2b.py`, and `probe_map2.py` (the real `geocode`, with only the HTTP layer stubbed so the URLs are recorded). `tests/test_chat.py` + `tests/test_house_turns.py`: 13 passed. No repository file edited, no live world.

## R2.1 What's fixed, as printed

| Round 1 | Probe | Now (ran) | Verdict |
|---|---|---|---|
| C1 rule rewrite | `probe_rule_set.py` | `Alex sets Pike's rule: False refused: sb76 is Pike's rule and runs as them, so only they change what it does (do)` | fixed; residue in R2.2 |
| C1 publish a private file | `probe_rule_attach.py` | `Alex sees the file after: False` | fixed |
| H1 merge (S6) | `probe_chat.py` | turn 1 `Conversation`, `model_was_given_open_line: False`, reply `say dk80 …` (Conversation); turn 2 `Shop talk`, `second_turn_holds_closed_text: False` | fixed |
| H1 catch-up (S7) | `probe_chat.py` | `chat: Conversation`, `first_turn_holds_open_line: False`, `still_queued: ['Shop talk']` | fixed |
| H2 refusals (S11) | `probe_chat.py` | text: `Pike: say (a thing you can't see) … → refused`, `jeff_reads_diagnosis: False`; **but `rows_carry_diagnosis: True`, `rows_carry_note: True`** | **not fixed** (R2.3) |
| M3 catch-up sight (S4/S5) | `probe_chat.py` | `catch_up_woke_pike: False`, `catch_up_woke_sable: False` | fixed; the fallback still widens (R2.2) |
| M4 names | `probe_names.py` | `refused: 2 people are called Chris (sb73, sb74); say with= by id` | fixed for `with=`; `@Chris` still takes the first (`chat.py:46-54`), which is availability, not privacy |
| L4 `reply_to` (S8) | `probe_chat.py` | `ok: False` | fixed |
| H4 viewbox | `probe_map2.py` | `viewbox '-122.6,37.5,-121.4,36.5'` (was the centre to six places) | fixed |
| H4 `map.find` on the side | `probe_map2.py` | `map.find coffee sent: [('coffee', …)]` only | fixed |
| Still open by design | `probe_map2.py` | `map.show` sends a private title (`'Review lease with the landlord'`), an ambiguous name (`'Dentist'`) and a hidden id (`'dk9'`); `map.layers` sends `'Dr Ames psychiatry, 14 Oak St'`; `map.near` sends both private locations; the route still hands Pike `36.970123,-122.012345` | open (drafts 2, §2-3) |
| Still open by design | S9/S10, S12 | relay `@JEFF`: `to: ['JEFF']` both ways; a member's `taskboard-task` fires Alex's rule as Alex | open (drafts 2) |

## R2.2 Holes in the fixes (ranked)

### High: H2 is fixed in `text` only; `rows` still carry every line, and agents get rows (ran; read)
- **Read:** the redaction rewrites `what` and `r["why"]`, but `out.append(dict(r, …))` (`refusals.py:192`) keeps `r["line"]`. The door returns the whole answer (`door.py:266-269`), and the agents' MCP adapter hands the model `json.dumps(out)`, rows included (`mcp/agora_mcp.py:100-102`).
- **Ran:** JEFF's `refusals` rows held `say dk81 about=dk99999 Pike's lab results: positive`, `say Dentist hi`, `set Dentist lane=Done`; `rows_with_line: 7`.
- **Fix:** pop `line` (and the original `why`) from the row for someone else's entry, and put `_seen_part`'s text in a `seen` field instead.

### High: the reason is still shown whenever the line's thing is named, not an id (ran)
- `_seen_part` treats only an id as the line's thing (`refusals.py:135-147`), so `say Dentist hi` keeps its reason. JEFF read `no chat you can see is called Dentist (called that: dk90, a note, dk91, a note)`, the ids and kinds of Pike's private notes. That message comes from `named()`'s hint branch, which has no `kept=` (`kernel.py:543-545`). The ambiguous-name refusal was redacted (`2 things are called Dentist; asked which`), so someone fixed `choices` and not this one.
- **The general problem:** many refusals quote their line (`no person here is called {name}`, `nothing answers to '{word}'`, the map's `{text}: not a place this map knows`). Showing someone else's reason "unless its thing is hidden" fails open.
- **Fix:** invert it. Show someone else's reason only when the `Refused` carried an explicit `kept=` (text its author vouched for); otherwise just "refused".

### Medium: a module's own refused lines are never redacted (ran)
- `keep` sets `person=None` for a module acting on its own (`refusals.py:60-61`), and the redaction applies only to rows with a person. JEFF read `#6 relay: say dk81 about=dk99999 Pike's lab results: positive` in full.
- A module installed `for` a member carries that member's data in its lines. Redact rows whose `by` is a module whose `for` is someone other than the reader.

### Medium: C1's residue is `off` and `undo` (ran)
- **`off`:** Pike parked his rule with `off=yes`. Alex's `set <rule> off=` printed `ok set dk92 [r21] · off taken away`, and the rule ran as Pike (`rule_ran_as_pike: [('pike-rule-ran', True)]`). Switching off is moderation; switching *on* is acting as the member.
- **`undo`:** Pike fixed his rule's `do`. Alex's `undo r4` printed `undid r4: set sb74 [r5]`, and `rule do now: make kind=note text=old-do …`. A steward may undo anyone's act (SHAPE §6), so he can re-point a member's rule to the member's own older line.
- **Fix:**
  - A leader may set `off=yes` but not remove it on someone else's rule.
  - Undoing a record that changed a rule's steering fields is the maker's own; anyone else's undo of such a record leaves the rule switched off.
  - **Good (ran):** `visibility_of` can't be written by a line (`refused: visibility_of is not a fact a line may write`), so a leader can't hide a rule from its maker.
- **When `by=` lands, add it to `steering`** (`words.py:734`), or a leader widens a member's rule to `by=anyone`.
- **Usability only:** `maker not in (actor.id, actor.person)` means Alex can't steer a rule his agent or a module made for him.

### Low: `sees_line`'s fallback widens, on a narrow path (ran with a stub; read for reachability)
- With no `a.door` and no session token, `sees_line` falls back to `in_chat` (`house.py:532`), which is True for any chat without `with`. Ran: the removed member's group-chat line went to his model (`sent_to_model: True`, `pike_can_see_line: False`). My stub had a live child and no door, which the real House never has: `door` is set in `start()` (`house.py:155`).
- **The real path:** an agent with no session at catch-up queues the line, `start()` fails, and the line is said once a session appears and `load()` begins the inbox.
- **Fix:** with no door, return False. An agent with no session can't take a turn anyway.

### Low, availability: queued chats are lost on a restart (ran)
- `wake` moves the cursor when a line is *queued* (`house.py:195`), not when it's said to the model. With one turn per chat, lines wait longer.
- **Ran:** JEFF busy, a Conversation line and a Shop talk line queued, house stopped: `cursor_saved: 16`, and catch-up after the restart has `c1: False`, `c2: False`. Both are gone.
- This predates tonight, but tonight's change widens the window. Move the cursor in `_begin` after a successful `send`, for the items sent: at-least-once, never lost.
- **No starvation (ran):** the turn order was `[('a', …), ('b', …), ('a', …)]`. Each turn takes the oldest waiting chat, so a busy chat can't hold another back.

### Does the redaction hide what a steward needs? Partly (ran; read)
- **Module errors are untouched** (`modules.py:102, 132, 212`: `by=` the module, no person), so "module died" and its stderr tail stay readable. Good, though a module's stderr can hold a caller's text (the map writes `find: {exc}`).
- **A person's error on a thing the steward can't see** shows only `error`, so the exception class and code location are lost. Ran: on a visible thing the row showed `TypeError: cannot read start of None at …`. Keep `TypeError at kernel/words.py:123` (code facts, not data) and drop the message.
- **A page's `failed why=`** from another person shows `(no line) → failed`. Ran: Alex loses `dock frame stopped: TypeError at shell_parts/dock.js:88`. Same fix: keep the `at …` part.

## R2.3 authority-and-shared-kinds.md draft 2 (`by=`)
- **Right direction:** "whose act" is the honest signal. The default (maker, their agents, the rule group's leaders) is conservative, and `look` naming which it is makes it legible.
- **Sealed acts must never match `by=` except `by=anyone` (imagined).** A sealed act's happening says `by=sealed` (`kernel.py:1579`), but the kernel can recompute seals. If `by=Pike on=vote` ever matched Pike's sealed vote, the rule's effect would tell its maker when Pike voted and on what (`$target`), which breaks SHAPE §8. The draft should say "a sealed act fires only `by=anyone` rules", and test it.
- **`by` has to be maker-only** (R2.2), and `look` should show the resolved set, as `do_bound` is shown.
- **Who counts as "by"** for a module's act: a module answering a call writes `by=<module>` with `for=<caller>`; on its own, there's no person. Match on `for` when present. A module on its own (a relay) then never fires a default rule, which is right.
- **Option 2 (∩ rights) leaves three things to specify (imagined):**
  - whose `once` budget it spends;
  - whose seal a sealed word uses: it must stay the maker's;
  - whose sight the line reads with. `may` alone isn't sight.
- **Item 6, grants: `by=` means something else there.** A grant limits the *target*, so the enforceable form is the target's maker: an `only=maker:<me|leaders|anyone>` clause beside `kind:`/`thing:`/`fields:` in `reaches` (`kernel.py:943-974`), which has the target. `made_by` and `for` are kernel-kept (RESERVED), so it can't be spoofed. Filtering a module's *hearing* by actor would live in module code, where the kernel can't enforce it.
- **Leave it as it is:** the transition ("today's rules keep firing for anyone") is honest. One notice per maker listing their `by=anyone` rules would make it actionable.

## R2.4 outside-and-privacy.md draft 2
1. **`@` only from the caller's own call text.** This is enforceable: `admit` has the call text (`kernel.py:1651`). One gap (imagined): a painted press fills its line from row values (lens handles), so text "in the call" can be outside text no one typed. Count only what was typed or bound in the button's own line, not values filled from rows. Agent laundering (JEFF repeating `@Pike` from Twitch in his own words) is still uncovered. Name it.
2. **Public, per aspect.**
   - Agreed.
   - Compute `private_aspects` only over the aspects the reader can see. Aspect names carry data: `contact:<person>` and `answer:<question>` are names (`words.py:228`), so listing hidden ones would tell a reader who left a contact.
   - Draft 2 dropped draft 1 §3.3, "`point_of` stops guessing". Probe_map2 shows it's still the biggest live sender: a found thing's title, an ambiguous name and a hidden id all went out. Keep it in the open list.
3. **Derived visibility.** The kernel can find "read from" without trusting the module: it already counts the rows a module reads during a call as the caller's look (SHAPE §17). Two limits (imagined):
   - `visibility_of` takes one parent, so a result read from two unrelated narrow things can't be made "within" both. Fail closed to `sees=me`, for the caller.
   - `set` on an existing wider thing (`map.route <route>` replanning to a private stop) can't be made within anything, and `sees.<aspect>` is kernel-only. Refuse such a set, or say what it would widen.
4. **The geocode cache in the home folder.** Fine, as long as it holds only answers to texts that were allowed out (public or typed). Otherwise it's a plaintext copy of private places outside who-sees, in backups.
5. **Window titles.** Live today, not only in dk1095's future: JEFF can read them now. `window.desktop` returning names to the owner only (`kd_window.py:828-838`) is a small interim step, Alex's to choose.
6. **The House's memory.** Agreed, with one more instance: `_begin` puts JEFF's next-steps packet (his task projection) into whichever chat's turn starts, including an open chat's (`house.py:225`). It's read through his own door, so it holds only what he may see, but the audience of the turn may be wider.

## What would change my mind (round 2)
- **On "rows carry the line":** if no reader ever gets refusal rows, it drops to Low. The MCP adapter forwarding the whole JSON says they do; pages may not.
- **On the reason redaction:** if every `Refused` that quotes its line already has `kept=`, inverting the default changes little. I found one that doesn't (`named()`), and the wording of others suggests more.
