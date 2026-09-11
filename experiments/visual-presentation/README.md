# Agora: two worldlines, one evolving desk

September 9, 2026 · Real JEFF execution · Isolated worlds

**The experiment supports building a native presentation layer. Its strongest benefit is making common visual intent reusable and inspectable. It does not eliminate interface engineering, and the small prototype initially had worse human interaction in two places.**

Both systems eventually fulfilled the nine scenario requests, including authoring a layout beyond the prototype's catalog. The prepared presentation layer substantially reduced routine source rewriting. Once the current system had built a reusable capability, it could also operate cheaply. This points toward a small, extensible contract—not a closed visual vocabulary or a promise that everything should become a declaration.

[Inspect the raw metrics](evidence/metrics.csv) and [independent checks](evidence/independent-checks.json). The complete private worldlines and visual gallery remain in the original experiment workspace.

## What actually ran

The current-system world used a copy of the working Agora3 runtime and the **actually installed shell: source revision 12, installation revision 9**. It was not compared against an older starter shell. The prototype used that same starting shell plus the presentation slice described below. Original project files, the original native world, and the original running VM were left alone.

Each world had its own native event store, bridge and Linux VM. A third, separate VM supplied resettable candidate execution. Both JEFFs used the real managed account adapter with **gpt-6-astra, high reasoning**, a 360-second turn limit and a 70-call bound. Each received the same nine requests in the same sequence: **18 real model turns**. No model training was involved.

The fixtures were six synthetic notes and an unsent draft. During the trajectory, I added a reading note and then a read-only reference card. After JEFF finished, I independently added another reading note to test the new circle's continued behavior. Each JEFF could reuse what it had built earlier.

Both worlds received identical experiment tools for real browser measurements, input and read-only candidate previews. JEFF saw geometry, computed styles, controls and errors; it did **not** receive screenshot vision. I separately reviewed captures. The requested browser sizes were 1440×1000 and 390×844; the protected host header reduced the shell's inner height.

## The implemented slice

I implemented typed native presentation rules rather than inventing a new textual parser. Rules select surfaces by identity, tag or view kind and contribute style, layout or chat composition. Higher-priority contributions override individual style properties. Retained layouts derive effective geometry while preserving original placement data.

The prepared slice included:

- Paper/color, typography, padding and radius properties.
- Live grid, alignment and snapping layouts.
- Conversation placement and sizing.
- Preview, inspection, revision-checked writes and bounded rule undo.
- A local Free placement / Resume layout control.
- Note and read-only reference-card adapters.
- An Appearance dialog using the same installed action package as JEFF.

The browser and native actions used the same JavaScript evaluator implementation. Native actions executed in the guest and returned proposed native writes through the existing gateway. No new authoritative storage system or privileged host renderer was added.

This is a small slice. The surface adapter still depends on existing shell functions and selectors. It is not a general renderer registry, universal constraint solver, full CSS replacement, or implementation of the entire draft documentation.

## Results by scenario

Times include JEFF's chosen development and verification work. They are observations from one trajectory, not benchmark estimates.

| Request | Current system | Prototype | Observed result |
|---|---:|---:|---|
| Persistent warm-paper reading style | 244s | 61s | Both correct. Current JEFF authored renderer logic; prototype JEFF saved a rule. |
| Live, title-ordered two-column grid | 239s | 72s | Both correct, including an independently added reading note. |
| Chat below desk, 300px area, 60px composer | 150s | 103s | Both correct after prototype JEFF repaired a real sizing defect. |
| Only Working memory uses 22px text | 150s | 51s | Both correct. Current JEFF extended its schema and renderer; prototype JEFF added a scoped override. |
| Undo only that exception | 36s | 35s | Both restored inherited 18px text and preserved earlier changes. |
| Reference card joins shared presentation | 228s | 62s | Both preserved its identity and read-only data. Current JEFF built the view; prototype JEFF broadened rule scope. |
| Narrow screen and return to desktop | 188s* | 108s | Both usable without another layout implementation change. |
| Impossible fixed-width fit | 15s | 20s | Both explained the contradiction and made no presentation change. |
| New live circle layout | 250s | 228s | Both authored it, retained styles/data, and disclosed overlaps with stationary notes. |

\* A transient Windows sharing error interrupted a status-file read while baseline JEFF continued normally. This time was recovered from the native assistant-message timestamp minus activity start; it excludes the small polling/finish overhead included in the other rows. No model task was repeated because of that error.

| Across the nine requests | Current system | Prototype |
|---|---:|---:|
| Sum of per-request elapsed times | 24m 58s | 12m 21s |
| Native verb invocations directly issued by JEFF | 163 | 145 |
| Package source saves | 12 | 3 |
| Package installations | 6 | 3 |
| Serialized arguments on JEFF's native invocations | 2,871,315 bytes | 508,333 bytes |

The prototype reduced summed elapsed time by about **51%**, source saves by **75%**, and serialized invocation arguments by about **82%** in this run. The byte count is **not a token-usage or billing measurement**. Full-file package payloads, including copied library code, contribute heavily to the current-system total. A better surgical source-editing workflow could reduce that cost too.

The relatively modest reduction in invocation count is revealing: JEFF still spent time discovering, inspecting and verifying. The larger reduction was in how much implementation work those calls had to carry.

## What JEFF's behavior revealed

### Routine customization became a shorter kind of task

For styling and maintained layout, prototype JEFF generally followed “inspect → preview → save → observe → reload.” It changed explicit intent rather than reproducing the renderer. The local exception also had an understandable relationship to the shared style: a higher-priority rule overrode text size alone.

Current-system JEFF was fully capable of the same outcomes, but repeatedly entered development mode: read source, author code, build, inspect a candidate, install, then verify. It also built reusable behavior rather than merely moving today's four notes. In the override case it extended `desk.note-style` with an optional body-size field. The subsequent undo therefore required only a native data edit, explaining the near tie.

### Some of the time difference was JEFF's discretionary testing

Current-system JEFF installed a guest browser test environment and tested membership changes, focus and selection, scrolling, read-only behavior, light/dark settings, and additional viewport sizes. A missing browser library and a mobile reference-body sizing issue were detected and repaired during that work.

That validation has value. The full elapsed difference cannot be treated as an unavoidable language cost. The stronger evidence is the repeated difference in required source/build/install work for the routine requests.

### A declaration was not proof that its renderer honored it

The prepared prototype accepted a 60px composer setting but implemented it as a minimum height; the browser rendered roughly 81px. Prototype JEFF noticed the mismatch, inspected the installed source, repaired the CSS, tested a candidate and installed it. The measured 103-second chat result includes that repair.

This is an important requirement for Agora: an agent needs to compare intended and observed presentation. A successful action response is insufficient. The initial smoke test checked chat placement and draft continuity, but did not assert exact composer height, so it missed this defect.

### The escape path remained usable

Circle layout was deliberately absent from the prepared catalog. Prototype JEFF extended the native rule schema, action package, evaluator and browser integration, then exercised the candidate and installed it. Its package build and candidate exercise alone took roughly 59 seconds, largely in the separate candidate environment.

Current-system JEFF changed its renderer and reused its guest tests. Both arrived at the same circle: centers on radius 260 around (500,350), upright 190×170 surfaces, title order clockwise from the top, and automatic membership updates.

The prototype's routine advantage largely disappeared here. That is acceptable if adding a family is an occasional development task and subsequent use is cheap. It would become a problem if ordinary creativity constantly required coordinated edits across those layers.

Both JEFFs disclosed the two overlaps with the stationary non-reading notes. Adding more members can crowd the circle further. They preserved the requested geometry rather than silently moving unrelated subjects. The impossible-fit scenario likewise demonstrates sound **JEFF reasoning**, not a general feasibility guarantee supplied by the evaluator.

## Human interaction exposed a different quality gap

After the measured runs, I performed an independent real-pointer text-selection test and exercised the Appearance dialog. These checks found issues that the successful agent-facing scenarios had not covered:

1. **The prototype lost selected reference-card text on refresh.** Its adapter reassigned unchanged text nodes. The current-system implementation preserved selection for the full 15-second check.
2. **The prototype's Appearance dialog used the wrong registry field.** Its action lookup expected `tools` instead of `actions`, so the human buttons failed even though JEFF could invoke the native actions correctly.
3. **The initial human preview only outlined geometry.** It did not visibly preview color and typography.

I repaired those in a **separate post-comparison review build**, without changing the recorded JEFF outcomes or timings. The retained prototype now preserves unchanged text nodes, reads the real action registry and previews styles/composition transiently.

The repeat checks confirmed:

- Real selected text survives refresh for 15 seconds in both worlds.
- Preview visibly changes paper color and text size with **zero native writes**.
- Closing Preview restores the saved presentation.
- Keep changes applies the style; Undo restores the previous inherited appearance.
- The draft, circle geometry and exact chat dimensions remain intact after reload.

This distinction matters: the experiment supports the presentation model, but it also shows why a good agent API cannot substitute for testing the human interface.

## What I would carry forward

**Keep the small native contract.** Persistent scope, explicit property contributions, inspectable causes, revision-checked edits and local exceptions all proved useful. They fit the existing native world and reduce the need to rewrite the shell for familiar requests.

**Keep executable extensions available.** The circle test supports an extensible system. It does not support binding Agora to the prepared grid/align/snap vocabulary, the current numeric ranges, or one universal evaluator architecture.

**Make rendered-state inspection and shared capability discovery dependable.** The composer mismatch and broken human action lookup were contract failures across layers. Stable surface parts, a common registry adapter, and observable effective values are more consequential than choosing a CSS-like syntax now.

**Treat interaction continuity as part of presentation.** Selection, focus, scrolling, draft preservation and manual placement belong in the contract and tests. The current-system JEFF's reference-card work was stronger here than my first adapter.

**Reduce extension duplication before broad adoption.** The evaluator was embedded in the shell as well as packaged for native actions. Circle support required coordinated updates. A versioned renderer/capability attachment could reduce that burden without restricting what a package may implement.

I would continue with this direction, while deferring the wider architectural commitments you wanted to revisit. The evidence favors making ordinary changes declarative and reusable; it does not justify freezing Agora's creative vocabulary.

## Evidence and limits

The independent final checks passed **58 assertions for the current system and 59 for the prototype**, the extra check comparing the native inspector with rendered desktop geometry. These covered styles, arrangement, mobile overlap/overflow, precise undo, unchanged impossible-fit presentation, circle geometry, reload, late arrival, native identity, original text, draft continuity and unrelated placement. They do not imply collision-free circle layouts or full usability coverage.

Pre-comparison validation also included 90 runtime tests passing, an explicit compiled-runtime inventory test passing with a local mock model, 108 evaluator cases, 22 browser/native-action smoke checks, a shell-assembly regression, and existing documentation/lint checks. Real model authorship is established separately by the 18 recorded runs.

There was one discarded initial attempt caused by a candidate-preview login defect in the harness. It was corrected, both previews passed preflight, and the measured comparison restarted from fresh fixtures. Setup also exposed a shell-insertion bug involving a bundled-library string; the retained assembly regression covers it. These failures are recorded in the experiment notes and excluded from model timings.

This remains one paired sequential trajectory with no randomization or repetition. Both worlds shared a host, account and serialized candidate VM. Prototype preparation is outside request timing. The reference-card adapter was prepared in advance, so that case does not demonstrate support for an arbitrary unknown third view kind. Smaller agents, large workspaces, concurrent edits and performance at the query bounds were not evaluated. The polling adapter, limited form, bounded undo and duplicated evaluator remain prototype limitations.

This compact archive retains metrics, checks, the final native action package and the repaired shell. Complete initial/final source snapshots, traces and browser captures remain in the original experiment workspace. No private world database, credential or VM image is included here. The main Agora world remains separate.
