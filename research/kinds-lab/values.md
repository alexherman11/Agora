# What values mean across apps

> **Draft 2, by Claude, 28 Oct 2026, late,** after the adversarial kernel review (`review/values-kernel-review.md`) and JEFF's review (§7b). Not approved, not built, except the two source fixes in §0.3. Draft 1 is kept below, from "Draft 1" on.

## Draft 2

### 0.1 What the review changed
1. **Held isn't a stage; it's a second axis with many authors.**
   - The code already reads seven or more hold sources, in two places that disagree (`builders.held`, `next_steps`).
   - Several of them are safety holds: approval required, permission, an external effect whose outcome is unknown.
   - Draft 1's `held?` (the owner's value, or an overlay) would have dropped those from the gate on paid workers.
   - It also made a paused `Now` card both active and held. And GitHub, which can't say held, would have answered `held?` *unknown* forever, so `house.build` would refuse every open issue.
2. **Holds are their own things, never facts on the owner's thing.**
   - The overlay was forgeable: any maker wrote `held_by=house` on their own thing (ran).
   - It leaked: a House reason ("waiting for Alex's approval on …") reached every reader of the card.
   - Writing it bumped the card's rev, so a sync adapter's fenced writes went stale, and a sync-out adapter would carry it outside (JEFF's dk1290).
3. **`verified` is an attestation, not a value.**
   - An agent for Alex could attest "verified by Alex" (ran). **Fixed tonight** (§0.3).
   - `verified?` is never answered from a mapped value: a GitHub label "verified" brought in by an adapter must not count.
4. **Meanings are governed like shapes.** A member's later closed declaration of a kind replaced the steward's (ran). **Fixed tonight** (§0.3).
5. **A refinement counts only when it agrees with its base.**
   - GitHub's `state_reason` records the last transition, not the current state. `state=open` with a stale `state_reason=completed` isn't done.
   - `reopened` is ignored.
   - Disagreement is a conflict, said as one.
6. **Writes:**
   - `writes=` may name only aspects its own `means=` maps, with values from that map;
   - it refuses if any aspect it writes is hidden from the caller;
   - the record says the value was asserted by the caller.
   - **A post-condition:** after a write, the thing must answer the asked question *yes*, or the whole act refuses (`gh.close` that leaves no reason isn't done).
7. **Routing is a new dispatch layer** and is deferred.
   - `to=` is each verb's own setting (`task-move to=Done` is the taskboard's lane), so it's never read as a stage generically.
   - A word that takes a stage says so, and stages are spelled so they can't fold into owner values (`to=stage:done`).
8. **Grammar collision:** `?` is "lenient" in shape-reads and "question" here. **Proposal:** questions are `is:closed=no`; `?` stays lenient.
9. **A bar for adding a question to the kernel.** A question enters only if:
   - two or more apps' acting words need it to avoid harm;
   - it can't be derived from lifecycle plus holds;
   - it names who can make it yes.

   That keeps the hub small: one review round had grown it from 5 questions to about 13.

### 0.2 The picture after both reviews (imagined)
```
lifecycle    the owner's value, read through means=
             open: not-started (queued) · active        closed: done · dropped (duplicate)
holds        any-of, each with its author: owner values that mean held · declared hold facts · hold things
             reasons: waiting on a person · blocked · approval · permission · unknown effect
attestation  verified: the reviewer's own act, in their own session, against the current basis
events only  certain?
answers      yes · no · unknown (unknown is an answer, not a stage)
```
**JEFF's §7b points, placed:**
- `queued` is a lifecycle refinement.
- Waiting on a person and blocked are hold reasons. That's what they already are in the code: `waiting_on` and `blocked_on`.
- `verified` is the attestation.
- His "teach the vocabulary once" stays, with two changes:
  - the refusal carries the id and "an unmapped value", not the raw value, unless the keeper can see the thing;
  - an agent may **propose** a `means=`, but a leader, in person, declares it. A meaning that gates paid workers is never settled by an agent recorded as Alex.

### 0.3 Fixed tonight, in source (ran; with tests; live since the 22:47Z restart)
- **One declaration per name per scope, closed ones too; a nearer one that hides an outer one needs a leader** (`kinds.py`, `validate_decl`; `test_shapes.py`).
- **`task.review` and `task.verify` are the reviewer's own act.** An agent or module can't attest for them, and `attested()` ignores records made through one (`next_steps.py`; `test_next_steps.py`).

### 0.4 Build order (imagined; the review's "simplest version")
1. **Small source step, not done:** one shared hold function for `builders.held` and `next_steps`. The two `HELD` sets become one, with `closed`/`done` and the safety holds kept. That's the House's code, so it goes to its keepers.
2. **`house.build` stays on task cards** (shape-reads 2.1 already says so). The "507 closed issues" failure then can't happen, and needs no value design.
3. **v1, read-only, about 300–450 lines:**
   - `means=` on owner kinds, declared by leaders, lifecycle only;
   - refinements only when they agree;
   - readings show `stage` and where it came from;
   - `rows … stage=` filters (24/37 → 37/37).

   Acting words check the stage in their own code, and refuse unknown. No question needs, no routing, no `writes=`, no holds as things.
4. **Writes:** the owner's own words, by full name. `move <issue> to=Done` goes to the Tracker's word, or is refused there.
5. **Later, each only on evidence from a rerun:**
   - hold things, with any-of `held?`;
   - questions as needs, in the `is:` grammar;
   - routing for words that declare a stage, with post-conditions.

**Cost:**
- **The full draft 1:** the review estimates 1,300–2,000 lines with tests, not my 600–800, which missed most of §0.1.
- **v1:** about 300–450 lines.

**It still waits on Alex's answer to shape-reads §6,** because `means=` is declared by the vocabulary's owner.

### 0.5 What would change my mind
- **If every hold in today's code could be said as values of one owner aspect,** a single stage axis would do. The code says it can't.
- **If module authors get the stage check wrong in their own code** in a rerun, question needs earn a kernel place sooner.
- **If owners don't declare** (vocabularies arrive as loose notes), `means=` has no home (draft 1 §7).

---
# Draft 1 (superseded)

> **Draft 1, by Claude, 28 Oct 2026.** Friction 2 in `trials/FRICTION.md`. In review, not approved, not built.
> - **Built on:** draft 0 (my thinking, written before the evidence; kept below as §8) and the prior-art research in `review/values-prior-art.md` (Jira, Linear, Notion, GitHub, sync tools, iCalendar, SKOS, Wikidata, OSLC, FHIR).
> - **Labels:** **read** (a source or code), **ran** (as printed), **imagined**.

## 1. The failures (ran, trials)
1. **A cross-app word can't tell done-ness.**
   - The House would start a paid worker on 507 closed issues: its `HELD` lacks `closed`.
   - Agora already has two `HELD` sets in source that disagree (research review).
   - A due-soon reminder needs a hand table per vocabulary.
2. **Writes invent values.** `move <issue> to=Done` wrote `status=Done`, a value the Tracker never uses. `status=paused` to GitHub would invent a state.
3. **Case and spelling:** a status filter found 24 of 37 cancelled items.
4. **RSVP to a `STATUS:CANCELLED` feed item** went through.

## 2. What every big tracker converged on (read, research)
- **Custom values sit in a small fixed set** that the value's owner picks when making it: Jira's 3 categories, Linear's 5+2 types, Notion's 3 groups.
- **Cross-project views, queries and automations use the set, not labels.**
- **OSLC Change Management** (OASIS) is friction 2 nearly word for word:
  - each server turns its own statuses into standard read-only flags (closed, inProgress…);
  - a client writing a flag gets 409; changes go through actions.
- **What failed:**
  - **Too few groups:** Jira can't say cancelled, which has meant years of disagreeing "done"s.
  - **Growing the set breaks old readers:** Linear's 2026 Duplicate type showed in its own UI as active until fixed.
  - **Pairwise sync maps:** they grow apps × apps, are case-sensitive, pass unmapped values through raw, and write back the "first value listed".
  - **Inventing on write:** Notion's select adds an option on an unknown value.

## 3. The design (imagined)
### 3.1 A small hierarchy of life stages, held by the kernel
```
open      not-started · active · held
closed    done · dropped (duplicate)
unknown
```
- It's split where the evidence says three is too few: cancelled is `dropped`, and paused or waiting is `held`.
- **It grows only by adding narrower stages** under existing ones (`duplicate` under `dropped`). So a word asking `closed?` keeps working when a stage arrives: the Linear lesson.
- It's the kernel's, versioned with the shape grammar. A world can't add top-level stages (no hub creep).
- **Certainty isn't a stage.** `TENTATIVE` is open; how sure a plan is would be a separate question, if ever needed.

### 3.2 The owner declares meanings, once, on its kind
```
make kind=kind name=gh-issue means="state: open=open closed=closed; state_reason: completed=done not_planned=dropped duplicate=duplicate"
make kind=kind name=ical-event means="status: TENTATIVE=open CONFIRMED=open CANCELLED=dropped"
make kind=kind name=issue means="status: Backlog=not-started Now=active Paused=held Done=done Cancelled=dropped"
```
- **The most specific aspect wins:** `state_reason` refines `state`.
- **Matching:** values compare after locale-free case folding and trimming. A declaration that folds two values together but gives them different stages is refused.
- **Optional, declared:** what absence means (Google's absent `eventStatus` is scheduled), and a default for unmapped values. Both are **unknown** unless declared.
- **Governance:** leaders only, the same as shapes (the review's point that `spells=` must count as a shape applies here too).
  - Re-pointing a value (`Paused`: held → dropped) changes what words do, so it's checked like narrowing against the words that ask the kind's questions, and recorded.
  - Jira's silent propagation is the case to avoid.
- **Where the owner is a sub-kind** (the board's events live under `post_kind=event`), `means=` sits on the post-kind declaration (dk333). That's the "who is the owner" question the kernel review raised.

### 3.3 Words ask questions; answers are yes, no or unknown
`done?`, `closed?`, `dropped?`, `held?`, `open?`. As a need on a word: `needs="closed?=no"`. In a reading: `values["closed?"]`, with the deciding aspect and raw value in `reading.from`/`raw`.

**The rule** (SKOS broad/narrow):
- **yes:** the value's stage is the one asked, or narrower;
- **no:** it's disjoint;
- **unknown:** it's broader (GitHub `closed` with no reason, asked `done?`), or unmapped.

**What words do with it:**
- **`house.build` needs `open?=yes held?=no`,** so unknown refuses. A paid worker never starts on a guess. This is the costliest failure in the trials, fixed.
- **due-soon skips `done?=yes`,** and lists unknown with a mark.
- **`board.rsvp` needs `dropped?=no`,** so a cancelled feed item is refused with its reason.
- **Lists filter on the question:** `rows task through=task closed?=no`. Case and spelling stop mattering to readers.

**Dispatch stays on "has"** (shape-reads §1): the question is checked at admission, so an unknown answer is a refusal with its reason, never a silent swap.

### 3.4 Writes never write the stage
`move <thing> to=done`, or a plain `done <thing>`:
1. **Already there:** if the thing already answers `done?=yes`, write nothing and say so. (The round-trip law; no "first value listed" rewrites.)
2. **The owner's word, if it has one:** `issue.close`, `gh.close`. Dispatch already prefers the thing's own kind's word.
3. **The owner's declared write:** `writes="done: state=closed state_reason=completed"`, in the owner's spelling and case.
4. **Otherwise refuse,** naming what the vocabulary can say: "gh-issue can't say held; it says open, or closed (completed, not planned, duplicate)". **Never invent a value; never fall back to the raw name.**

### 3.5 Held is often someone else's overlay
The House pausing a card isn't the Tracker's lifecycle. When the owner can't say held, the House writes **its own** hold fact on the thing (`held_by=house held_why=…`), not a value in the owner's `status`.
- `held?` reads yes if the owner's value is held **or** any hold overlay is present.
- That ends the trial's `status=paused` → "set lane=paused" advice.
- It also answers JEFF's worry (dk1290): the House never writes into a field another app syncs out.

## 4. On paper against the trials (imagined; needs a rerun)

| Failure | With this |
|---|---|
| House on 507 closed issues | `open?=yes held?=no` → refused, with the stage and raw value |
| Two `HELD` sets that disagree | gone: `held?` is one question |
| due-soon's hand table | `done?`, one question |
| `move <issue> to=Done` writes `status=Done` | §3.4: the owner's word or declared write, else refused |
| `status=paused` to GitHub | refused, naming what gh-issue can say; the House writes its own hold |
| 24/37 cancelled by filter | `dropped?=yes` → 37/37 |
| RSVP to a cancelled feed item | `dropped?=no` → refused |

## 5. How it joins shape-reads
- `means=` sits beside the producer spellings of shape-reads §6. Both are declared by a vocabulary's owner, on its kind. **So both wait on Alex's answer to §6.**
- **If §6 is no,** the fallback is the research's alternative C: each shared kind lists every vocabulary's values (N×M), or B, value things. Both are worse, and both are named in the research.
- **The questions are new need forms** (`closed?=no`), versioned with the grammar. An older kernel fails closed (the C4 fix).

## 6. Cost (imagined)
- **Kernel:**
  - the stage hierarchy and question evaluation, about 150 lines;
  - `means=`/`writes=` parsing and governance, about 150;
  - readings and need forms, about 100;
  - write routing in `move`/plain words, about 100;
  - tests.

  About 600–800 lines with tests, after shape-reads v1.
- **Adoption:** the House (`held?`/`open?` instead of `HELD`), the board (`dropped?`), and declarations on the four trial vocabularies.

## 7. What would change my mind
- **If owners don't declare,** because vocabularies arrive as loose notes, `means=` has no home: value things (B) or consumer maps (C).
- **If real words need more than about ten stages,** or separate branches per domain, one hierarchy is wrong.
- **If a rerun shows "unknown" dominating** what words ask, refusing on unknown blocks work, and owner defaults become required.
- **If meanings depend on context** (Canvas's state lives on the *submission*, not the assignment), a flat map isn't enough. That's FHIR's `dependsOn`, or bonds: the held graph work.

## 7b. JEFF's review from inside the world (dk1307, 28 Oct 22:24Z)
Asked in Shop talk, as someone who works with these values daily. **What it changes (imagined, to be reviewed):**
1. **Refuse on unknown only for words that act.** Words that only read (his task list, views) show "unknown" instead.
   - The refusal carries the one line that teaches the vocabulary, for example: "'Resolved' in Jira isn't known yet; `set <jira kind> means=…Resolved=done` settles it".
   - It goes to whoever keeps that kind (JEFF on the desktop), never to Alex. Each unknown value is answered once and stays settled.
2. **Verification is its own question, not a stage.** "Done isn't one moment for me": received → reviewed → landed → live → verified by Alex.
   - He told Alex things were live today because "done" was ambiguous.
   - So `verified?` (yes, no or unknown) sits beside `done?`, the way certainty sits beside stage for events.
   - The hierarchy stays small. Other yes/no questions are separate, few, and kernel-held.
3. **Narrower stages he uses daily:**
   - under `not-started`: **`queued`** (agreed, not started) apart from a mere idea;
   - under `held`: **waiting on a person's decision** apart from **blocked by another thing**, because he chases them differently.

   **Reopened** is a move back to open, not a stage. The record keeps the history.
4. **The hold overlay is right.**

**The hierarchy after his review (imagined):**
```
open      not-started (queued) · active · held (waiting-on-person · blocked)
closed    done · dropped (duplicate)
unknown
questions beside the stage: verified? · certain?
```

## 8. Draft 0, and what the evidence changed
**Draft 0** (written before the research) had the same core: groups, an owner's map, readers ask the group, writes go to the owner's word, case-insensitive.

**What the evidence changed:**
- **The groups:** from 4 flat groups (`open/active/done/cancelled`) to a hierarchy (open: not-started, active, held; closed: done, dropped), with growth only by narrower stages. That's the Linear and Jira lessons.
- **Answers:** from a single group value to **three-valued questions**, so "broader than asked" is unknown, never a guess. That's SKOS and the GitHub `closed` with no reason.
- **Writes:** from "owner's word or refuse" to also "already there → write nothing" and "declared writes". That's the round-trip law and Getint's explicit default.
- **Held:** an overlay the House writes on its own. Draft 0 didn't see this; JEFF's concern and the research did.
