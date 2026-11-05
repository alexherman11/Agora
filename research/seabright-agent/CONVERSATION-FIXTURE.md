# Generic private conversation fixture — dk2770

Pike approved this boundary on 5 November 2026. This increment implements
generic kernel words and a provider-neutral host seam, exercised in hidden
synthetic worlds. It is not connected to the desktop, House or a provider.
Sable owns UI composition; no lens or component was edited.

## Implemented boundary

`kernel/conversations.py` supplies four words:

| Word | Authority and result |
| --- | --- |
| `conversation.open <module> [fresh=yes]` | Direct signed-in member only. Server finds their newest private chat for the enabled module; `fresh=yes` makes an empty chat. No caller-selected person/chat. |
| `conversation.append <chat> text=...` | The owner, or that chat's bound module answering that exact owner under its grant. Saves `said` with visibility inherited from the chat, without addressing anyone. |
| `draft.create <chat> text=... destination=<group>` | Only the bound module answering the owner, intersected with its grant. Creates a reserved `draft` private to the person, with module authorship. No publication. |
| `draft.post <draft> rev=<reviewed revision>` | Direct person only; verifies owner, exact revision and current destination post policy/rate limit. One transaction publishes as the person and records the published id. Repeat does not duplicate. |

The module is the executing agent identity; it is **not** an ordinary
`agent for=<person>` identity. No resident/steward session is borrowed.
Conversation bindings are kernel-reserved facts. Generic make/set cannot
forge a binding or forge/modify a draft. A replacement draft requires a new
review. The managed chat is read-only to ordinary `say`.

Conversation opening, messages and draft creation are passive transactions.
They remain recorded and visible to permitted readers, but their events do
not dispatch to rule automation or module subscribers. This closes the
indirect publication path through an `on=draft.create` rule. Actual Post is
the person's ordinary non-passive post event. No diagnostics were changed.

`help draft` now discovers the whole word namespace even before any drafts
exist. The general help mechanism still gives authored topics and module
help precedence over this fallback.

## Runner and model interface

`kernel/conversation_runner.py` defines `ConversationRunner`, `ModelFactory`,
`ModelSession`, `ModelReply`, `ToolCall` and the scripted `FakeModel`.

The trusted host injects an authenticated **person Actor** and a configured
module id. The public methods are `entry(caller)`, `enter(caller, fresh=False)`
and `respond(caller, text)`. The model never supplies caller or chat routing.
One runner is owned by one kernel. Its session dictionary is keyed by
`(agent-module, person, chat)`; each new key calls `model.open()`. New chats
start with only the new user's message. Restarting the runner rebuilds
context from the current person's visible world messages.

The model gets copied message/tool-result data, explicitly marked untrusted.
It returns text and typed tool proposals. Neither text nor results are
evaluated as Lines. There is no model callback capable of supplying an
Actor or invoking arbitrary code/Lines.

The closed tool vocabulary is:

| Tool | Exact arguments | Kernel capability |
| --- | --- | --- |
| `look` | `id` | Caller-visible object/map facts; no rendering execution. |
| `search` | `query` | World search, permission-projected results and source ids. |
| `help` | `topic` | Discoverable kernel/world help. |
| `draft` | `text`, `destination` | Private draft creation in the server-bound chat. |

The runner reads history with `chat` itself. Every reading uses `module_see`
and every write uses a module Actor with the authenticated person as caller,
so the kernel intersects current caller rights and module grants. The broker
also enforces `only=` restrictions for targeted readings. Aggregate readings
with only constrained grants fail closed: their prose cannot safely be
post-filtered. A broad module grant still cannot add a tool to this vocabulary.
Canonical kernel bindings are checked so shadowed words cannot become
arbitrary module/verb execution. Grants are rechecked at dispatch; disabling
the module prevents reuse of an existing model session.

Safe fixture grants:
`look search help chat conversation.append draft.create`.
Optional narrower grants on writes can use `only=kind:said` and
`only=kind:draft`. No `post`, `say`, `notify`, `grant`, `do`, web, ordinary
agent tools or ambient module operation are exposed.

## Sable's data contract

See [conversation-entry.contract.json](conversation-entry.contract.json).
`runner.entry(authenticated_person)` returns the concrete entry data:
label from the visible module, a `conversation.open` action targeting that
module, `scope: signed-in-person`, and the fresh-chat option. All members
receive the same entry shape. The server resolves different private chats.
The JSON uses symbolic bindings, not live world ids.

After resolution the person may read the returned chat through the existing
permission-checked chat reader. A model response returns text, its saved
message id, the server-resolved chat and typed tool receipts. Object/map
references are projected world ids; use existing permission-checked readers
for presentation. Treat text and tool results as inert content, never as
button definitions, HTML or automatic navigation/execution.

For a draft, the authenticated UI reads the draft, shows exact text and
destination, and presents **Post** with `draft.post <id> rev=<shown rev>`.
Only an explicit gesture sends that line as the signed-in person. Do not
auto-run it from model prose or generate a confirmation on the model's behalf.
The model has no Post action. No shared draft button holding another member's
id should be written into the world.

Host wiring and layout remain unactivated. This increment supplies the
kernel word and callable host seam; it does not add an HTTP endpoint or
intercept existing House chats.

## Evidence and deliberate limits

**Ran:** the fixture suite tests alternating people, fresh chats, distinct
agents, runner restart, guessed private object/chat/said ids, direct history
ACLs, inherited/ambient identities, immutable bindings, tool schemas,
injected posts/results/prose, broad and revoked grants, constrained reads,
module shutdown, draft privacy, exact confirmation, idempotency, wrappers,
rules, event subscribers, destination permissions and post rate limits.
Grounded map/search/help/draft journeys use fake model replies only.
Exact commands and results are in `BUILD-RESULT.md`.

**Read, not fixed:** existing `house.log`, activity and live summaries can
expose private chat information through their diagnostic readers. Passive
events do not repair those readers or remove stored records. Do not describe
this increment as a complete operational privacy guarantee.

**Not implemented/tested:** live activation, member UI, provider inference,
web/egress, provider auth, streaming/cancellation, persistent provider session
recovery, cross-process concurrent runners, retention/deletion or operator
privacy. This fixture serializes turns with a runner lock, loads at most
the existing chat reader's 200 messages, and holds session objects in memory.
Production must own one runner per configured module/kernel or supply shared
serialization; a separate-process worker lifecycle is future work.
Draft destinations currently use the existing group/place post surface.
Application-specific channel post fields need a reviewed world mapping,
not hardcoded Seabright behavior. No draft editing UI is supplied.

## Provider extension and decisions still outstanding

Implement a reviewed `ModelFactory` adapter only after an authorised route is
established. Opening must create an isolated session, never reuse a resident's
shared session. The adapter must preserve typed data/tool boundaries and use
only the host-selected model/route. Auth material must stay outside world
facts, chat and model context; never add token collection to this interface.
Before real inference, add cancellation/usage limits, explicit context-egress
policy and per-person route binding. Fail closed when access is unavailable;
no subscription/API entitlement or billing fallback is implied.

The earlier [inspection](INSPECTION.md) records provider documentation findings.
They are not evidence of access for this agent. No Sonnet/real inference was
attempted this round; the authorised Sonnet route remains unestablished.
JEFF/Alex still own provider/billing, operator access, retention and web-egress
choices. Sable owns UI composition; Pike/House own review and landing.
