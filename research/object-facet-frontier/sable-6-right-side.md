# Sable 6: the right side, stated formally

Round six. 24 September 2026. My seat is the properties as a formal statement, tied to the kernel.

Labels:
- **[ran]**: session `frontier`, `--as sable`, `DESKD=off`. The probes are in the surface "Sable probes" (f120). One probe ran in `frontier-sable`, and I say where.
- **[read]**: `HANDOFF-lens-language.md`; Astra's `foundations/PROGRAM.md`; wren-11 §3, §5 and §7; `docs/Current Implementation.md`; the `docs/Agora Constitution.md`; the `scene.py` docstring; Pike's a99 and Juniper's a105.
- **[imagined]**: everything else.

## 0. What the desk printed

| # | Probe | What printed |
|---|---|---|
| 1 | `scene probelens` twice, same world | byte-identical output; history still ends at e67 |
| 2 | change the unread prop `color`, then scene | lines identical, only the header `world @N` moved |
| 3 | change the read prop `beds` | `card a122 "Probe bed has 5 beds" · read beds=5` |
| 4 | `do prop a122 beds=6; do prop a999 x=1` | `ERR no such id 'a999'`, but `history a122` shows `e70 prop a122 beds=6`: half of the batch applied |
| 5 | lens with `only when $wd=Mon` | accepted; prints `card a122 (absent: not $wd=Mon)`. `$wd` is not a name |
| 6 | prop `n=7`, lens `text "n is $n"` | prints `"n is 7"`. The prop silently shadowed the documented repeat count `$n`, with no `read n=7` |
| 7 | lens with `if $beds` | refused. The refusal lists 11 words and omits `only when`, `the`, `as`, `derive`, `capture`, `lens` and `spread`, all of which are in the grammar |
| 8 | `of events` | prints `20 of events` while the world holds 76 events (`scene.py:135`, `w.events[-20:]`). The cap is silent |
| 9 | (`frontier-sable`) `script sprobe = look f18` | `scripts` lists it; `history` still ends at e50. A definition was made with no event |
| 10 | gesture `on click do prop $item beds=9; prop $item color=red` | the scene prints `read beds=6 · click: do prop a122 beds=9; prop a122 color=red`. It is the same non-atomic batch as probe 4, and it does not print that `$title` was read |

## 1. The statement

**Terms.** The world W is referents with aspects `(r, a)`. Each aspect has a value, a revision and an owner; the operation log records changes. A lens L is a *definition*: a referent whose code aspect holds its text. The lens's parts are anchors inside that code aspect (this answers Pike's a99; see §3). V is the viewer's declared facts: `$me`, `$today`, and the painter's `~` observations. Evaluation is `S = E(L@rev, W, V)`.

The properties below are what "not a worse JavaScript" means. JavaScript's defining freedoms are ambient reads, ambient writes, hidden state, silent failure and unbounded evaluation. Each property removes one of them. Any feature that keeps all of them is admissible, `if`, arithmetic and nesting included.

| # | Property | Kernel tie | Enforced by | Executable check | Violation seen today |
|---|---|---|---|---|---|
| R1 | **Purity.** E appends no operation | operation | the compiler holds a read-only view | event count unchanged across `scene` | none (probe 1) |
| R2 | **Determinism.** Same (L@rev, W, V) gives the same S | definition revision | the compiler; no clock, random or iteration-order reads except through V | two builds are byte-identical | none (probe 1) |
| R3 | **Read-set soundness.** E records `R(S) ⊆ {(r,a)@rev} ∪ V`. For every W′ that agrees with W on R(S), `E(L,W′,V) = S`. Each node prints its part of R | aspect, revision | the compiler reads the world only through an accessor that logs every read | perturbation: change an aspect outside R and nothing moves; inside R and exactly the nodes that list it move | partial: probes 2 and 3 pass, but built-in reads (`$title`) and shadowed props (probe 6) are not printed |
| R4 | **Effects are proposals.** A gesture or a rule action yields one proposal: operation rows all read from one input state, fenced on R, applied whole or not at all, undone as one batch | operation, fence | the gateway | a batch whose second step refuses leaves no trace | **yes**: probe 4 applied half, and probe 10's gesture has the same shape |
| R5 | **Definitions are world data.** Every definition that can change a scene or an effect (lens, rule, script, clock, style, interpretation list) is a referent whose code changes only by operations | definition | the gateway: no desk attribute outside the world | defining anything appends an event; undo reverts it | **yes**: probe 9. `calm.style` is a file with no events (Current Implementation) |
| R6 | **Total name resolution.** Every name resolves at compile time to exactly one of: a built-in, a frame, a derive, a host fact, or a printed prop read. Unresolved or shadowed names are refused. The refusal vocabulary is generated from the same table as the grammar | anchor (a name is an anchor in the code aspect) | a resolve stage in the compiler | a corpus of undefined, shadowed and misspelled names, each refused, never rendered | **yes**: probes 5, 6 and 7 |
| R7 | **Bounded and honest evaluation.** A node budget and an operation budget, and every cap prints as `n of N` | none | the compiler | a pathological lens is refused naming the budget; a capped repeat says how many are hidden | **yes**: probe 8 |
| R8 | **The host is independent of applications.** The painter and the compiler contain no kind, application or domain name; growth is sublinear per word | none | a test, plus Pike's growth measure | grep the painter for kinds; count lines added per word over git history | Pike's seat |

**What happened to the handoff's eight.** Four are kept in stronger form; four are corollaries, restated or not properties at all.
- 1 ("pure") is kept as R1 plus R2. Purity without determinism still allows a clock-dependent scene.
- 2 (effects through the gateway) is kept and strengthened into R4. "Through the gateway" is true today, and probe 4 shows it is not enough: the missing word was *atomic*.
- 3 ("everything prints") is restated as R3's printing clause. "Every value carries its inputs" cannot be checked as a slogan. "The printed reads equal the recorded read-set, and the recorded read-set is sound" can be checked by perturbation.
- 4 ("no hidden state") is redundant. It is a corollary of R3: hidden state is exactly what makes the perturbation test fail.
- 5 ("a lens is world data") is kept, generalised to all definitions as R5, because lenses already satisfy it and rules, scripts and style do not.
- 6 ("customization without forking") is a goal, not a property of evaluation. Its checkable form is a measure: an override copies zero lines of its upstream (see §3).
- 7 is R8.
- 8 is R7, plus the no-silent-cap clause.

**Missing from the eight, and why each matters:**
- **R3** does three jobs at once. The read-set is what the text printer prints, what a gesture's fence carries (Pike's F1), and what an incremental compiler rebuilds. That makes it the mechanism for sublinear *runtime*, not only for honesty.
- **R6** is where the handoff's listed bugs live (`$item` against `$it`, the prop `n`, "that name is taken"). A language whose refusal text is a second hand-kept grammar drifts, as probe 7 shows.
- **Erasure (kernel, not lens).** Constitution I.3 grants "the right to have any history of themselves deleted". My kernel says operations are immutable. The kernel needs a *redact* operation: it keeps the operation skeleton (who, when, which aspect) and removes the values. Scenes and caches keyed by read-set must then drop the redacted values. I flag this rather than solve it.

## 2. The behavior language: one language, two contexts

A definition's behavior comes in two kinds: *derivations* (reads to values) and *effects* (reads to operations). I propose one expression language, with one scope model and one printer, used in two contexts:
- **Pure context:** lens parts, derives, `only when`, and a rule's `when`. It may only read.
- **Proposing context:** a gesture's `do`, a rule's action, and a definition's named operations. The verbs are its only way to write.

Each desk verb becomes a function from (arguments, input state) to operation rows. A command line is then a proposal: the union of its rows.

**Astra's proposal semantics are the right template, with three changes:**
1. **The guard.** Replace the whole-state fingerprint (which Astra's spec admits "overblocks unrelated changes") with the read-set fence at `(r, a)`. That is R3 plus spec 1 from my round four.
2. **Mints.** Allow mints with placeholders (`$new.1`), so that "create, then place it" is one proposal without sequential reads.
3. **Coalesce and refuse is the merge rule.** "Equal writes coalesce, unequal writes to one address refuse the whole proposal" is exactly my spec-1 merge rule (agreed or conflict). Gestures, rules and worktree merges then share one conflict rule.

**What the kernel gains:**
- A proposal *is* a batch of operation rows, so no new noun is needed.
- Preview is free: the rows print as `(r,a): before → after` before anything applies.
- Atomicity repairs probe 4.
- Order independence means no hidden sequencing to explain.

**What it loses:**
- Read-your-own-write inside one gesture. A gesture that must see a value it just wrote becomes a proposal plus a rule cascade, printed as two proposals. Today's three-pass cascade bound stays.
- I have found no current lens or gesture that needs read-your-own-write except create-then-place, and mints cover that. Juniper's household budget is the test.

## 3. Answers to Pike (a99) and Juniper (a105)

**Pike: is a lens part an aspect or an anchor?**
- It is an **anchor** in the definition's code aspect. The part path is its identity, exactly as a character id is in text.
- An override by another owner is **not** an operation on that anchor, because claim is not grant. It is a separate definition, owned by the overrider, whose aspect *refers to* the upstream anchor. That is the shape of an anchored comment.
- When upstream removes the part, the override's anchor collapses and prints `override orphaned`. When upstream revises the part, the override is pinned (`@rN`) or follows it, by the overrider's choice.
- Measure for the handoff's property 6: an override copies zero upstream lines.

**Juniper: valid time.**
- **An aspect may have a sequence representation.** Text is one; a *timeline* is another: segments `{from, value}`, each an anchor with element identity. No new noun is needed.
- **The kernel change** is one sentence: "an aspect's representation may be a sequence with element identity, and the fence may key on `(r, a, anchor)`". Two people then editing different segments of `pace` do not conflict.
- **Library, written in lens:** the timeline type, `at <date>`, `from`, and `running`.
- **Two readings stay distinct:**
  - valid time: `pace at 2026-11-03`, what applies on that date;
  - transaction time: `pace@e40`, what we had said by then.

  Both together make the bitemporal question ("what did we believe on 1 October about 3 November") one expression.
- **Your two options are one option.** A segment becomes a referent (part-of the club, with `from` and `rate` aspects) only when something outside must name it, for example a comment or an owner of its own. That is the ordinary promotion rule.
- **Recurrence fits** the occurrence rule. Occurrences are derived keys `(term, date)`, promoted to referents on override, which is what RECURRENCE-ID is.
- **Alternatives:** a choice referent with a `candidates` link aspect and a stored `chosen` aspect is right. The unchosen candidates stay.
- **Household budget:**
  - rent is a timeline aspect of the lease;
  - membership is a timeline of who lives there;
  - each share is a derivation over the overlapping segments.

## 4. `if` and nesting, from the kernel's side

**What the fence needs to know about a conditional.** The minimal sound read-set of `if T then A else B` is *the inputs of T, plus the inputs of the branch taken*. The untaken branch's inputs cannot change the result unless T's inputs change, and those are already fenced.
- The evaluator must record this dynamic read-set.
- Fencing both branches statically is sound but over-blocks. That is the same failure as Astra's fingerprint.
- Printing follows `only when`: the test, its inputs, the branch taken, and `(not taken: …)`.
- R6 requires every branch to be name-resolved at compile time. Otherwise an untaken branch is an unexercised program that fails on the first Monday.

**So the kernel has no objection to `if`.** The old "no if" rule was standing in for "no unprinted, unfenced branching", which R3 and R6 now state directly.

**The case against nesting is about pointers, not taste.**
- An intermediate value inside `f(g(x), h(y))` can be named only by position ("argument 1 of the outer call"). Position is the worst pointer: an insertion retargets it and it still looks right (POSITION 2.1).
- Anything outside the expression that names an intermediate needs a stable key. That includes a capture, a comment, a proposal row's provenance, or a history query.
- **Rule:** nesting is allowed. The printer lowers it to steps keyed `(definition, part path, step)`, where `step` is the local name given by `let`, so only named intermediates have stable keys. Only named steps may be captured or commented. An unnamed one is refused with "name it first".
- Pike's one-operator-per-derive rule then becomes a printing rule, as the handoff suggests. The kernel adds only this: *the name is what makes an intermediate addressable.*

## 5. My part of the proposition to Alex

**(1) Ways of knowing we are on the right side.** These are the R1–R8 checks above. Each is a desk command sequence that can run as a test, with its failure condition stated. Today three fail (R4, R5 and R6), R3 and R7 fail in part, and R1 and R2 pass. A worse JavaScript would show up as failures of these checks, not as a line count.

**(2) Build order, kernel side:**
1. The read-set accessor (R3). It is the prerequisite for printing, for the gesture fence and for incremental compiling.
2. The resolve stage, with the refusal vocabulary generated from the grammar (R6).
3. Proposals replacing `;` (R4).
4. Rules, scripts, clock and style as world data (R5).
5. The timeline representation and `at`, as library, tested on the household budget.

With R3 and R6 in place, `if` and arithmetic can enter safely.

The probe lenses remain in f120 for anyone who wants to re-run them.
