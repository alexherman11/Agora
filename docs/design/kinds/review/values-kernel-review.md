# Adversarial kernel review of values.md draft 1 (with §7b), by a review agent for Claude, 28 Oct 2026.

> **What this is.** A review of `docs/design/kinds/values.md` draft 1, including §7b (JEFF's answers, dk1307), grounded in the working tree as it is tonight, with the round 2 shape fixes in. No source file was edited and the live world was not touched.
> - **Read:** `values.md`; `review/values-prior-art.md` (GitHub section); `kernel/kinds.py` (`validate_decl`, `decl`); `kernel/kernel.py` (`plain_verb`, `fence`, `actor_for`, `_commit_use_record`, `bind_policy`); `kernel/words.py` (RESERVED, `_writable`, `_conditions`, `set_`, `vote`); `kernel/next_steps.py` (HELD, `person`, `attested`, `change`); `modules/house/builders.py` (`HELD`, `held`), `manager.py`, `house.py`; `community/board/board.py` (`post`); the trial's Tracker and GitHub verbs (`trials/tasks-rebuilt/build.py`); `shape-reads.md` draft 2.1 §4.
> - **Ran:** `probe6.py` and `probe7.py` in `scratchpad/review-kernel/`, on fresh temporary worlds. Numbers and text are quoted as printed.
> - **Labels:** **read** (file:line), **ran** (as printed), **imagined**.

## Verdict in six lines
1. The core is right: the owner declares meanings, readers ask a small fixed set, and writes never invent values. The prior art supports it.
2. **"Held" is in the wrong place.** It's a sibling stage in the hierarchy and also an overlay, and the code already has seven-plus independent hold sources. The House migration as drawn would **drop safety holds** (`approval_required`, unknown effect) from the paid-worker gate.
3. **"Leaders only" isn't what the code would do.** A member's later closed declaration of a kind already wins `decl()` (ran), so `means=` written on it would be a member's.
4. **`verified?` is forgeable today by Alex's own agents** (ran): JEFF can produce "verified by Alex" through `task-verify` or a plain `set`. Mapping it from values would make it worse.
5. **`writes=` and the overlay are confused-deputy and leak paths.** A declared write runs as the caller and may write visibility conditions. The overlay is a plain fact anyone who can set the thing can forge, and everyone who sees the thing reads it.
6. A smaller read-only first step fixes most of the trial failures (section "Simplest version").

---

## Critical

### V1. A member can already re-point a kind's meanings (ran)
- **Ran (`probe6.py`):**

  ```
  V1 steward: ok make sh78 [r3] · a kind
  V1 member : ok make sh79 [r4] · a kind
  V1 decl('issue') now: sh79 made_by Bea means status: closed=active
  ```

- **Why (read):**
  - `validate_decl` counts only `needs`/`extends` as a shape (`kinds.py:411`), and returns before the leader check when neither is present (`kinds.py:423`).
  - The one-declaration-per-scope rule fires only when a shape is involved (`kinds.py:418-422`).
  - `decl()` takes the **later** declaration at a level (`kinds.py:146-148`).

  So a member's closed `kind=kind name=issue` with any extra facts replaces the steward's, for every reader. That's the trials' finding 2, alive for every field that isn't `needs`/`extends`.
- **The draft's "governance: leaders only, the same as shapes"** needs these source changes, not just a sentence:
  - `means=` and `writes=` count as a shape in `validate_decl`;
  - one declaration per name per scope applies to **closed** declarations too;
  - kits carry and validate the new fields (`kits.py:17` lists `name title help fields needs extends`, so a kit with `means=` is refused today: safe, but not portable).

### V2. Held isn't a stage; it's a second axis with many authors (read; imagined consequence)
- **Today there are at least seven hold sources, and two code paths read different subsets:**
  - `builders.held`: `lane=done`, and `paused`, `cancelled`, `permission_required`, `approval_required`, `status` against `HELD` (`builders.py:25, 40-43`);
  - `next_steps`: `lane`/`status` against its own `HELD`, plus `commission`, `authority ∈ {held, permission}`, `effect_state=unknown`, `paused`, `approval_required`, and `blocked_on` (`next_steps.py:15, 116-128`).
  
  Several are **safety holds**: approval required, permission, an external effect whose outcome is unknown.
- **The draft's `held?` = "the owner's value is held, or a `held_by` overlay is present"** (§3.5). Migrating the House to `open?=yes held?=no` (§3.3) then admits a card with `approval_required=yes` or `effect_state=unknown`, unless every one of those aspects is declared. And "the most specific aspect wins" (§3.2) is a **refinement** rule; holds need **any-of**.
- **The hierarchy contradicts itself once overlays exist:**
  - "no: it's disjoint" makes `held?` *no* for an `active` value;
  - an overlay makes it *yes*;
  - so a `Now` card with `paused=yes` is both active and held;
  - a paused Backlog card is both not-started and held.
- **"Broader → unknown" makes coarse vocabularies unusable for any acting word.** GitHub can't say held, so every open GitHub issue answers `held?` **unknown** under the SKOS rule, and `house.build` refuses all of them forever. Same for iCal `CONFIRMED=open`.
- **Change: two axes.**
  - **Lifecycle** is the owner's value through `means=`: not-started, active, done, dropped, with broad open and closed.
  - **Holds** are a set of sources, any-of, each with an author: owner values that mean held, existing hold facts declared per kind, and hold things (V6).
  - `held?` asks the hold axis only. A vocabulary that can't express a hold contributes "no" to it, never "unknown". "Unknown" stays for lifecycle refinements the vocabulary *can* express (GitHub `closed` with no reason, asked `done?`).
  - §7b's `waiting-on-person` and `blocked` then become hold **reasons**. That's what they are in the code: `waiting_on` and `blocked_on` relations, `next_steps.py:128-131`.

### V3. `verified?` can be forged today by the person's own agents (ran)
- **Ran (`probe7.py`):** an agent for Alex (labelled JEFF) attests Alex's verification two ways:

  ```
  jeff actor: sh77 agent person sh2
  JEFF task-verify: ok task.verify [r5]
  record by sh77 via agent
  attested as Alex's verification: True
  JEFF plain set: ok set sh80 [r7] · verified_basis=9d0691670a4b18ae, verified_evidence=sh79
  attested: True
  ```

- **Why (read):**
  - `task-verify` allows `reviewer(k, p) == actor.person`, and an agent's `person` is its human (`next_steps.py:186`, `kernel.py:1912-1927`);
  - `attested()` maps the record's `by` through `person()`, which turns an agent into its human (`next_steps.py:28-31, 80`), and ignores the record's `via: agent` (`kernel.py:1261`);
  - `verified_basis`/`reviewed_basis` aren't reserved, so a plain `set` writes them (`words.py:222-228`).
- **This is the failure JEFF describes in §7b** ("told Alex things were live"), and the House's builder works through an **agent** session for the requester (`builders.py:123-132`). An agent's say-so is exactly what verification must exclude.
- **Change, before any `verified?` question:**
  - attestation facts are reserved, written only by `task-verify`/`task-review`;
  - those words require a direct person session (`actor.kind == "person"`, no module or agent between);
  - `attested()` refuses records whose `via` is set.
  - `verified?` is then answered **only** from that attestation, never from `means=` on any vocabulary: a GitHub label "verified" imported by an adapter must not answer it.

---

## High

### V4. `writes=` runs as the caller and may write anything a caller may (read; imagined)
- A declared write is applied as the caller's `set`. `set` may write any aspect that isn't reserved (`words.py:222-228, 561-564`), including:
  - `sees_when` (it hides the thing);
  - `allows.<word>` (it gates later acts; `_conditions` binds both, `words.py:567-570`, `kernel.py:363-370`).
- **The trap:** a group's leader declaring `writes="done: state=closed sees_when=word:…"` turns every member's `done` in that group into a visibility change the member never chose.
- **A declared write also overwrites what the caller can't see:** gh `state_reason` hidden by `sees.state_reason=leaders` reads as broad `closed`. So `done?` is unknown, the declared write runs, and it replaces the hidden `not_planned` with `completed`.
- **Change:**
  - `writes=` may name only aspects the same `means=` maps, with values from that map;
  - a write refuses if any aspect it writes is hidden from the caller;
  - the record says the value was asserted by the caller.

### V5. "Most specific aspect wins" misreads GitHub, by the draft's own prior art (read)
- `values-prior-art.md:118-127`: `state_reason` "records the last transition, not the current state", and includes `reopened` on an open issue.
- **Two misreads:**
  - A stale or adapter-kept `state_reason=completed` beside `state=open` reads as **done**, so the House refuses an open issue and due-soon hides it.
  - An unmapped `reopened` beside `state=open` beats the known `open` and makes it unknown. §7b agrees reopened isn't a stage.
- **Change:** a refinement counts only when its stage is under the base value's stage (done ⊂ closed); otherwise it's ignored (`reopened`), or the answer is a conflict (open with `completed`).

### V6. The hold overlay as facts on the owner's thing (ran; read; imagined)
- **Forgeable attribution (ran, `probe6.py`):** any maker writes the House's overlay on their own thing:

  ```
  V2 member writes the House's overlay on her own thing: ok set sh80 [r6] · held_by=house, held_why=worker quota
  V2 on Alex's: refused: set is for whoever made it or leaders of Shapes; …
  ```

  `held_by=house` is a claim in a value, not an author. The maker can also remove the House's hold from their thing.
- **Leaks to every reader of the thing (ran):** `V3 alex sees her overlay text: worker quota`. `shown()` returns every fact without a `sees.<aspect>` rule (`kernel.py:451-465`). A House reason (quota, error text, "waiting for Alex's approval on …") becomes visible to every member who can see the card.
- **Hiding it per field makes `held?` differ by reader:** a member, who can't see the hold, passes `held?=no` for a hold a leader can see. A safety hold must bind whoever calls.
- **It perturbs the owner app's fences:** writing the overlay bumps the thing's rev. Every module that fences with a bare rev (the int form) is then refused as stale (`kernel.py:863`), so the GitHub adapter's sync writes fail because the House held the card.
- **A sync adapter that exports facts carries it out,** which is JEFF's dk1290 concern again.
- **Change: holds are things.**
  - `kind=hold about=<thing> reason=…`, written by a `hold` word (and `release`), with the holder as the authenticated author and its own `sees`.
  - The owner's thing is never touched.
  - `held?` is evaluated over **all** holds about the thing, whoever reads. A hold the reader can't see shows as "held (by someone you can't see)", the way refusals count hidden things.
  - The board already models per-person state this way (`board-rsvp about=`, `board-mark about=`, `board.py:186-209`).

### V7. Write routing is a new dispatch layer, and `to=` isn't a stage slot (read)
- Plain `done` finds family words by **suffix** (`kernel.py` `plain_verb`); `issue.close` isn't a `done` word, and the trials found aliasing doesn't help (tasks-rebuilt finding 8). "Dispatch already prefers the thing's own kind's word" (§3.4) is true only among `*.done` words.
- Routing `done` to the owner's `close` needs a declaration (`writes="done: word=issue.close"`) that the draft doesn't count.
- **`to=` is a free setting of each verb:**
  - `task-move <task> to=Backlog|Now|Done` takes the taskboard's own lane values (`apps/taskboard/build_lines.py:16-32, 93`);
  - `issue.move … to=open|in_progress|closed` takes the Tracker's (`build.py:44`);
  - `window.move` moves windows.
  
  `Done` folds to `done`, a stage name. Reading `to=` as a stage generically reinterprets every `move`.
- **Change:**
  - routing only for words that declare they take a stage;
  - stage names spelled so they can't fold-collide with owner values (e.g. `to=stage:done`);
  - the 130k-line dispatch replay before and after.

### V8. No post-condition on writes (read; imagined)
- The trial's `gh.close` writes `state=closed` only (`build.py:47`). After step 2 ("the owner's word"), a `done` on an issue closed as `not_planned` is still dropped, and one with no reason is still unknown. The act "succeeded" without reaching the stage.
- **Change:** in the same act, the thing must answer the asked question `yes` after the write, or the whole act refuses ("gh.close left Fix login closed with no reason; gh-issue says done with state_reason=completed"). That's the round-trip law applied to writes as well as to "already there".

### V9. `?` means two things across the two drafts (read)
- `shape-reads.md` 2.1 §4 uses `?` as the **lenient** suffix (`seats:count?`, lines 120-124).
- `values.md` §3.3 uses it as a **question** (`closed?=no`). `done?` is ambiguous: a lenient text need `done`, or the question.
- Pick one grammar before either is built: for example `is:closed=no` for questions, or `~` for lenient.

---

## Medium
- **What "has" is for a question need (imagined).** "Dispatch stays on has" (§3.3) needs a definition:
  - if "has" means the thing's kind declares `means=`, loose notes and member-made kinds are never reached, and plain words fall through (the C3 swap again);
  - if it means the deciding aspect is present, a thing with no lifecycle aspect at all is reached and refused, which is honest.
  
  Use the second. Questions count zero in ranking, as `reads=` does (shape-reads 2.1 §5b.5).
- **"Already there" is safe for the fence, with three caveats (read; imagined):**
  - With nothing written, nothing needs fencing, and a repeated painted press stays a no-op (`kernel.py` `_run` press check).
  - **But it's decided on the caller's view:** a hidden deciding aspect sends it down the write path (V4).
  - **No record means no happening:** rules and modules hearing `done` don't fire. That's right, but say so.
  - **On unknown it writes:** `move <gh closed, no reason> to=done` asserts `completed`. Record it as asserted.
- **Done isn't verified in Alex's own code.** `next_steps` separates "done claimed; acceptance unverified" from verified (`next_steps.py:119-127`). A due-soon word that skips `done?=yes` drops claimed-but-unverified cards that `next_steps` keeps showing. §7b's `verified?` is right in spirit; V3 says how it must be held.
- **Events are temporal.** `CONFIRMED=open` stays open after the event ends, and "done" for an event is "it happened". Say events answer `dropped?` and `certain?` only; the hierarchy is task-shaped.
- **The board's owner is a special case.** `means=` "on the post-kind declaration (dk333)" needs a rule in `decl()` that a declaration applies to things whose `post_kind` equals its name. The board accepts **any** visible kind declaration as a post kind (`board.py:96-100`), including members' (V1), so member-made post kinds will have no meanings: unknown, refused by acting words. Acceptable, if said.
- **Re-pointing governance freezes meanings.** Questions are global (`done?`), so "the words that ask the kind's questions" is every acting word with any question need, for every kind. The narrowing check then refuses every re-point once one such word exists. Define reliance (declared `acts_on`, or observed use), or allow re-points with a record and a notice to the kind's users.
- **§7b's refusal routing to "the kind's keeper":**
  - **It's a new notification channel** (uncounted).
  - **It carries raw values:** an unknown value can be private free text. The House's manager writes free-text `status` notes on cards (`manager.py:11`). Apply the `kept` rule: id and "an unmapped value", unless the keeper can see the thing.
  - **"The keeper" on the desktop is JEFF,** an agent acting with Alex's steward rights (`kernel.py:1912-1927`). "Each unknown is answered once and stays settled" means an agent settles the meanings that gate paid workers, recorded as Alex. Decide whether an agent may declare `means=`, or only propose it.

## Low
- "unknown" is an answer, not a stage; drop it from the hierarchy picture.
- **Folding doesn't fix spelling:** `canceled` and `cancelled` are both in `builders.HELD` (`builders.py:25`). The owner lists both. Say so, so nobody expects folding to merge them.
- **A fact named `closed` already means a poll is closed** to `vote` (`words.py:816`). Fine under `means=`, but a reader may confuse `closed=yes` with the `closed?` question.

## §7b's two questions
**Does a separate `verified?` reopen hub creep?** Yes, the creep moves from stages to questions.
- One review round took the kernel's vocabulary from 5 questions to about 13: `done? closed? dropped? held? open? active? not-started? queued? waiting-on-person? blocked? duplicate? verified? certain?`.
- Each question is a kernel concept, with a map per vocabulary (N × Q), and a kernel release to add.
- **Proposed bar:** a question enters the kernel only if
  - two or more apps' **acting** words need it to avoid harm;
  - it can't be derived from lifecycle plus holds;
  - it names who can make it yes.
- `verified?` passes only as an attestation (V3); `certain?` passes for events only. `queued`, `waiting-on-person` and `blocked` fail it: the first is a lifecycle refinement, the other two are hold reasons (V2).

**Who may set it, and can a member forge it?**
- **Who:** only the designated reviewer, as a person in a direct session, through the one word, against the current basis.
- **Members:** can't forge Alex's today. `attested()` checks the author is the reviewer, and `set` refuses others' cards (ran, V6).
- **Agents can:** Alex's agents can forge it (ran, V3), so can any module or House session acting as Alex, and so would anyone able to set a value that a `means=` maps to `verified?`. Fix V3 first; then `verified?` is never value-mapped.

## Simplest version (imagined)
1. **Now, in source, small:**
   - one shared hold function used by `builders.held` and `next_steps` (the two HELD sets become one, with `closed`/`done` and the safety holds kept);
   - reserve the attestation facts and require a person session for `task-verify`/`task-review` (V3);
   - count every declaration field as governed, and apply one declaration per scope to closed declarations (V1).
2. **Keep `house.build` on task cards** (shape-reads 2.1 already says so). The 507-closed failure then can't happen, and needs no value design.
3. **v1, read-only:**
   - `means=` on owner kinds, leader-gated, lifecycle only: not-started, active, done, dropped, plus broad open and closed, and unknown;
   - refinements only when consistent (V5);
   - readings expose `stage` and where it came from, and `rows … stage=` filters (24/37 → 37/37);
   - acting words check the stage in their own code, and refuse unknown.
   
   No question needs, no write routing, no `writes=`, no overlays.
4. **Writes:** the owner's words, by full name. `move <issue> to=Done` dispatches to the Tracker's own word, or is refused there.
5. **Later, each on evidence from a rerun:**
   - hold things (V6) with any-of `held?`;
   - questions as needs, with an unambiguous grammar (V9);
   - routing for words that declare a stage, with post-conditions (V7, V8).

## Cost (imagined)
- **The draft:** 600–800 lines after shape-reads v1.
- **Not counted:**
  - the governance fix (V1);
  - two-axis holds with every existing hold source declared (V2);
  - attestation hardening (V3);
  - `writes=` restriction and hidden-aspect refusal (V4);
  - refinement consistency (V5);
  - hold things, an index of what's `about` a thing, and reader-independent evaluation (V6);
  - routing declarations and the dispatch replay (V7);
  - post-conditions (V8);
  - the grammar choice (V9);
  - the keeper channel;
  - adoption across `builders.py`, `manager.py`, `next_steps.py`, the board, and the taskboard's lenses and verbs.
- **My estimate:** 1,300–2,000 lines with tests for the full draft. The simplest version is about 300–450, plus the step-1 source fixes, each under 50 lines.

## What would change my mind
- **On V2:** if every hold source in today's code could be expressed as values of one owner aspect per vocabulary (no separate flags), a single stage axis would do. The code says it can't.
- **On V6:** if hold facts on the owner's thing never reached a sync-out adapter and were always public by intent, the overlay as facts would be simpler and acceptable.
- **On the simplest version:** if a rerun showed module authors getting the stage check wrong in their own code, question needs would earn their kernel place sooner.

## Not verified
- The House, manager and `next_steps` running with any of this.
- Whether real cards carry the safety-hold facts today (I didn't read the live world).
- GitHub's current `state_reason` behaviour beyond the prior-art file's citations (recall, not checked).
- The other reviews of `values.md`, if any. I didn't read them, to stay independent.
