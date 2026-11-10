# Adversarial kernel review of kinds-intelligence.md draft 0, by a review agent for Claude, 28 Oct 2026, late

> **What this is.** A review of [[kinds-intelligence]] draft 0, against the working tree tonight. No repository file was edited except this one. The live world, `sessions/*.pickle` and `keep/sessions.json` were not touched.
> - **Read:** the draft; `shape-reads.md` §5b, §6; `values.md` draft 2; `review/values-kernel-review.md`; `review/privacy-authority-review.md` (Round 2); `kinds-decisions-for-alex.md`; `kernel/kinds.py`, `dictionary.py`, `kits.py`, `kernel.py` (`guard`, `shown`, `find_entry`, `plain_verb`, `reaches`, `_rule_matches`, `_fire_rules`, `on_offer`, `_refresh_offer`, `actor_for`), `words.py` (RESERVED, `claim`, `role`, `verb`, `rows`), `store.py`, `bonds.py`, `next_steps.py`; `modules/house/house.py`, `builders.py`, `manager.py`; `agents/MOVING-IN.md`.
> - **Ran:** `probe_ki.py` in `scratchpad/review-ki/`, on fresh temporary worlds. Output is quoted as printed.
> - **Note:** `kinds.py` and `kernel.py` changed under me while I read (children by declaration landed). Line numbers are from the second read.
> - **Labels:** **read** (file:line), **ran** (as printed), **imagined**.

## Verdict in eight lines
1. Alex's direction holds up: one place holds the kinds, producers declare, the system notices duplicates. The prior art supports it.
2. **The draft contradicts itself on the one guard that matters.** §2.2 says support "never grants"; §2.4 says acting words admit "declared" meanings. A hostile producer's declaration is "declared".
3. **The kernel has one `fits` for reading and acting.** Anything wired into it (supports, same, a mapping) reaches acting words and plain-verb dispatch. Acting words already reach by structure today (ran).
4. **"Its own kind" has no owner in the code.** A member squats any kind name first, and her closed declaration carries `supports=`, `map=`, `means=` unchecked (ran).
5. **"Same" can't be read-only.** It's identity, so it either widens `house.build`, grants and rules, or it isn't "same".
6. **On the desktop the three bands collapse to JEFF.** He's a person and a steward, so he passes "a leader, in person" (ran). A paid builder agent passes the kernel's leader check too (ran).
7. **What the librarian sends a model isn't private:** aspect names hold person ids, and value sets hold phone numbers and free text (ran).
8. A smaller first build delivers the direction without these: declared supports, two-party, read-only, plus a deterministic duplicates report. About 400–550 lines with tests.

## What the probes printed (ran, `probe_ki.py`)
| # | Probe | Printed |
|---|---|---|
| A | Steward: `task needs="title"`, verb `task.close acts_on=task`. Bea makes `kind=gh-issue title=…` | `actions` as Alex: `as a task: task.close`; plain `close`: `ok set ki82 [r7] · closed=yes · ~ task.close` |
| B | Bea's first declaration: `name=gh-issue supports=task map=… means="state: open=done"` | `ok make ki83 [r8] · a kind · ~ no other kind has supports=; … still made, as you said`; `decl: ki83 made_by Bea · supports task` |
| B3 | Steward then declares `gh-issue` | `refused: gh-issue is declared here already (ki83); set ki83 changes it` |
| B4 | Bea declares `todo supports=task` | `ok make ki84 [r9] · a kind` |
| C | JEFF joins; `role JEFF leader` | `JEFF steward: True · actor.kind: person`; `make kind=kind name=ticket extends=task` → `ok` |
| C6 | A builder agent session for Alex | `kind agent, person is Alex: True`; `make kind=kind name=jira-item extends=task` → `ok`; Bea's `jira-item` then shows `as a task: task.close` |
| D | Kit with a kind; add `supports=` to the bundle | `refused: not a definition-only kit (version 1)`; Bea `take`s the plain kit: `made_by: Bea · origin: {'world': …, 'thing': 'ki89'}` |
| E | Kernel kind names that are also word names | `['component', 'grant', 'group', 'kit', 'module', 'rule', 'widget']` |
| F | Bea claims a seat with a phone; a module reads the note | for Alex: `['claim:ki78', 'contact:ki78', 'in:ki1'] · a value: 555-0199`; place-wide: `['claim:ki78', 'in:ki1']` |
| G | Undo a declaration after a word acted through it | `undid r22: make widget-x [r25] · closed still = yes` |
| H | `urgent-task extends=task`, verb `urgent.page acts_on=urgent-task`, Bea's unmarked note | before any mark: `ok set ki97 [r29] · paged=yes` |

---

## Critical

### K1. "Declared" lets a producer's support reach acting words (read; ran A, C6)
- **The contradiction (read):** §2.2: support "never grants … a hostile producer … gets its things listed, never acted on". §2.4: "Acting words admit only declared or confirmed meanings." A producer's own declaration is "declared".
- **One `fits` serves both (read):** `check_word` → `_lacks` → `fits` (`kinds.py:325-340`, `190-211`). `plain_verb` ranks by `kinds.reaches` (`kernel.py:630`), which counts `_descends` as "mine", rank 0 (`kinds.py:385`). Lists use the same `fits` (`words.py` `rows`). Wire supports into `fits` or `_descends`, and it is `extends` without the leader check.
- **Acting words already reach by structure (ran A):** with no support at all, Alex's plain `close` ran `task.close` on Bea's `gh-issue`. That's Alex's approved rule, words reach things that fit. "Supports never widens acting" therefore needs a new split, not a sentence.
- **What still holds (read):** grants match the target's own kind (`kernel.py:957`), rules match `of_kind` exactly (`kernel.py:1608-1610`), the House matches its own kinds (`house.py:58-59`, `manager.py:55`, `next_steps.py:110`). Support doesn't widen those, unless "same" does (K3).
- **Fix:**
  - Two readings in `kinds.py`: `fits` (acting, dispatch, `actions`) and `fits_reading` (lists and `through=`). Support enters only the second until accepted for acting.
  - Delete "declared" from §2.4. Acting words admit only acceptances that met the acting bar (K4, K5).

### K2. "It may declare only for its own kind": nobody owns a kind name (ran B, D; read)
- **First come owns (ran B3, B4):** a member's closed declaration is legal when it's the first in its scope (`kinds.py:418`, `434`). The steward then can't declare that name, only `set` hers.
- **Its other fields aren't governed (ran B):** `validate_decl` counts only `needs`/`extends` as shaped (`kinds.py:418`). Tonight's V1 fix stops a second declaration, not a first one carrying `supports=` or `means=`. The `~ still made` hint warns, nothing refuses.
- **Kits re-author (ran D5):** `take` sets `made_by` to the taker (`kits.py:200`). The bundle's `source` is only format-checked (`kits.py:34`), so "from GitHub's world" is self-declared.
- **Kind names have no namespace (read):** `KIND_NAME` allows no dot (`kinds.py:26`). Words have one: `gh.*` is the gh module's (`dictionary.py:20-26`). A module can't publish kinds at all today: `on_offer` makes word entries only (`kernel.py:1822`).
- **And members can already name their kind `task` (privacy review H3, ran there).** A hostile producer doesn't need `supports`, so the draft's blast radius is bounded by own-kind claimability, which is unfixed.
- **Fix:**
  - Every field of a kind declaration except `name title help` counts as shaped (leaders only).
  - Kinds get namespaces like words: a module's kinds are `<module>-*`, and the module owns them.
  - Support is **two-party**: the producer offers it on its own declaration; the target kind's keeper accepts it, in the target's scope.

### K3. "Same" is identity, so it is never reading-only (read; imagined)
- **If "same" resolves where kinds are matched,** `todo` things meet `house.build`'s `kind=taskboard-task|task` (`house.py:59`, matched raw in `Need.met`, `kinds.py:48-56`), grants with `only=kind:task`, and rules with `of_kind=task`. Accepting "same" would start paid workers on things nobody declared as tasks.
- **If it doesn't,** it isn't "same"; it's an alias for typing.
- **Things can't be migrated:** `kind` is RESERVED (`words.py:222`), so a merged `todo` keeps its spelling forever. 147 places compare kind strings directly (ran, a rough grep over `kernel/`, `modules/`, `community/board`), many in out-of-process modules that see raw rows.
- **Transitivity is the `owl:sameAs` bite (imagined):** `todo`=`task` (accepted in G) and `task`=`ticket` (accepted at the place) make `todo`=`ticket`, which nobody accepted.
- **Fix:**
  - v1 has no "same".
  - Later, "same" is an **input alias only** (`rows todo` means `rows task`). Stored kinds, markers, grants and rules stay exact.
  - It's accepted by a leader in person, never auto, never transitive.

---

## High

### K4. Who accepts: JEFF passes "a leader, in person", and so does a paid builder (ran C; read)
- **JEFF is a person and a leader:** "Agents are people… JEFF is a person and a leader" (`MOVING-IN.md:13`), and "An agent is a person in the world" (`house.py:3`). Ran: `actor.kind: person`, steward `True`.
- **The draft's band 3 cites values V3,** which is about `kind=agent` actors. It doesn't exclude JEFF. So JEFF can be band 2's keeper and band 3's leader, and the bands mean nothing on the desktop.
- **Builders are agents for whoever asked** (`builders.py:123-132` picks the requester's agent session). `validate_decl` checks `actor.person` only (`kinds.py:436`), so a Codex worker for Alex declared `jira-item extends=task` (ran C6). The `task.verify` fix checks `actor.kind` (`next_steps.py:193`); kind declarations don't.
- **The property at stake** is §2.5's "machines notice; people decide". JEFF accepting a librarian's proposal is a model ratifying a model.
- **Fix:**
  - Now (source, small): kind declarations and acceptances refuse `actor.kind != "person"`.
  - **Alex's call:** may JEFF accept acting mappings? If not, the kernel needs to tell a House-run person from a human. Either a kernel-kept fact set by kdesk's entry, or "no steward-made `house-agent` names this person".

### K5. The bands aren't enforceable as drawn (read; imagined)
- **They mix two axes:** confidence (high / middle / low) and effect (reading / acting). Band 3 is defined by effect, the others by confidence.
- **Fellegi–Sunter's thresholds** sit on match weights from m- and u-probabilities estimated over many labelled pairs. Four vocabularies make about six kind pairs. A model's stated confidence isn't such a weight.
- **"Lossless, affects reading only" is a claim the proposal makes,** but only the kernel can compute it: does any `do` word act on the target kind, by `acts_on` or by shape? Under K1, almost always yes.
- **"Confirmed" is one bit.** JEFF's middle-band confirmation becomes "confirmed", which §2.4 admits to acting words.
- **Fix:**
  - The effect decides who accepts, computed by the kernel.
  - Confidence only decides whether a proposal is shown.
  - Each acceptance records its acceptor and the bar it met; acting words read only acting-bar acceptances.
  - Auto-accept is off until a replay gives an error rate (the draft's own §6).

### K6. What the librarian sends, and where proposals land (ran F; read)
- **Aspect names carry ids (ran):** a module for Alex sees `claim:<person>` and `contact:<person>` with the phone `555-0199`. A place-wide module sees `claim:<person>` and `in:<group>`. Also `answer:<question>` and `member:<person>` (`words.py:228`).
- **Value sets are data:** the House's manager writes free-text `status` notes (`manager.py:11`), so "the value set of `status`" is every card's note.
- **Kind names are data** too (a member's private kind's name).
- **Alex's approved rule is "public, or my own".** An aggregate over everyone's things is neither, so an outside model gets nothing but public kinds.
- **Proposals as world things leak samples:** a `make` defaults to `sees=place` (`kernel.py:432`). Evidence samples from Alex's private things would show to every member. The privacy review's derived-visibility limit applies: `visibility_of` takes one parent, so fail closed to `sees=me`.
- **Fix:**
  - Send only declared names (kinds and aspects) of public declarations; never `prefix:` aspect names, never values.
  - Local model only for anything else.
  - Proposal things are `sees=` the acceptor, with counts, not samples, unless the acceptor can see the sample.

### K7. Children by declaration doesn't hold for acting words (ran H; read). Tonight's build, not the draft.
- **`fits` refuses an unmarked child** (`kinds.py:204-209`). But `_lacks` falls back to `missing(row, ks)`, which is empty when the thing has the child's needs (`kinds.py:337-338`). Ran: `urgent.page` paged Bea's unmarked note.
- `test_shapes.py:560` checks only `rows meeting`.
- **Fix (about 3 lines plus a test):** when `fits` fails and nothing is missing, lack `is.<kind>=yes` ("marked a meeting").
- **Also, said plainly:** a child's membership is declared by whoever may `set` the thing (`mark`, `kinds.py:545-568`), not by the child kind's keeper. Members can self-declare into narrower kinds, the same as K1's producer.

---

## Medium

### K8. Determinism (read; imagined)
- **Replay is safe if proposals and acceptances are records:** facts are the truth and `words` are never parsed on replay (`store.py:4`). The draft has this right.
- **If a model is consulted inside an act:**
  - acts hold the kernel lock (`kernel.py:1076`), so every other act waits on the model;
  - modules get 10 s (`modules.py:35`);
  - the call is an outside effect made with the actor's sight;
  - `trail` and `undo` can't say why.
- **Gaps:**
  - The deterministic pass must run as the reader sees. "38 things share…" counts things the reader can't see.
  - A rejection must be a durable record ("not same as"). Otherwise the librarian re-proposes forever, and "a counted miss" isn't a no.
  - shape-reads §5b.1's basis fingerprint must include every support fact a reading used. An acceptance changes readings without changing the declaration's rev.

### K9. Scopes (read; imagined)
- `decl()` is nearest-first (`kinds.py:138-151`), so `task` in G can differ from `task` at the place.
- "gh-issue supports task" must name the target **declaration** by id, the way stored lines bind entry ids (`dictionary.py:118-128`).
- It's accepted by that scope's leaders. A mapping onto the place's `task` doesn't carry to G's.

### K10. Undo reverses the mapping, not what was done under it (ran G)
- `closed still = yes`. That's right, but say so, and record on each act the mapping it used (K8's basis), so the trail can show it.

### K11. Kits and offers (ran D; read)
- **Kits refuse `supports=` today (ran):** safe, not portable. Carry it with the target named by kind, not id, because `validate` refuses ids outside the kit (`kits.py:99-100`). Re-validate at `take`.
- **Acceptances never travel.** Each world's keepers accept for themselves.
- **"A mapping only adds" isn't how offers behave:** `_refresh_offer` re-points any field the module itself wrote last (`kernel.py:1886`). Producer declarations through offers need the add-only check in that path.

## Low
- **Name collisions if kinds join the words' namespace (ran E):** `component grant group kit module rule widget` are both kernel kinds and word names.
- **`bonds.py` calls a kinds API that no longer exists:** `spellings`, `canonical`, `fill`, `fits(reader, …)` (`bonds.py:169-175`, `544-545`). It's held (`kernel.py:123`), so it's harmless now, but the "iceberg lattice" pass can't reuse it as is.
- **§4's Twitch example:** a channel supporting `chat` is fine read-only. But `say` acting on a supporter would be an outside act (Pike's rule), so K1's split matters most there.

---

## The three relations (imagined, grounded)
- **Distinct by effect, not by meaning:**
  - **narrower** is in the code as `extends` plus a marker (K7);
  - **supports** is `extends` plus a map, in another vocabulary;
  - **same** is an input alias (K3).
- **Missing:**
  - **not-same** (`owl:differentFrom`), a durable no (K8);
  - **related/overlaps** (SKOS `closeMatch`), for a Canvas assignment vs its submission;
  - **context-dependent** maps (values draft 1 §7, FHIR `dependsOn`).
- **Over-merging bites at:**
  - identical aspect names with different models: `capacity` remaining vs total (shape-reads §5b.6), window `at` vs place, `status` free text vs lifecycle;
  - transitive chains: `gh-issue supports task`, and `task` fits `event` by `start`, put issues on calendars.
- **Rule:** supports doesn't chain; each hop is its own acceptance.

## Kinds into `dictionary.py`? (read; imagined)
- **Keep `kind=kind` things as the entries,** with their own namespace. Don't make them `kind=word` (ran E's collisions; `find_entry`'s "already answers here", `dictionary.py:27-29`).
- **Borrow from the dictionary:**
  - labels and aliases on the declaration;
  - a stable id that references bind to (`acts_on`, `extends`, `of_kind`, `only=kind:`, `tag:` gain `_bound` twins, as `do_bound` did);
  - a steward edit word.
- **What migrates:** references, not things (`kind` is RESERVED). The House's and the board's own-kind checks stay raw on purpose.
- **A dictionary *view*** (`kinds` already exists) shows names, keeper, supporters, and pending proposals.

## Smallest first build (imagined; lines include tests)
1. **Source fixes now, each under 30 lines:**
   - every kind-declaration field but `name title help` is governed (K2);
   - kind declarations refuse agent actors (K4);
   - the child-kind `_lacks` fix (K7).
2. **`supports=<kind> map="a=b …"` on a kind declaration**, offered by its maker. A leader of the **target's** scope accepts with one word (`kind.accept <decl> for=<target>`), recorded with who and in what scope (about 150).
3. **Lists only:** `rows <kind>` (and `through=` when shape-reads v1 lands) include accepted supporters, renamed by the map, marked `as: gh-issue supports task (accepted by Alex)`. `fits`, `check_word`, `plain_verb` and `actions` unchanged (about 80).
4. **Kits carry `supports`/`map`,** the target by name, re-validated at `take`; acceptances don't travel (about 40).
5. **`kinds.alike`, a see word:** candidate duplicates from names, spellings and aspect overlap, computed as the reader sees, no writes, no model. Residents read it and propose in chat; a leader accepts (about 120).
6. **Not in v1:** same, auto-accept, the model, acting reach, value meanings.

**About 400–550 lines.** The last two estimates here ran 2.5× over (220 → 569), so plan for the top.

## Answers to the draft's §5, briefly
1. **The librarian** is a module or role that only proposes. Its acceptor is never itself, and for acting, not JEFF unless Alex says so (K4).
2. **Everything goes through a keeper at first.** Yes.
3. **One dictionary per world,** with kits. An upstream shared dictionary is an outside service (K6) and a second authority.
4. **"Same" vs supports:** merge only by alias, by a person; otherwise support (K3).
5. **The kernel holds declarations and acceptances; a module proposes.** The kernel must not depend on the model.

## What would change my mind
- **On K1:** if Alex wants support to reach acting words once accepted, as `extends` does, two-party acceptance by a person is enough, and the reading split becomes a convenience.
- **On K3:** if every kind check in the House, grants and rules moved to declared entry ids, "same" could be real identity. That migration is the price.
- **On K4:** if Alex says JEFF is his keeper for meanings too, the human check goes. Then say so in the draft, and keep it from builders.
- **On K6:** if the model is local-only and proposals are acceptor-only, the privacy findings drop to Low.
- **On the build:** if a deterministic report on the trials' 2,174 things already finds the four vocabularies' duplicates, the model waits. If it finds almost none, the model earns its place sooner.

## Not verified
- The live world, the House running, any model.
- Whether real producers would declare (the draft's own first doubt).
- The children-by-declaration build beyond `_lacks`; it was landing while I read.
- The 147 count is a grep, not a reading of each site.
