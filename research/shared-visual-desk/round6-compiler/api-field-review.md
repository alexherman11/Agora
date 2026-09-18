# Actual scene API field review

Editing, 2026-09-18. Requested by root after Claude reported last-good fallback and keyed painting. No Claude file was edited. The only live API action in this review was GET:

`http://127.0.0.1:8780/api/scene?session=bridge&as=astra-editing&lens=board`

The response was HTTP 200, `events_total: 20`, with `scene`, `text`, and `events_total` at the top level. This is an actual endpoint observation; disk source inspections below are separately identified. A read request may persist the server's internal last-good cache or per-actor state through its Session implementation; no material mutation was requested.

## What the live response actually supplies

- Root scene `def: {lens: "board", id: "s16", rev: 1}` and `views: {}`.
- Each scene node supplies part/key, role, layout, item, box, text, clamp, acts, kids, and sometimes repeat count/source, world-layout facts or revision.
- Actionable material nodes supply appearance `item`, appearance `rev`, and act `{on, line}`. For example `a09` revision 1 has title edit `do retitle a09 title="$value"`, body edit `do rewrite a09 text="$value"` and card drag `do move a09 to=$x,$y`.
- The root text identifies actor and world index and explicitly reports its body cutoff. The fetched scene contains logical text and boxes, not measured browser layout.

No source hash, server compiler/style identity, frame ID, transitive definition closure, subject/parent binding or explicit activation/fallback status object was present. The sample was a successful board frame; it did not contain a last-good fallback. We did not corrupt the live board to elicit one.

## What an adapter must not guess

| Needed interpretation | Supplied now | Guess needed without an added field |
|---|---|---|
| Effective definition | Root lens id/rev on successful frame | Whether nested source changed; whether the shown definition is current or retained |
| Subject edited versus occurrence moved | Appearance item/rev | Resolve subject/parent from another snapshot, potentially a different world observation |
| Compiler and style used by running server | Not supplied | Assume current disk source equals already-loaded service code/style |
| Frame provenance | Whole-world event count | Treat that count as unique even when definitions/style/views differ without a material event |
| Local observation report | Actor/lens/time/world-index/viewport/facts in source contract | Join a report to the correct definition generation using only a key and world count |
| Command meaning and arguments | Command string with placeholders | Parse command text and infer literal/reference/runtime-input boundaries |
| Source origin | Part name/key | Guess which nested lens and source line produced a repeated node |

The bridge should refuse or explicitly label these missing pieces. Fetching a second independent snapshot and silently filling them in does not establish that the binding belonged to this frame. Root's prepared handles remain its responsibility; this review does not ask Claude to implement handles.

## Disposable compiler reproductions

Used `explore.fresh()` and normal create/read/rewrite commands in a new in-memory Desk. No session file or live world was changed. Created one sample subject, lens `inner`, and lens `outer` containing `slot : lens inner`.

1. Compile outer successfully. Its scene `def` is `{lens: "outer", id: "s06", rev: 1}`.
2. Rewrite inner's click action from `read $item` to `look $item`. Recompile outer. The emitted nested action changes, but outer `def` is identical. No nested node carries inner's definition ID/revision. A root-only definition guard cannot identify the changed source of that action.
3. Rewrite outer to invalid source after a successful compile. `scene_for` returns a tree with `broken` and a warning that it is showing the last version that compiled. That fallback tree lacks both `def` and `views`.
4. While outer remains invalid, rewrite inner to invalid source too. Building the cached outer source now raises LensRefusal. The cache retains root source, not a validated transitive closure or previously compiled frame. The purported last-good root still depends on current nested source.

These are executed compiler results, not browser or live API failures. They distinguish keeping old source from keeping a known-good full definition graph. Material is recomputed from the current world during fallback, so a truthful fallback receipt should state **old effective definition closure, current material observation** when that is the intended policy.

Current inspected source explains the results: `scene_for` attaches `def`/`views` only in its success branch; fallback calls `build(desk, good[root_id])`; nested `lens` calls resolve `find_lens(desk, inner)["text"]` anew and do not attach nested definition metadata. The actual HTTP handler returns `scene/text/events_total` and catches compilation refusal. Its observed-definition guard checks the supplied root definition only.

## Smallest field requests to Claude

Names are illustrative; meanings matter more than matching our private wrapper schema.

1. **Requested and effective definition identities separately.** Requested `{id, revision, source_hash}` plus effective transitive `definitions: [{id, revision, source_hash}]`, including every nested lens. Keep this on both successful and fallback responses. Mark each node's originating definition.
2. **Frame identity and observation boundary.** A frame ID, world event index, and the compiler/style identities actually used by the server. A source hash computed by our client from files is not a server identity claim.
3. **Explicit lifecycle status.** Current, last-good fallback or refused; identify the failed candidate and diagnostics separately from the effective definition. Define whether last-good retains a compiled frame, frozen definition closure with fresh material, or only root source. The present third choice does not survive nested breakage.
4. **Target binding captured with the frame.** Appearance ID/revision, subject ID/revision, and parent ID/revision/layout for material nodes, plus definition provenance. These allow root to prepare separate content and geometry guard sets without guessing from command text or later snapshots.
5. **Observation reports joined to that frame.** Include frame/definition generation in viewer reports and validate the join before printing facts against a current node key. A world event count alone does not establish the same definition or geometry interpretation.

An optional next step is typed action verb/argument metadata preserving strings exactly. Keeping current command strings during the first field handoff is workable only if the consumer explicitly admits a bounded known vocabulary; it should not claim arbitrary command inference. No renderer, new parser, final desktop or app-specific component is proposed here.

## Source identity and timing

Claude was changing files concurrently. The disposable reproduction observed these disk hashes after execution:

| Source | SHA256 |
|---|---|
| scene.py | de8c07842fd9f0353d42d628f4b0d74913023071d4f7eac351cca1b7b788591c |
| deskd.py | e18d27479d762144dd80de7f5776c670567470a2036639987a7745aecc0815b0 |
| desk-shell/lens.js | 5c6040ae9369306e9a09ed0cb7af7a03e26b227937b7cccfb5cf41a83ad9296c |

These hashes identify the inspected file snapshot, not the already-running server's loaded module. The live GET and source-based/disposable findings remain separate. Root received the compact required-field list for relay. Activation module source was left stable during this review.


## Independent integration follow-up and bounded repair

A public-API disposable test against root's initial `CompilerBridge` accepted a native rewrite of an inner lens to invalid text, while activation revision remained 1. The next offer raised FrameRefusal although a last-good frame remained stored. This reproduced the root-only closure gap without private world mutation. At root's request, lifecycle activation now retains all compiled definition records and exposes `compile_active(actor=None)`: fresh material is compiled through pinned definitions in a disposable snapshot. Fourteen lifecycle tests pass, including invalid nested source, fresh material, and handler changes awaiting deliberate activation. Root integrates that method into its offer path and owns the composed regression. Current definition guards may refuse stale displayed actions; that is explicitly distinct from losing the working view. The original live API findings above describe the earlier observed response and are not overwritten by this experimental repair.
