# Rule evaluator contract v1 (round-three prototype)

`program.mjs` is a standalone browser/Node module. It evaluates JSON data, without `eval`, generated functions, imports supplied by the program, timers, network or DOM effects. It is not Agora's authenticated gateway or a hardened security sandbox for arbitrary JavaScript callers.

The designed document is `{state, program}`. State is ordinary bounded JSON, for example:

```json
{"content":{"title":"Field notes"},"appearance":{"bloom":0,"caption":"Dormant"},"controls":{"light":0.6},"items":[{"id":"seed","role":"signal","value":4,"style":{"size":10,"fill":"#cccccc"}}]}
```

A program has `version: 1` and at most 32 rules. A rule has a unique `id`, optional event name `on`, optional boolean expression `when`, and `steps`. An absent `on` matches every event. The default preview event is `run`.

```json
{
  "version": 1,
  "rules": [
    {
      "id": "light-response",
      "on": "change",
      "steps": [
        {"op":"let","name":"amount","value":["clamp",["add",0.15,["mul",["get","controls.light"],0.85]],0,1]},
        {"op":"set","path":"appearance.bloom","value":["var","amount"]},
        {"op":"set","path":"appearance.caption","value":["if",["gt",["get","controls.light"],0.55],"In the light","At rest"]}
      ]
    },
    {
      "id": "semantic-shapes",
      "on": "change",
      "steps": [
        {"op":"forEach","collection":"items","as":"item","where":["eq",["var","item.role"],"signal"],"steps":[
          {"op":"set","target":"item","path":"style.size","value":["mul",["var","item.value"],3]}
        ]}
      ]
    }
  ]
}
```

## Expressions and steps

Scalars are literal expressions. Arrays are operator calls. Use `["lit", VALUE]` for an array/object literal. Objects are not implicit expressions.

- `["get", "state.path"]` reads input state. `["var", "name"]` or `["var", "item.value"]` reads a local.
- Numeric operators: `add`, `sub`, `mul`, `div`, `min`, `max`, `clamp(value,min,max)`, `round`, `abs`. Arithmetic rejects nonnumeric, nonfinite and division-by-zero values.
- Comparison: `eq`, `ne` compare JSON values; `gt`, `gte`, `lt`, `lte` require numbers.
- Boolean: `and`, `or`, `not`; conditionals require actual booleans, not truthiness.
- `["if", TEST, YES, NO]` and boolean operators short-circuit at runtime. All branches still undergo syntax validation.
- `concat` joins scalar expressions, with a bounded result length.

Steps are `let`, `set`, `if`, and `forEach`. `if` contains `test`, `then` and optional `else` arrays. `forEach` reads an existing root collection path, binds its element to `as`, optionally filters with `where`, and evaluates `steps` for each selected element. `set` optionally names an iteration `target`; its path then resolves within that element. Missing paths refuse rather than silently creating typo properties.

Local lets are sequential within their block. Branches and iterations have nested local scopes. State writes are **proposals**, not imperative updates visible to later steps. All rules and expressions read the same input state. Equal writes coalesce with contributor provenance; unequal writes to one address refuse the entire proposal. Parent/child overlapping writes also refuse. There is no implicit last-rule-wins policy.

## Module API

```js
import {preview, apply, undo, limits} from './program.mjs';
const proposal = preview(document.program, document.state, {event: 'change'});
if (proposal.ok) {
  const result = apply(document.state, proposal);
  // If result.ok: use result.state and retain result.receipt for undo.
}
```

`preview` returns `{ok,changes,errors,diagnostics,stats}`. `changes` entries are `{path,before,after,ruleIds,origins}`. Errors are printable strings; diagnostics additionally carry `{code,message,path,ruleId?}`. Failed previews return no changes, preserving the input. Successful previews do not mutate input either.

`apply(state, proposal)` returns `{ok,state,receipt,errors,diagnostics}`. `undo(state, receipt)` returns `{ok,state,errors,diagnostics}`. Failures retain the supplied state. Proposal and receipt objects are ephemeral, single-use handles: do not serialize or clone them. The module privately retains the admitted changes, so mutating a public preview's rows cannot alter the writes. Document state/program remains portable JSON.

A conservative whole-state value fingerprint guards apply and undo. Any intervening unequal state causes refusal. This overblocks unrelated changes; it is **not** a revision history and does **not** detect ABA sequences returning to the same values. Undo has no selective compensation or redo contract. These choices support one isolated authoring demo, not general collaboration.

## Bounds and domain responsibility

Maximums: 8,192 evaluated operations, 256 proposed writes, 512 loop iterations, JSON nesting depth 24, 20,000 JSON nodes per input validation, string length 16,384, and 32 rules. Per-preview operation/write/iteration budgets can only lower these hard limits. Errors identify where evaluation stopped. There is no recursion, unrestricted looping or user code execution.

The caller chooses event delivery and whether/when to apply. This is not a persistent dependency scheduler, constraint solver, physics/media runtime, or automatic rollback of external effects. Domain code must validate renderable state, bind real controls, manage live drafts/focus, authorize and persist changes, and test actual interaction. General JSON validation does not establish that an arbitrary color, layout, or whole-object replacement is valid for a particular renderer.
