# Tessera 0.1: a language of contributed relations

Experimental, standalone, not an Agora implementation. A program is the unordered
union of authored JSON modules. No module contains JavaScript, HTML, CSS source,
callbacks, imports, or execution-order instructions. JSON is the initial syntax,
not the semantic model. All addresses survive module/file ordering.

## Module format

`{"id":"notes", "claims":[ ... ]}`. Every claim has `kind` and `id`.
Kinds: `field`, `seed`, `query`, `derive`, `action`, `reaction`, `view`, `style`, `constraint`, `gesture`, `pulse`.
The id names a semantic address within its kind. Multiple authors may contribute
different properties at the same address. Identical values coalesce; incompatible
values are reported with both authors and block that address. No last-file-wins.
Each property is an indivisible claim (arrays are values, not positional patches).
To extend behavior, contribute a reaction; to extend a view, contribute a child.

References to absent named derivations, queries, or command targets make a
contribution **dormant**, with the missing address and the full original claim
retained. This propagates through dependent contributions. Other independent
reactions can still participate. Restoring the missing definition reactivates the
same contributions; no feature-source rewrite is involved. This is conservative
static closure, including references inside a branch that may not currently run.
Mandatory constraints are never dropped: an unresolved constraint rejects program
admission. Dormancy is for incomplete capabilities, not a way to bypass invariants.
Recursive expression definitions remain unsupported and fail on evaluation.

### State

`{"kind":"field","id":"items.title","type":"string","default":"","merge":"register"}`

Field id = collection.field. Types: string, number, boolean, array, object.
Merge = register (default), counter (only numeric add), set (array union).
Defaults fill all records, including records seeded by other modules.

`{"kind":"seed","id":"items/welcome","values":{"title":"Welcome","body":"Hello"}}`

Seed values merge per field. Conflicting seed values are diagnostics. Existing
runtime data is never overwritten by seeds during live program reload.

### Expressions (pure data)

Scalars are literals. Objects evaluate recursively. Arrays are operator calls;
use `["lit",[1,2]]` for literal arrays. No string evaluation.

* `["arg","title"]`, `["row","title"]`, `["local","draft"]`
* `["parent","id"]` (outer list row, for nested collections)
* `["get", expression, "field"]`
* `["record","items", idExpression]` returns a record including its id
* `["all","items"]`, `["query","notes.visible"]`
* `["eq",a,b]`, `ne`, `gt`, `gte`, `lt`, `lte`, `and`, `or`, `not`
* `["if",condition,then,else]`, `["coalesce",a,b,...]`
* `["concat",a,b,...]`, `["lower",x]`, `["includes",haystack,needle]`, `["trim",x]`
* `["startsWith",string,prefix]`, `["number",x]`, `["round",x]`, `["min",a,b]`, `["max",a,b]`
* `["floor",x]`, `["mod",a,b]`; lt/gte also compare strings lexicographically
* `["abs",x]`, `["sqrt",x]`, `["sin",x]`, `["cos",x]`, `["pow",x,y]`
* `["add",a,b,...]`, `["sub",a,b]`, `["mul",a,b]`, `["div",a,b]`
* `["count",array]`, `["sum",array,"field"]`; omit field to sum numeric array
* `["filter",array,predicateUsingRow]`, `["map",array,expressionUsingRow]`
* `["unique",array]`, `["join",array,separator]`

`{"kind":"query","id":"notes.visible","from":"items","where":["not",["row","archived"]],"sort":"title"}`

Query where runs with row, args, and local context. `sort` is optional field name.
Queries are derived afresh. Cyclic query calls fail with an explicit diagnostic.

Named expressions avoid copying logic between views, constraints, and reactions:
`{"kind":"derive","id":"mission.cost","value":EXPRESSION}`.
Use `["use","mission.cost",{"id":EXPRESSION}]`; the supplied object becomes arg
inside the derivation. Pure, acyclic, no effects or source strings. The caller's
row/parent/local remain available, but explicit args are preferred for reuse.

### Actions and shared behavior

`{"kind":"action","id":"item.rename","requires":["ne",["trim",["arg","title"]],""],"effects":[{"op":"set","collection":"items","id":["arg","id"],"field":"title","value":["arg","title"]}]}`

`{"kind":"reaction","id":"tasks.onRename","on":"item.rename","when":true,"effects":[...]}`

Every matching reaction evaluates against the SAME pre-action snapshot. Its
effects join the action's effects. Reactions do not call actions or each other.
Set + same set coalesce; set + unequal set conflict and the WHOLE action fails;
add + add sum; union + union combine. Mixed operators at an address conflict.
No phase order and no implicit handler winner. The concrete addresses of effects
are the write footprint. All expressions read the same immutable snapshot.

Effects:
* set: collection, id expression, field, value expression (record must exist)
* add: same, numeric value (field must be counter)
* union: same, array value (field must be set)
* create: collection, id expression, values object of expressions
* delete: collection, id expression
* foreach: `{"op":"foreach","in":arrayExpression,"effects":[...]}` expands
  effects with each array member as row, retaining arg and outer row as parent.
  Every expansion still evaluates on the one pre-action snapshot and joins the
  same atomic candidate. Maximum 1000 expanded effects, nesting maximum 8.

Create can compose disjoint fields of the same new record. Delete versus another
effect on that record conflicts. Action ids come from a supplied arg or a literal;
UI buttons may supply `["local","newId"]` (shell prepares unique ids per click).

`{"kind":"constraint","id":"budget.nonnegative","check":["gte",["get",["record","budgets","main"],"remaining"],0],"message":"Insufficient budget"}`

Constraints run on the complete candidate state before commit. Actions are atomic.
In constraints, `["before",EXPRESSION]` evaluates against the pre-action state;
normal expressions see the candidate. This enables transition invariants at the
data boundary, protecting against newly added commands bypassing old guards.
Example: quantify over old reservations, compare their immutable fields with
current records. A missing current record is a failed equality, so deletion is
also refused. New-program admission evaluates constraints with before=current.
This prototype uses a single local authority, not distributed transactions.
Calls can include `expected` cell revisions for register writes. A stale write
records both proposals as a conflict and commits nothing; unrelated cells proceed.

### Views: open, stable addresses rather than nested source trees

`{"kind":"view","id":"notes.panel","parent":"workspace","widget":"panel","title":"Notes","order":10}`

All views are independently addressable. `parent` refers to another view id.
Children sort by numeric order then id (no file-order dependency). Unresolved
parents remain dormant and diagnosed. Cycles are diagnosed and not rendered.
Widgets: panel, stack, row, text, badge, input, textarea, select, button, list, link.
Properties: title, text (expression), role (string), visible (expression).
Input/textarea: `bind` local-state key, `value` fallback expression, `placeholder`.
Input accepts `inputType:"number"` to produce numeric local values. Select uses
`bind`, `options` expression returning records with id, `optionLabel` field
(default title), optional `value` expression; its local value is the selected id.
Button: `text`, `action` id, `args` expression object, optional `disabled` expression.
Link: `text`, `href` expression; only https/http allowed, opens a separate tab.
List: `query` query id; all child views repeat for each row, with row context.
Nested lists are allowed. Child additions to a list extend EVERY row naturally.
Local state is scoped to a view occurrence (row id + bind), with top-level input
values inherited by row descendants. Buttons resolve local fields in their scope.
All text is rendered as text, never HTML. No arbitrary markup or script hooks.

### Styles

`{"kind":"style","id":"notes.cards","selector":"role:card","priority":10,"values":{"background":"#fff","color":"#123","borderRadius":"16px"}}`

Selector = `role:...`, `id:...`, or `widget:...` (not arbitrary CSS).
Values are an allowlisted set of CSS properties; priority resolves overlap. Equal
priority unequal claims produce diagnostics and omit that property. Provenance
retains winning and losing claims. A missing match is inert. No behaviors in style.

## Trial 1 shared contract (the scaffold, frozen before builders)

Workspace root id `workspace`, widget stack. Collection `items`; known fields
`title` string, `body` string, `archived` boolean false. Initial record
`items/welcome`: title `A shared research note`, body `Three builders, one workspace.`
Shared command `item.rename` above is supplied by the scaffold. Agents may add
fields and reactions, and contribute children to each other's advertised addresses.

Notes builder provides `notes.list` with row `items`, `notes.card` child panel with
role `item-card`, and `notes.card.tools` child row. Other agents can target these
before they exist. Agents own features, not isolated parts of the screen.

Builders write only their own `*.tessera.json` and optional `*.cases.json` in the
trial directory. They may read LANGUAGE.md, TRIALS.md and scaffold. They must not
read other builders' modules until initial submissions are frozen; may communicate
interface questions directly, preserving messages. Coordinator never patches
their contributions. Runtime changes must be general language repairs, recorded.

Cases: `{"steps":[{"action":"...","args":{...}}],"assert":[{"expr":EXPRESSION,"equals":VALUE}]}`.
Put multiple cases in a JSON array. Cases run from fresh state independently.
Steps may include `ok:false` to expect refusal.
