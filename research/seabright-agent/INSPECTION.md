# Seabright resident AI: inspection and proposed boundary

**Follow-up status:** this is the original inspection snapshot. Pike subsequently
approved the hidden-fixture boundary. Implementation and executed evidence now
live in [CONVERSATION-FIXTURE.md](CONVERSATION-FIXTURE.md) and `BUILD-RESULT.md`.
The unimplemented gates below describe the inspection's status, not the
follow-up's results. Provider/diagnostic/activation gaps remain explicit.

Builder report for Pike and JEFF, 5 November 2026. Task dk2770.

This turn follows Pike's live `next_action`: read-only inspection, this document,
no source edits, no credentials and no provider calls. **Read** means inspected
source, live metadata/help, or the linked official documentation. **Imagined**
means proposed behavior, not implemented. **Ran** is reserved for actual checks.
No model inference, privacy test, browser fixture or activation ran.

## Recommendation

**Read:** existing persons, closed chats, visibility projections, module grants,
board readings and map words are useful foundations. They do **not** collectively
provide a safe multi-person resident today. House keeps one model conversation
per resident, and its ordinary agent session is not narrowed to each asker.
Do not install a shared resident and describe its chats as isolated.

**Imagined:** retain one world resident identity, but add a general
conversation-scoped runner and tool broker: separate context per
`(world, resident, authenticated person, chat)`, current caller-visible data,
explicitly scoped tools, and author-confirmed publication. Use existing module
admission instead of giving the model a person's unrestricted door session.
Keep providers behind that boundary. Sable owns every board lens/component edit.

**Read:** Claude transport accepts the configured model, so Sonnet is not
structurally excluded. Existing authorised Sonnet availability for this new
identity is **unverified**, not a demonstrated route. No new signer was made,
no session store was opened, and no provider was invoked. General web search
also has no installed provider. These remain explicit acceptance blockers.

## 1. How House runs residents

Paths below are repository-relative and name the exact inspected functions.

| Source | Current behavior |
| --- | --- |
| `research/kernel-lab/modules/house/house.py::House.load` | Reads `house-agent` world things; indexes `self.agents` by person. Two configurations for the same person are not separate conversations. |
| `house.py::Agent.__init__`, `start`, `provider` | One child, inbox, turn and persisted state under the resident name. Provider is `claude` or `codex`; model/reasoning come from configuration. Resume uses one `state["session"]`, conditional on provider. Configured quota fallback can switch providers. |
| `house.py::House.system_text`, `charter_text`, `welcome` | Reads prompt and charter things; welcome includes soul and optional guide. Prompt changes restart the child while retaining its conversation. These are shared resident material, not per-member private memory. |
| `house.py::House.happen`, `_catch_up`, `line_for`, `sees_line` | Addresses and closed-chat recipient lists wake residents. Catch-up uses durable cursors; `line_for` rechecks visibility through the resident's own door. Task/explicit wakes also exist; `wake_policy=addressed` narrows automatic wakes. |
| `house.py::Agent._begin`, `_spoke`, `_receipts` | Batches queued input by chat and replies into that chat. This prevents mixing chats in one turn, but the same child/session survives the next chat. Receipts attach to spoken lines. |
| `research/kernel-lab/modules/house/transport.py::claude_cmd` | Runs unmodified Claude CLI in stream-json mode with configurable `--model`, optional resume, no built-in tools, strict MCP configuration and only Agora `see/do/lines`. |
| `transport.py::codex_cmd`; `research/codex-residents/codex_resident.py::require_subscription`, `build_config` | Uses the pinned Codex adapter. Subscription metadata is checked without token refresh; custom OpenAI routing is refused. Shell/files/web built-ins are disabled in the resident configuration. |
| `house.py::House.token_for`, `Agent.start`; `transport.py::mcp_config` | Existing runtime resolves an already-issued signer session and gives it to its MCP adapter. Inspection read this code only, **not** the credential files it names. A new world person alone does not supply a signer session. |

**Read, live:** `house.who` showed Sable and Pike on the Claude route, configured
with `claude-opus-5-5`, and JEFF/Rowan on Codex. That proves reported existing
configuration, not Sonnet entitlement, billing mode or authorization for members.
`Agent.start` would refuse a missing signer session. Do not borrow a steward's,
Pike's or another member's signer to get past that refusal.

**Read:** `transport.clean_env` removes launcher Claude variables and the live
keeper reference, but is not a proof of subscription-only billing: other provider
environment settings can remain. No environment values were inspected. A future
bounded Sonnet trial needs an authorised owner to attest the effective route,
model, existing signer and no-new-spending boundary without exposing credentials.
Do not enable automatic paid fallback or use a model-name substitution as proof.

## 2. Closed chats and the privacy gap

**Read:** `research/kernel-lab/kernel/chat.py::closed_sees` turns
`make kind=chat with="..."` into explicit person visibility and includes the
maker. `say` admits only listed people in a closed chat, creates `said` with
`visibility_of=<chat>`, refuses cross-chat `reply_to`, and excludes inaccessible
recipients from wake addresses. `lines_of`/`chat` project each line for the reader.
`kernel/kernel.py::Kernel.shown` checks object, parent-chain, predicate and
field visibility; broken/cyclic parent chains fail closed.

One resident person can belong to multiple two-person chats. At the world-object
layer, each member can read their own chat and the resident can read all its
chats. A steward does not get an unconditional read bypass in `shown`.
Creating every chat as a third-party coordinator would add that coordinator
through `closed_sees`; create under the member's authenticated call instead.

**Read:** this does not isolate model memory. `Agent._begin` separates turns,
not session histories, summaries, fallback continuations or retrieved data.
The resident's own session can retrieve every chat it belongs to. A prompt
telling it to forget other people is not permission enforcement.

**Read, audit finding, not an exercised exploit:** `House.call` for resident
`house.log` calls `log_of` without caller `use`; `log_of` reads `rows said`
through House's own view and selects lines addressed to/by that resident.
`house.activity` likewise returns resident activity; `row`/`publish` expose
last tool summaries and errors. The result depends on installed module rights,
but these are not suitable as private multi-person diagnostics without review.
Do not probe live private histories to demonstrate it. Test with synthetic
sentinels and audit House logs, activity, live projections, errors and event
streams before promising privacy. OS operator access/backups are a separate
retention/trust question, not something chat ACLs can eliminate.

## 3. Acting principal and server enforcement

**Read:** `kernel/door.py::make_handler`'s `_actor` validates the door session, obtains
the account's person, then calls `Kernel.actor_for`. It does not trust a model's
claimed person. `actor_for(pid, agent)` makes an agent identity associated with
`for=pid`; `Kernel.may` delegates ordinary agents to `_may_person(actor.person)`.
Thus “agent for Alex” has Alex's rights, including stewardship where applicable.
An extra grant row addressed to that agent is not an attenuator.

The existing stronger mechanism is a **module answering a caller**:

- `Kernel.module_see` uses `Actor(module, caller.person, "module", caller=caller)`.
- `Kernel.may` requires both the caller's right and the module's live grant.
- `Kernel._granted` rechecks grantor authority/location.
- `Kernel.admit`/`_admit_lines` validate declarative kernel writes as that caller
  narrowed to the module; `fence` and participant checks reject stale writes.
- `Kernel.reaches` adds kind/thing/field/library constraints for module writes.
- `kernel/modules.py::ModuleProcess.ask`, `handle`, `_see` bind a call's `use` to its
  caller; unknown/closed uses cannot claim a previous caller's read context.

This is the right base, but not a ready asynchronous resident interface.
`reaches` is not a universal row filter for arbitrary read words. A grant to
`rows` plus caller visibility can reach unrelated caller-visible objects.
The Documents-specific context in `module_see` illustrates additional scoped
projection; it is not a generic conversation scope. Nested module dispatch
and long-lived accepted calls need tests that preserve the outer attenuation.
`_admit_lines` accepts kernel acts, not arbitrary module-to-module command chains.

**Imagined:** a reviewed broker should bind the authenticated requester and
chat server-side, allow typed operations within a declared capability scope,
and preserve that scope on every nested call, tool result and final write.
Expose neither unrestricted `do` nor an ambient door token to the model.
Revalidate membership/grants before retrieval, remote disclosure, reply and
publication. Stop a queued turn on revocation; do not replay stale context.

## 4. Existing tools and what is missing

| Journey | Read: available base | Remaining boundary |
| --- | --- | --- |
| Find/explain Seabright | `help`, `rows`, `look`, `find`; `kernel/words.py::search` searches projected name/title/text and returns visible labels/snippets. | Ground explanations in actual results; lexical search is not semantic discovery. |
| Read board content | `research/community-app/board/board.py::call`, `rows`, `visible_posts`; `board.feed`, `board.search`, `board.events`, `board.catch-up`. Calls use caller-bound `use`. | Restrict to approved Seabright scope and recheck source permissions; no shared retrieval cache. |
| Bring an object into chat | `said.about` can reference a visible object; ordinary world links can name it. | Render from current caller projection; model text cannot choose an unverified target or preserve revoked facts in a cached card. Copying text is a disclosure, not only a link. |
| Show map/place | `modules/map/map.py::w_find`, `w_where`, `w_near`, `w_place`, `w_show`; live Seabright map dk864. | Some “see” words do network I/O. `w_find`/`geocode` can send a query to Nominatim; tiles/buildings also fetch externally. Use local/synthetic data first. |
| Draft a channel message | Board composer has local `api.draft` state; private `make kind=post sees=me` is compatible. `conversation-draft` exists for the current desktop chat. | No inspected durable draft-and-confirm contract binds exact author, destination and revision. Never interpret arbitrary model output as `board.post`. |
| Ask local model | `modules/model/model.py::context`, `plan`, `generate`, `local`; fixed loopback service at port 11434, projected facts, bounded generation and untrusted-data prompt. | Not Sonnet and not a multi-turn tool agent. `model.search` advertises a held prototype; suitability requires evidence. |
| Search the web | No general web provider in live `rows module`, world help or inspected resident tool configuration. dk2675 also records the gap. | A reviewed web provider/egress capability is needed; this coding worker's web tool is not available to the Seabright resident. |

**Read, live:** `model.status` returned “local model is up; selected qwen3.5:9b;
loaded: none.” This was a status reading only, not an inference or quality test.
`help map` resolves to the generic XY component; use `help map.find` and the
other geographic words for geographic capabilities. This ambiguity belongs in
the resident help journey.

**Read:** `Kernel.outside_marks` labels module-readable data as public/yours/no
and identifies narrower fields. Here “public” means visible throughout the
place, not necessarily public on the internet. Its own comment explicitly says
it is an honest-module policy aid, not process/network containment. Remote
model and web requests need an explicit enforced egress gate.

## 5. Channel entry and Sable's ownership

**Read:** live `rows board-channel` showed six channels, no resident channel.
`Meetings & events` has `opens=calendar`; `Research & documents` has
`opens=documents`. In `board-components.js`, `chooseChannel` reads world channel
data and selects `view.channel`/`view.opens`; `board.lens` arranges the panels.
An `opens` value alone does not implement private-chat lookup or rendering.
The existing desktop `jeff_chat.py::install` and `jeff-chat.lens` target one
Conversation with fixed participants and should not be reused unchanged.

**Read:** Shop talk dk2785/dk2788 records the agreed split: Sable owns all UI,
Pike supplies the entry contract, and Sable will provide stable map/reminder
names. No UI files changed here.

**Imagined entry contract for review:** world-authored channel title,
`opens` panel name, resident reference and help reference; the panel invokes a
general `conversation.open <resident>` capability on an explicit click.
The server derives the member from authentication, checks membership, then
atomically finds/creates the one closed chat for that pair. Return the private
chat handle, visible resident name, provider readiness and allowed actions.
No caller-selected person, arbitrary `with` list or public member-chat index.
Two simultaneous opens must yield the same chat. Do not wire this proposed word
as if it already exists.

## 6. Minimal architecture and staged implementation

**Imagined; review proposal, not installed:**

1. A world-authored resident/service definition holds identity, prompt/help,
   provider reference, enabled state and capability policy. No Seabright name,
   prompt, model or member IDs are source constants.
2. A generic private conversation resolver builds on `chat`, `with`,
   `visibility_of` and authenticated callers. Private state follows the chat's
   visibility. Do not make a public index that reveals who uses the assistant.
3. A conversation-scoped runner keys session, queue, cursor, summary, provider
   state, caches and diagnostics by member/chat. Begin with fresh bounded
   context assembled from that chat, not one resident-wide resumed session.
   Shared soul/help must contain no member memory. Model identity does not
   grant permission to retrieve the resident's other conversations.
4. A typed tool broker runs under caller rights intersected with declared module
   capabilities. It validates IDs/revisions, strips hidden fields, marks web and
   tool content untrusted, and returns grounded references. Provider text is
   data; neither web text nor tool output can grant authority or confirm sends.
5. Private drafts hold author, destination, content and revision. The trusted UI
   previews these and the author's explicit submit calls the publish path.
   Recheck rights and exact revision at publish; edits invalidate confirmation,
   retries cannot double-send. The model has draft capability, no publish tool.
   The same distinction applies to other external effects.
6. A provider adapter receives approved context and emits text/typed tool
   proposals. Credentials stay outside chat/world facts/model context; its
   binding carries owner, route, auth method, readiness, model, limits and
   cancellation policy. No silent provider or billing fallback. Web fetching
   remains a separately scoped adapter, with approved queries, no private
   network targets, bounded redirects/bytes/time and explicit unavailability.

The missing general capabilities are **conversation-scoped execution**,
**caller-bound asynchronous tool delegation**, and **author-confirmed drafts**.
This task can carry those gaps; no unrelated worker or parallel UI task is
needed. Reusing world data alone cannot fix the current session boundary.

After review, the first hidden increment can use synthetic people and a fake
provider to prove the resolver, ACLs, tools and draft lifecycle. Fake-provider
plumbing is not a Sonnet demonstration. Provider readiness should remain
explicitly unavailable until an existing approved route is established.
Discoverable help must explain private audience, source links, draft versus
send, unavailable tools/provider, and the off switch.

Proposed fixture gates (not run):

- Two members and a resident: direct guessed IDs, search, rows, history, links,
  events, diagnostics and provider payloads never reveal the other sentinel.
- Alternating turns, parallel opens, restart, compaction, fallback, cancellation
  and delayed tool replies never switch person/chat or reuse another context.
- Revocation before dispatch, during inference and before reply/publication
  prevents stale disclosure; field-hidden names remain hidden.
- Injection in board/help/web/tool data cannot call a forbidden tool, change
  requester, read another chat, publish a draft or manufacture confirmation.
- Draft preview/edit/confirm/retry/cross-author actions enforce exact content,
  target, author and one successful send.
- Grounded search/object/map demonstrations reference only projected objects;
  network calls remain mocked until provider/egress authorization.
- Scoped grants survive aliases, nested modules, broad `rows`, expired calls
  and stale revisions. No steward or unrestricted agent-session fallback.

## 7. Supported provider options, read 5 November

These are documentation findings, not account entitlement checks. No login,
client registration, connection, billing change or credential lookup occurred.

| Option | Supported direction and limitation |
| --- | --- |
| Existing Claude CLI, bounded Alex test | Current House transport can select Sonnet. Effective auth, exact model availability, new-identity signer and billing constraints remain unverified. An existing personal test route is not permission to serve other people. |
| Claude API / supported cloud provider | Programmatic product route. Console API keys or supported workload/cloud authentication require their own approved access and billing; no such access was established here. [API overview](https://platform.claude.com/docs/en/api/overview). |
| Own Claude subscription | Anthropic distinguishes an end user signing into an unmodified hosted Claude Code binary from an app offering its own Claude.ai login or routing other users through plan credentials. The latter is restricted; don't build token collection or a shared subscription relay. [Credential and product conditions](https://code.claude.com/docs/en/legal-and-compliance), [SDK guidance](https://code.claude.com/docs/en/agent-sdk/overview). |
| Own ChatGPT via current Codex adapter | Local adapter already supports native subscription authentication, but is not a member auth/tenancy implementation. Official Codex docs distinguish subscription and API-key modes; app-server auth is not permitted for commercial/hosted services. [Authentication](https://developers.openai.com/codex/auth), [App-server auth endpoints](https://developers.openai.com/codex/app-server#auth-endpoints). |
| Own ChatGPT via supported app sign-in | Official Sign in with ChatGPT now documents optional plan usage for eligible requests by open-source/locally hosted apps. Paid or remotely hosted offerings take a separate eligibility path. This is a future extension requiring app registration, consent, per-user bindings and preview-limit review, not something enabled here. [Overview](https://developers.openai.com/siwc/token-sharing-open-source), [Preview limitations](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations). |
| Shared low-cost default | Evaluate local inference quality/resource cost first, or a separately authorised service API account and budget. No default model, purchase, connection or spending permission inferred. |

Do not claim either “every subscription includes API use” or “no subscription
ever includes API credits.” Official billing pages distinguish the products;
Anthropic currently also describes monthly API credits for some plans, still
requiring separate Console access. Actual entitlement and permitted use need
checking when Alex chooses a route. [Claude billing](https://support.claude.com/en/articles/9876003-why-is-claude-api-usage-billed-separately-from-my-paid-claude-plan),
[OpenAI billing](https://help.openai.com/en/articles/9039756-managing-billing-for-chatgpt-and-the-api-platform).

## 8. Decisions for Alex through JEFF

The explicit task already settles private per-member history, caller-scoped
retrieval, no ambient stewardship and author-confirmed external effects.
Those are requirements, not questions to reopen.

Novel choices still need review:

| Decision | Conservative proposal pending review |
| --- | --- |
| Which remote data may leave Seabright? | Synthetic fixtures first; identify approved categories and consent before sending private chats, member-visible posts or map queries to a provider. Visibility alone is not export permission. |
| Which provider relationship serves members? | Separate bounded Alex Sonnet test from member service. Decide local default versus authorised service API; set explicit budget/rate limits. Own-provider connection remains future opt-in. |
| What does private mean operationally? | Define transcript/summary/log retention, deletion, backups, operator access and provider retention disclosure. Chat ACLs protect application readers, not the machine administrator. |
| Which additional tools/actions are in scope? | Begin read/reference/map intents and private drafts. Authorise external search egress separately; preserve explicit author confirmation for publishing and other effects. |
| Where will members run/connect? | Local/OSS versus remote hosted deployment changes supported subscription integration and credential custody. Confirm before designing login UI. |

**Needed from Pike/JEFF:** review this boundary and route only the novel choices
to Alex; then commission the scoped hidden-fixture increment. Establish an
approved existing Sonnet route without sharing credentials, or retain the
provider blocker. No permission to weaken privacy is needed or proposed.

## Evidence and delivery status

**Read:** AGENTS.md; live charter dk838; task dk2770; guide dk371; map dk864;
search research dk2675; Shop talk coordination; live channel/module/provider
metadata and help. Source paths/functions above were inspected.
Existing `tests/test_chat.py` covers closed-chat, addressing, reply and forged
line cases; its presence is not a new passing test result.

**Ran:** read-only repository/world inspection and document-reference checks
recorded in BUILD-RESULT.md. The proposal was sent to JEFF and Sable in Shop talk
(dk2797, receipt r6150). This is delivery of a proposal, not approval.

**Not done:** implementation, Sonnet inference, hidden privacy/adversarial
fixtures, UI entry, member journeys, web-provider integration, live activation
or outcome review. This turn completes the requested inspection only.

