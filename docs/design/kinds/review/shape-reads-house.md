# Review: shape-reads, from the House and JEFF

> By Claude (the desktop/refusals session), 28 Oct 2026, of [[shape-reads]] draft 1. Read only: nothing ran.
> Labels: **read** (code, with file:line as of today's working copy), **imagined** (design).

## Short answer
**Yes, it fits the builder,** and it's the right layer for the title/text gaps. Five changes would make it safe for a reader that holds a claim for hours. JEFF's context is unaffected, so long as plain `look` and `rows` keep raw values.

## What the builder does today (read)
`modules/house/builders.py`:
- **Re-reads the card every time.** `Door.look` (:61) runs on claim (:247), each update with up to 4 stale retries (:161), tell (:382), the launch retry (:370), `assert_owned` before irreversible steps (:449), and House start (:102).
- **Compares exactly what it saved.** It saves `basis = {title, text, acceptance, who}` and `task_owner = who` (:214, :394). Then `assert_owned` stops the run if any of them reads differently later (:451-453).
- **Treats `who` as a name.** It checks `who` against `caller['name']` and `'JEFF'` (:200, :202, :249, :383). `manager.py:64,99` does the same, and so does `house.py:592` (casefold against the agent's name).
- **Holds on values.** `held()` (:40) reads `lane`, `paused`, `cancelled`, `permission_required`, `approval_required` and `status` against `HELD`.
- **Writes its own bookkeeping.** It writes `builder build build_run build_phase build_detail` with `saw={task: rev}` (:167, :254). The manager path writes with `WRITE_FIELDS`/`NOTE_FIELDS`, and `NOTE_FIELDS` includes `status` (`manager.py:11-12, 95`).
- **Hard-codes kind lists in two more places.** Besides the shape: `manager.py:55` refuses anything not `task`/`taskboard-task`, and `house.py:58` `TASK_KINDS` gates the "gave you a task" wake. **So widening `house.build` in the world still wouldn't reach through `house.manage`, and wouldn't wake anyone.** That's worth adding to the trial table. The fix is the House's own (read the word's shape, or `thing`), but the draft should say the call's `thing` is how those checks retire.

## Where it fits (imagined)
- **`through=house.build` on each door re-read is the right surface.** It's one string change at `Door.look`, and every comparison then runs on House names. `thing` in the call replaces only the first read (:188); the hours-long reads still need `through=`. The draft already says so (3.5).
- **`unread` is the most useful part for the House.** It lets the builder *fail closed*. The rule would be: if any need, or any aspect `held()` consults, is in `unread`, refuse or stop. Today a missing `who` silently skips the owner check (trial finding 4: 1,255). With this, it becomes a refusal with a reason.
- **Real facts in the record** (3.4) is right for the House. The receipts, `claim_records` and undo all keep meaning the actual write.

## What I'd need that it doesn't give

### 1. The reading cache must key on the reader, and on more than `rev`
§5 says a per-(thing, rev, shape) cache. But `person`, `thing` and `point` read "only what the caller sees", and `person` also depends on *other* things: whether a second visible "Alex" exists.
- **Cross-reader leak:** the builder reads as the House narrowed by the caller (:188), then as the requester's door session (:161). If the cache serves one reader's reading to another, that's a visibility leak. Key it on reader too.
- **Stale reading:** someone renames a person, and the thing's `rev` doesn't move, but its reading should. The cache would hand back the old `who`. Either drop the cache for readings with a hop, or key it on what was read.

### 2. `person` by unique name shouldn't gate authority (your Q4: yes, too clever for this)
The owner check is an authority check. If it hangs on a name lookup, other people's actions can flip it:
- A second "Alex" appears, so `who` goes from read to unread, so `assert_owned` stops a healthy run. That's safe, but spurious, and it's hours into a build.
- Worse, the reverse: a name that was ambiguous becomes unique when someone leaves, so a card suddenly reads as owned by someone.

**Suggestion:** when a need gates reach, a `person` value reads only from ids. A name is `unread`, and the builder refuses with "assignee 'Alex' isn't a person id". Names can read leniently in lists and lenses, matching your "membership is has". Mapping Tracker/GitHub names to people is then the adapter's job, done once and visibly. That's your "what would change my mind" #2, applied to this one type.

### 3. Canonical `who` changes the value the builder has saved
- Today `who` is a name, and every check compares names (above). `person` canonicalises to an id (`who: "dk2"`).
- If the House adopts `through=` and nothing else changes, every saved `state.json` holds `task_owner: "Alex"`. The next re-read gives `dk2`, so **every in-flight run blocks on restart** ("task changed before claim", "owner changed").
- **Ask:** make `read` structured, not prose: `read: {who: {from: "assignee", raw: "Alex"}}`. Then a reader can compare raw values across a migration, or pin on raw. The House also needs a one-time translation of saved bases. That's the House's job, but the draft's cost table should list it under `builders.py`.

### 4. Writes `through=` on value-bearing aspects need a guard before friction 2
`set dk94 status=paused through=house.build` on a gh-issue goes to `state=paused`, by 3.4's spelling rule. But `paused` isn't a GitHub state, and an adapter would try to push it back out.
- Name translation is safe only where the values are the same vocabulary. `status|state|lane` aren't (trial finding 5).
- **Ask:** until value maps exist, `set … through=` refuses to rewrite a key whose spellings are value-bearing: any untyped spelling whose two names don't share values. The refusal should say "status is spelled state here, and their values differ; set state yourself". Alternatively, mark these spellings in the shape (`status|state!`), meaning names only, no write-through.
- **For the House,** this matters through `NOTE_FIELDS ∋ status` (Rowan's notes), and through anyone holding a card.

### 5. Outside text reaching a worker prompt (worth one line in the draft)
`reads="text|body|description"` is honest. But for gh-issues, the `body` was written outside Agora, and the builder pastes `text` straight into a Codex worker's instructions (`builders.py:422`). Widening reach widens who can write instructions to a worker. The reading already says `read: {text: "body"}`; the builder needs that, plus the thing's maker, to label the text in the prompt as outside-authored. That's the House's change, not the kernel's. Name it in §4's table, so a rerun of the House trial checks it.

## JEFF (read)
JEFF's wake and context read only said lines and chats:
- `rows said` for catch-up and the chat feed (`house.py:493, 667`);
- `look <said>` for the line (:556);
- `look <chat>` for its name (:507).

They're kernel-made, in one vocabulary, so `through=` neither helps nor hurts. `context()` (:511) is held and not called.

**One ask:** plain `rows <kind>` and `look` keep raw values. Only `through=` may canonicalise. `local()` (:661) parses `made` with `%Y-%m-%dT%H:%M:%SZ`, and on any other form it silently falls back to the raw string. If `rows said` started returning `made` with an offset or milliseconds, the feed's times would quietly change format. §3.3 says `rows event` sorts typed values; please say that it sorts by them and shows raw.

**Where JEFF would want it later:** JEFF writes cards as lines it types. It won't remember `through=`. So on your Q2, I agree that module answer lines stay explicit. But `set`'s existing spelling note (`words.py:700-715`) could end with "or say `through=<word>`". Then an agent learns it from the refusal, as the Lines help work found agents do best.

## On the other open questions, briefly
- **Q1 (has vs reads):** right. The House is a reach reader, so it gets the strict side.
- **Q5 (form-preserving writes):** for the House's own bookkeeping facts, there's nothing to preserve. They aren't shape names, so they go as told. That's fine.
- **Q7 (`through=`):** it reads well in House lines: `look dk94 through=house.build`. Keep it.

## What would change my mind
- **If the House rerun shows the builder still needs raw reads for most checks,** because the bookkeeping facts and the hold values dominate, then `through=` buys the House little. The cheaper fix would be the House reading the word's shape itself.
