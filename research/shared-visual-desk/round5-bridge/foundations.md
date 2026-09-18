# Round five foundations audit: the actual scene bridge

2026-09-18. Foundations, Astra team. Scope: audit Claude's current `scene.py`, generic `lens.js` painter, style compiler and `/api/scene` integration. No competing compiler, app, stylesheet or final desktop was built. Only this report and `scene-probes.py` are owned by this researcher. All probes use newly constructed in-memory data, actual source imports and a minimal mocked DOM for style compilation. No saved sessions, network calls, HTTP server, deployments or live-world mutations are used.

## Repair addendum — 2026-09-18, later same-day source revision

Claude's team repaired two of the initially reproduced defects while the collaborative audit was running. I reread the current `scene.py` and `lens.js`, changed only those two probes into positive regression assertions, and reran the full suite: **18 of 18 observation assertions pass**. The current composition is 3 original supported checks, **2 repaired positive regressions**, **11 remaining defect reproductions**, one positional-identity limitation and one mixed style test. The other 16 probes were not weakened. This is collaborative progress, not a regression in Claude's implementation.

- **Count binding repaired:** a root that selects two appearances now renders `2 notes` rather than literal `$n notes`. The positive check asserts both the scene value and text output.
- **Silent 100-character cut repaired:** the original 113-character sample now appears in full. A second, 312-character sample verifies the new 240-character limit explicitly reports `240 of 312 chars printed here` and directs the reader toward the full content. This establishes disclosed truncation for the tested case, not unlimited full output or measured pixel equivalence.

Current source identities for this rerun:

```text
scene.py            38b4e86c99cf371df45bab5efec370ad75d2493902d55b654bdf28bd42eaa807
desk-shell/lens.js  f502fcf3be676b5bc0e13587e881bec145b8c1047caae9f5a066105f49742aa9
```

The other nine source hashes are identical to the original complete hash list below. All eleven hashes were stable before and after this rerun. Together, these two replacements and the unchanged nine entries identify the complete current tested source set.

The reread also found new source-level changes: unknown text variables are refused, `at item` checks for a free parent, the text printer explains that CSS clamp may show fewer wrapped lines, and the painter now writes the scene key to `data-key`. Those observations are not additional executed workflow checks in this suite. The painter still replaces children rather than reconciling by key, and no new browser continuity claim is made.

**The original audit body and original source hashes below are retained as historical evidence. Its text-truncation and unbound-count rows describe the earlier source and are superseded by this addendum.** The binding, literal transport, recursion, unsupported gesture, remaining identity, style and prepared-packet limitations are not withdrawn.

## Conclusion

This is a real, useful foundation direction: authored world notes can select material, describe hierarchy/roles and expose actions through one scene representation, with no app-specific painter code. The current bridge already preserves subject-versus-appearance identity and supports declarative repetition. It is a materially stronger candidate than our round-four policy interpreter wrapped in three hand-coded apps.

The stronger source claim that the shared tree makes text and pixels unable to disagree is not established and is false in concrete cases. The bridge still needs a small explicit contract for literal data, identity, supported interaction, admission, bounds and observations. Merely adding more scene words would not repair those boundaries. Nor would replacing the missing cases with app-specific JavaScript satisfy the current user direction.

## Source coverage and execution

Read all of `scene.py`, `desk-shell/lens.js`, `desk-shell/lens.html`, `desk-shell/style/style.js`, and the relevant complete GET/POST/session integration in `deskd.py`. Read `design-studio/ROUND-FIVE.md` as project context, not authorization to enter sessions or edit another owner's files. Read selected actual world/desk construction, seen-revision fencing and command paths to design the synthetic tests. These are current source observations, not claims about the running server at port 8780.

Ran:

```powershell
python -B research/shared-visual-desk/round5-bridge/scene-probes.py
```

Result: **18 observation assertions passed**. This means the reproduced outcomes matched expectations, not that 18 healthy workflows passed. The suite contains 3 supported-behavior tests, 13 tests named `DEFECT`, one positional-identity limitation, and one style-compiler test covering both supported and defective outcomes. All 11 source hashes matched before and after the run. The test runner imports actual `World`, `DeskKnife` and `scene` without loading any session; style compilation executes actual `style.js` in Node v24.19.0 against a minimal document stub. This is not a browser rendering test.

## Supported behavior, independently reproduced

**Subjects and appearances remain distinct.** One synthetic subject is placed twice. The compiled scene has two items with separate placement boxes and keys, while `$id` resolves to the shared subject and `$item` resolves to each appearance. This passes the identity distinction that round four failed to represent.

**Repeated occurrence keys survive selection reordering.** Reversing selected appearances leaves the key associated with each appearance unchanged. This supports stable occurrence binding at the scene-data level. The current painter recreates DOM and does not use those keys for reconciliation, so stable scene keys do not yet prove draft/focus continuity.

**Some definition failures are clean refusals.** Unknown scene properties and missing referenced parts raise `LensRefusal`. Separately, the style compiler rejects a literal off-scale pixel property during parse and retains its previous installed stylesheet. These are specific admitted/refused cases, not full definition-time validation.

## Reproduced defects and their consequences

| Boundary | Exact observed result | What it defeats |
|---|---|---|
| Text projection | A 101-character prefix plus a marker remains complete in `scene.text`, but `to_text` slices to 100 characters without an omission notice | Complete logical-content agreement; painter reads the full value |
| Template comma | `text "Hello, world"` is split at comma-space and refused | Quoting does not protect ordinary literal text |
| Template comment | `text "Keep # this literal"` becomes `Keep` | Literal content silently changes |
| Backslash data | A literal path containing backslash-n is turned into a new definition line before parsing | Source transport/data are conflated |
| Count variable | A repeated root has `n == 2`, but text `$n notes` remains unresolved | A documented variable is not actually bound |
| Recursive part | A self-repeating `each root` yields Python `RecursionError`, not a bounded lens refusal | No safe admission/execution bound for this definition |
| Repetition budget | 1,200 selected instances all compile; source loop contains no scene-node budget | No explicit negotiated resource bound; this is not a claim about an ultimate machine limit |
| Duplicate definition | A later top-level `root` silently replaces the earlier one | Definition identity is ambiguous |
| Duplicate child | Two sibling children named `child` get the same scene key despite different text | Keys cannot uniquely address all admitted nodes |
| Command data | Subject text `She said "yes"` interpolated into a quoted rewrite command becomes `She said yes` when the actual desk executes it | Runtime action transport loses literal data |
| Stale observation | A rewrite from an old observed revision refuses; prefixing fresh `look item;` makes that same draft rewrite succeed after another author's edit | The painter refreshes the stale-write fence without refreshing the decision basis |
| Gesture support | `drop` is admitted into scene actions while current painter has no drop branch | Text advertises an interaction the implementation cannot perform |
| Observation binding | Compiled actionable nodes have occurrence identity but no observed subject/appearance revision or expected-version action field | The scene cannot directly bind a later gesture to its observed generation |

The stale-fence probe uses the real in-memory desk command path. Alice observes an appearance; Bob rewrites its subject; Alice's previous observed revision is restored to model her original scene. A direct rewrite refuses as stale, while the painter-shaped `look ...; do rewrite ...` succeeds and overwrites Bob's text. This is stronger than a source suspicion, but it is still a synthetic command reproduction, not a concurrent browser test. The actual painter source supplies the fresh-look prefix. The fix is not simply omitting it: the scene endpoint currently does not bind or record the exact observation needed to authorize an act on an otherwise unseen item.

The quote-loss probe uses the emitted action verbatim. Mutation recipes require the authored introducer and the native command introducer: `on click do do rewrite ...`. Removing the second `do` emits a command the desk does not accept. Editing independently caught a harness that had accidentally repaired that mismatch and corrected its tests. Read-only commands such as `read` do not need an extra native `do`, so a renderer should not blindly add it.

List repetition over tags currently keys by array index. Reordering tags preserves index keys while changing their associated values. That is a documented limitation here, not proof that every primitive list needs identity allocation. A minimum contract must declare whether a repeat is keyed or positional and what continuity, if any, a positional repeat promises.

## Style is part of the bridge, not a solved layer

The actual style compiler has a useful parse-refusal/last-good property for one invalid pixel declaration. It also accepts `role card : pad missingToken`; resolution records an unreadable property, while the installed role omits the padding. The painter uses a role class, so this diagnostic is not automatically part of the scene's text/interaction explanation. Definition acceptance is therefore weaker than renderability.

More directly relevant to the requested boundary, `token sneaky = ok; outline: 99px solid red` is accepted as a fallback word token and emitted unescaped into the generated root stylesheet. The probe sees the extra declaration in the actual compiled stylesheet text. This is a benign source-generation demonstration, not a browser-executed exploit or an authority/security claim. It nevertheless falsifies the idea that the authored language necessarily prevents raw CSS merely because lens syntax has no CSS clause. Token values need typed grammar and deliberate serialization too.

The current lens paints declared role classes from one static style file. It does not establish that all style-language conditional clauses, overrides, provenance and presentation declarations are represented in the semantic scene. Source comments and shared token names alone do not make style semantics part of the text/pixel contract.

## Same scene does not mean same observed view

The current text projection describes a logical scene and some authored/appearance geometry. Browser wrapping, font metrics, clipping, scrolling, overlap, focus and live input can change what is actually visible. For example, `clamp` in `to_text` counts explicit newline-separated source lines, while CSS line clamp operates on rendered line boxes. The same integer does not establish the same visible substring. This is a source-based architectural counterexample; no browser wrap measurement was made by this researcher.

Similarly, stable keys exist in scene data but the painter replaces all children and does not reconcile by key. It suspends polling while an edit/drag is busy, which can preserve a local interaction temporarily but leaves the server observation increasingly old. The refresh cache compares only scene/refusal data, while the endpoint also reports an event count and text header. An unchanged scene can leave that displayed observation header stale. These source observations should guide a browser contract test, not be relabeled as completed browser evidence.

`deskd.py` catches `LensRefusal` around scene compilation; it does not catch the reproduced `RecursionError` in that branch. A scene GET also enters the session context whose exit saves actor state. This audit did not call that endpoint, precisely to keep tests detached from live persistence. File locking, crash consistency, authenticated authority and all server failure modes were outside this bounded bridge audit.

## Minimum contract before adding more interface vocabulary

1. **A typed semantic scene and declared support.** Versioned node kinds, layouts, roles, content fields and interaction kinds must have validated arguments. Reject unsupported combinations such as drag without required geometry, and unsupported gestures such as drop, or expose them explicitly as unavailable. Unknown roles/variables must be diagnostics, not unexplained blanks or literal placeholders.
2. **Unambiguous address and binding.** Every admitted node key must be unique in its generation. Bind occurrence identity, subject identity, definition revision and relevant observed material revisions separately. Keyed and positional repetition must declare different continuity guarantees. Renaming a part cannot silently be treated as durable material identity.
3. **Literal data separate from command syntax.** Author action intent as an operation reference plus typed arguments; carry input text as data without trimming, quote substitution or string-replacement metacharacter semantics. If text commands remain the exact human interface, give them a single round-trip serializer/parser boundary rather than interpolating user data into a command template. Keep native authority and admission in the existing action path.
4. **Gestures act on their observed generation.** Send the binding and revision seen when the interaction began, with any explicit preconditions. Resolve/refuse at the authoritative action path. Do not turn stale pixels into fresh permission by prepending an unobserved read. Preserve an unsettled draft and make retry/rebase/discard an explicit supported policy.
5. **Bounded definition admission and evaluation.** Detect duplicate names, recursive expansion and missing references; budget scene nodes, nesting, text/output size and selection expansion. Use structured diagnostics carrying definition location. Keep the previous accepted definition/renderable scene available while an invalid draft is edited. This is separate from staging effects of a valid interaction that later fails.
6. **Honest projections.** One logical scene can feed both outputs, but text must disclose omission and unsupported meaning. Add a distinct optional observed-view report for actual clipping, focus, camera and mounted generation when the task needs it. Do not claim pixel-identical visibility from shared source alone. Resolved style/provenance needs an inspectable route too.
7. **A deliberate extension boundary.** App authors should create definitions, schemas, material and native action compositions inside the environment. Extending a reusable renderer primitive is runtime/core development with conformance checks, not permission for each app to ship arbitrary JS/CSS. Opaque specialized media engines may remain necessary, but their mounts, state, capabilities and evidence need declared contracts rather than a silent escape to implementation code.

These are properties and admission boundaries, not a proposed replacement compiler. The next step should repair a narrow set in the existing bridge and rerun the same probes. A useful minimum repair experiment is a long, quoted multiline document shown in two appearances: edit through one authored lens, preserve all literal bytes, refuse against an intervening revision, retain the draft, and render/read the accepted result through a different authored lens. No app-specific host branch should be needed.

## Peer contributions and evidence boundaries

Editing independently authored three existing-grammar lenses and reported successful in-memory definition rewrite/undo, material preservation, new-subject inclusion and action-scope changes, plus invalid-definition persistence and missing role validation. Its initial action harness had repaired missing native `do`; the corrected harness executes emitted commands verbatim. Those authoring checks are separate from this suite and should be read in `authoring.md`.

Media independently executed actual painter listeners with a fake DOM and reported whitespace/quote loss, empty-delete failure, replacement-string metacharacter behavior, unimplemented drop, missing pointercancel cleanup, and clearing prior pixels on invalid definitions. Those are its reproduced listener results, not browser screenshots or independently rerun by this researcher. The observer also warned against claiming a missing native mount capability from stale docs; native runtime reuse is its separate source audit.

Our disagreement is productive: an extensible scene vocabulary does not prove broad application authoring, while a fixed vocabulary does not need to pretend to cover every domain. The minimum positive test is whether independent authors can build materially different useful interfaces from the same native material/action boundary without writing app-specific host code. The supported scene probes and Editing's fixtures are evidence toward that test; the defects identify what currently breaks it.

## Independent review of the coordinator's prepared-action experiment

At the coordinator's request I read `prepared_actions.py` and `test_prepared_actions.py` and independently reran all seven tests successfully. This is a useful narrow response to the literal/observation failures: scene compilation and binding share one owner lock; handles retain target/definition revisions; typed values enter actual structured desk dispatch; unrelated subject edits need not invalidate a content action; moving one appearance does not invalidate the separately bound subject edit. Unsupported actions are explicit. The two host adapters recognize existing rewrite and move templates; they are runtime bridge code, not hidden app-specific UI code.

The experiment is not yet an integrated replacement bridge. Its offer packet replaces scene actions `{on,line}` with typed descriptors. Passing that packet's scene to the existing actual `scene.to_text` raises `KeyError: 'line'`, independently reproduced with the coordinator's fixture. Existing `lens.js` also expects line strings. Both projections need an explicitly updated action-descriptor contract; retaining arbitrary command evaluation as fallback would undo the boundary this experiment establishes.

Additional source-review limits: `inspect()` omits the retained parent identity/revision guard used for a drag; at most 128 outstanding handles persist until cancelled or consumed, with no automatic frame expiry; compiler recursion and duplicate-key defects remain inherited. The bridge owns a deep-copied in-process desk and excludes rules/hooks/follow to make staging meaningful. It is not an HTTP/authentication/persistence integration, production gateway or external-effect transaction. The tests justify the literal-safe, revision-bound two-operation claim, not those broader claims.

Audited companion hashes: `prepared_actions.py` = `CCFC54138EF2CB4C3A22FF50B0D1217EDD0DB968A13EFD6DA504667C1D1996D1`; `test_prepared_actions.py` = `A8F0F78FEA92F3728D2860663D79CAF8C9E942C25B83E97ADC3618E311684F78`. These identify the reviewed version; subsequent coordinator changes require rechecking the affected claims.

Team desk record: a149/s148 summarizes this audit; c150 on Editing's a140 acknowledges definition-only authoring as evidence against our earlier adapter-heavy approach and challenges activation/literal safety; c151 on Media's a142 challenges descriptor compatibility across both projections. No Claude studio messages were posted by this researcher.

## Exact audited source identities

SHA256, relative to `research/text-desk-lab/notation/`. These matched before and after the probe run; later source changes require rerunning rather than treating this report as current by assumption.

```text
scene.py                         4957d5218f539cca2f91b04dfc35f99f80d034a52cae1c8e7a432d9f4c06e68d
desk-shell/lens.js               ed3e88fcd83c8ab7ee93642ac231440c2dab8632c8794276fc182ffc81f4d97f
desk-shell/lens.html             e787658a76a56335130d47e08e471880b3e394d3af20a8dfae7e8778917b3935
desk-shell/style/style.js        b5f68d26b37d423d4fab60bb528591e6e23a071c3b725ecee7ef08b84c83e482
desk-shell/style/calm.style      1e5695ed6f579b1ee93de91e9b3c88b8948f672362812ed6a93a5f886681f4dd
deskd.py                        7605316dccd599f90160befce5f8ae85bad3bc2d0a57ec25247a1824f59b8321
desk-shell/core.js               be92eb9da68de1401d1443eaa92b9cf9482d1742cf26a854d6d6f87acd4e8959
world.py                        44c01e818655988ee4513796639d55fa66b7598215a7e550d8c4d6e7999b748b
desk.py                         cbfb251f68da467949c663034c5b4d7ee122bff8bc43775c89b47ed60b0c3652
desk_moo.py                     f8f65e57dcfdea21c9f9b148abeccafbe270c1c946f92a103c707f262a18f8aa
desk_knife.py                   d87af7dedefb95181d3c0703ba424e2da7bf58027f5f51211ad887c7617cc304
```
