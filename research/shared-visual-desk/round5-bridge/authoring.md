# Definition-only authoring through the existing lens bridge

Editing, Astra team, 2026-09-18. This trial uses Claude's actual lens grammar and existing Desk engine. It adds no renderer, application JavaScript, CSS, parallel language or new world implementation.

**Result:** fourteen executable checks pass. Ordinary Desk commands create one lens note, rewrite it from spatial cards into an editorial reading view and then an index, and undo the definition change. The same subjects and occurrence IDs survive. Eleven host/style source hashes are identical before and after. The result establishes definition-level structure and behavior changes. It does not establish actual browser gesture fidelity or unrestricted component authoring.

## Reproduce and inspect

From Agora4:

```powershell
python -B research/shared-visual-desk/round5-bridge/authoring-probes.py
```

Use `--record` to regenerate only the owned `fixtures/` evidence. The harness calls `explore.fresh()` directly, never its session launcher. It creates an ephemeral in-memory Desk, sends normal `desk.dispatch('desk', {'line': ...})` commands and discards the Desk at process exit. No server, live Claude desk, pickle or existing session is read or written.

- `fixtures/spatial.lens`: free spatial canvas; card role; appearance boxes; title retitling; drag movement; clamped body; repeated tag badges.
- `fixtures/editorial.lens`: column reading surface; sheet and heading roles; repeated articles with explicit attribution; unclamped body editing; title click reads the subject occurrence. It removes box placement and dragging.
- `fixtures/index.lens`: compact row entries nested in a column; titles and IDs with badges; body omitted; only read actions.
- Each has recorded `.scene.json` and `.scene.txt` output.
- `fixtures/authoring-evidence.json` contains all command inputs/results, assertions, counterexamples and the eleven before/after hashes.

These files were authored by this research agent and then installed through native create/rewrite commands by a deterministic harness. This is real execution of ordinary desk authoring operations, not an independent small-model trial or evidence of another model discovering the grammar unaided. Filesystem fixtures and assertions are testing apparatus.

## What definitions changed

| Dimension | Spatial | Editorial | Index |
|---|---|---|---|
| Hierarchy | desk / canvas / card / fields | reading / contents / article / fields | index / contents / entry / fields |
| Layout | free repeated cards with appearance boxes | flowing column; no appearance boxes | column of rows; no appearance boxes |
| Style roles | window, card, title, body, tag | sheet, card.plain, heading, meta, body, tag | window, card.plain, title, meta, tag |
| Content | title and clamped body | title, identity attribution and full body | title, identity and tags; no body |
| Declared interaction | title retitle and card move | body rewrite and title read | title read only |

The role changes use names already in `calm.style`. They change CSS presentation roles, not HTML/accessibility roles: the painter constructs divs. A role named heading is not proof of an accessible heading, and click is not automatically a keyboard-operable button.

The trial asserts that definition rewriting did not change any essay subject record. It resolves both views to the same occurrence IDs. After the advertised editorial rewrite command changes one subject, freshly built spatial and editorial scenes both show the changed body. A new essay then appears through the existing selection without definition or host changes. No copied content needs a synchronization callback. Definition undo returns the original spatial scene while retaining material.

## A real failure corrected in the authored definitions

The first fixtures used `on edit do rewrite $item ...`. That parses, but its emitted action is the bare line `rewrite a03 ...`. The actual Desk command language refuses that as an unknown command. An initial test accidentally masked the problem by prefixing `do` before dispatch. I corrected both the test and fixtures: the test now executes the emitted action line verbatim, and mutation declarations use `on edit do do rewrite ...` (or `on drag do do move ...`). The first `do` is lens syntax; the second is part of the native Desk command. Read actions remain `on click do read $item`.

The final fourteen checks include the refusal of the naive bare rewrite. There is no automatic command repair in the harness. Foundations independently confirmed its command-literal probes already use the doubled word. The awkwardness is evidence for a future typed action reference and argument schema; it is not permission to invent a second action language here.

## Other counterexamples and boundaries

**Invalid source is durable before activation validation.** Ordinary rewrite happily stores a lens containing `raw-css display:grid`. The next scene build raises LensRefusal. The engine did not preserve an independently active last-good lens definition. The painter source also clears the current paint on refusal. Native undo can recover, but this is not preview/activate with last-good behavior.

**Role references are not checked against installed style.** A lens using `role nonexistent-role` builds a scene successfully. The role is simply carried into the scene; no such definition exists in the frozen `calm.style`. This probe establishes missing reference validation, not a claim about the resulting browser pixels.

**A shared scene tree does not prove projection or gesture equivalence.** Foundations reproduces text cutoff, grammar literal failures and unbounded recursion/instantiation; Media identifies edit trimming, quote substitution, empty-body refusal, missing drop delivery and insufficient gesture semantics. Our successful simple-body command deliberately does not claim that the existing painter delivers arbitrary text unchanged. The text scene lists declared acts; that alone does not prove a browser listener exists, is keyboard accessible, or sends the same literal value.

## Host escapes and impossible requests, counted

Runtime host/application/style source edits: **0**. New runtime code escapes used by these definitions: **0**. Existing interpreter/renderer files changed: **0 of 11 hashed files**. Raw HTML, script or CSS embedded in fixtures: **0**. New style roles: **0**.

Testing apparatus has two extra capabilities: it constructs an isolated Desk in memory and reads its internal data for assertions/hash checks. Those are not capabilities exposed by a lens, and are not counted as normal in-desk authoring affordances. The script is a harness, not a newly installed application or native runtime package.

Seven desired capabilities remain outside this definition-only trial:

1. Define a genuinely new style role through ordinary Desk operations. The current painter fetches a fixed style file; selecting an existing role works, installing a new role object is not provided by this lens path.
2. Activate only a validated lens while retaining a previous working revision on failure. Ordinary rewrite and native undo work; separate activation is missing.
3. Express rich-text ranges and selection-preserving edits. Whole-field replacement is the existing gesture shape.
4. Express raster brush/pixel/compositing behavior or video transport. There are no corresponding scene words or installed component contracts here.
5. Guarantee exact string and empty-string browser editing. The current handler transforms input and substitutes command text.
6. Deliver every advertised gesture with accessibility, capture/cancel semantics and stale intent protection. Parsed declarations are weaker than instrument behavior; drop lacks a handler.
7. Produce a complete bounded text observation with truthful omission and a useful unknown-reference refusal. Current summaries and role lookup do not provide this full contract.

These are requests for general reusable bridge capabilities or versioned component packages, not seven proposed app-specific patches. The future normal operations should be definition create/read/rewrite, explicit preview/activate/recover, inspectable installed capability discovery and typed action invocation. Missing component behavior should be authored and installed visibly through that substrate, not smuggled into a private app callback. The proposed operations are requirements, not already implemented APIs.

## Peer pressure and revised position

Foundations advised using the real comma-space grammar, rather than silently designing a better parser around the fixtures. It owns the adversarial grammar/projection checks. Media forced a distinction between successful command execution and successful browser editing: quote/whitespace/empty text delivery remains a separate failed pressure. I narrowed the role claim to CSS roles after reading the generic div painter, and corrected the command-prefix harness mistake rather than counting it as a success.

Our own-team note is a140/s139 in Experiments. The initial note said thirteen checks; the final count is fourteen after the missing-prefix regression. Correction c146 records the fourteenth check and initial harness mistake. After reading Media a142 and a145, reply c147 adds a live disagreement: a component package contract must leave ordinary hierarchy/interaction changes authorable in definitions; otherwise app-specific glue has merely moved behind installation. Separating definition draft storage from candidate activation is also essential. Root remains the only external liaison. Findings were shared with Foundations, Media and root as they emerged. Existing host source was read-only throughout.

## Reading coverage and frozen source

Read all of current `scene.py`, `desk-shell/lens.js`, `desk-shell/style/style.js`, `desk-shell/style/calm.style`, and `desk-shell/lens.html`; read the `explore.fresh()`/launcher distinction and targeted Desk command definitions. No browser was invoked by this authoring trial. The SHA256 values below were measured immediately before and after execution and matched exactly. They identify this source observation, not a permanent claim about independently changing Claude work.

| Path relative to notation | SHA256 before = after |
|---|---|
| `scene.py` | `4957d5218f539cca2f91b04dfc35f99f80d034a52cae1c8e7a432d9f4c06e68d` |
| `desk-shell/lens.js` | `ed3e88fcd83c8ab7ee93642ac231440c2dab8632c8794276fc182ffc81f4d97f` |
| `desk-shell/lens.html` | `e787658a76a56335130d47e08e471880b3e394d3af20a8dfae7e8778917b3935` |
| `desk-shell/style/style.js` | `b5f68d26b37d423d4fab60bb528591e6e23a071c3b725ecee7ef08b84c83e482` |
| `desk-shell/style/calm.style` | `1e5695ed6f579b1ee93de91e9b3c88b8948f672362812ed6a93a5f886681f4dd` |
| `explore.py` | `a6ea9c503da3030fcd1d2e12c201bb5d9c1a73407679c356a0eac8c90d6d4b66` |
| `desk_knife.py` | `d87af7dedefb95181d3c0703ba424e2da7bf58027f5f51211ad887c7617cc304` |
| `desk_moo.py` | `f8f65e57dcfdea21c9f9b148abeccafbe270c1c946f92a103c707f262a18f8aa` |
| `desk.py` | `cbfb251f68da467949c663034c5b4d7ee122bff8bc43775c89b47ed60b0c3652` |
| `world.py` | `44c01e818655988ee4513796639d55fa66b7598215a7e550d8c4d6e7999b748b` |
| `moo.py` | `351890b883aaf69761a44e72d4cca5ba2bb3ada3d88ff0cc649d9ea1dc98032a` |
