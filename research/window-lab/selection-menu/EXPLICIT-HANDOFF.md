# Explicit selection continuation

Source checkpoint on worker/a8420, based on fresh main 490b7fb; original
6f9e8ac patch reused with `git apply`, not rebuilt. No main/worktree override,
no git-index mutation. House must merge newer main before landing.

## Callable world contract

**Historical inspection, superseded by the authorized preservation fix below:**
the paired-action parser initially refused
native multi-command cleanup chains AND multiple guarded plain variants.
This blocks adoption by the existing Conversation. It rejects the lens rather
than stripping cleanup. Do not simplify native Send to fit this restriction.
Source/copy inspection only was authorized for this finding; no preservation
fix has been made. Exact receipts: `MOUNTED-COMPOSER.json` and
`NATIVE-SEND-INSPECTION.json`.

Actor-bound read-only Session on frontier-try, deep-copied in memory, compiled
home-base as **alex**, e18572 / **18574 events**, **2588 nodes**. The one offered
explicit composer is:

```text
home/tiles/lens:home-tiling/stage/f5664/body/tiling/a6802/body/lens:jeff-chat/chat/a5082/dock/say
```

Cold recompile after clearing reuse/last-good caches returned the identical key.
Renderer assigns `el.dataset.key = n.key`; this is the actual compiled mount,
not a local-key guess or DOM/browser observation. Same authored mount, panel,
repeat identity and branch keep the path through recompile/repaint. A moved
panel, renamed part, changed repeat identity or dock/commentbox branch can
change it. DOM reuse separately requires the same paint/actions; a rebuilt
element with the same key can still recover the page-memory quote. Nothing
here proves stability across structural edits or page reload.

Read native jeff-chat revision **34**. Current mounted ordinary Send is a
single append with captures/context_from/reply_to/About. Its explicit
topic/reply variants each include append/comment + read + cleanup prop
(**3 commands**). Existing-Talk quote variants have **3 or 5 commands**,
including writer and draft cleanup. Missing-Talk creation chains have 7/9
commands and remain outside initial scope. Each say part currently declares
four ordinary world-guarded edit variants; only one is offered for this state.

`scene.parse` refuses a native 3-command action paired with quoted edit:
`on edit quoted do needs commit explicit, exactly one plain on edit without
quote bindings, and one quoted action consuming $quote_text; each sends one
command`. Exact restrictions are scene.py's static plain/quoted cardinality
and `len(split_batch(action["line"])) != 1`. Existing dispatch already sends
the entire chosen action string once through `/api/do`, `whole` unset, and
the established batch engine preserves its steps. Ordinary unpaired native
actions still support those chains; this is the new paired parser limitation.

Smallest proposed preservation fix (imagined, **not implemented**): allow full
authored batch strings in both branches, keep all native cleanup steps; allow
ordinary guarded variants statically and fail closed after guard evaluation
unless exactly one plain action and at most one quoted action are offered.
Continue making one existing composer and one send call for the selected full
action, with current source/context fences and batch semantics. No second
composer, logged quote flag, routing change or new atomic-batch promise.

`on menu "Comment" prepare <exact-painted-composer-key>`

Optional suffixes: `context=<item> destination=<item>`. Both items must have an
integer revision in the menu origin's fence reads. Use canonical subject ids
actually read by the lens; there is no current-item or Talk inference. A frame
must read each relation/target before naming it. Missing/ambiguous destination
composers refuse; only the named existing explicit composer receives the packet.
Its quoted edit action must consume `$quote_text`, so no attachment silently disappears.

Single-composer source continuation authorized by JEFF, 21 Oct:

```text
say : text ""
  commit explicit
  on edit do <world-authored plain command>
  on edit quoted do <world-authored quoted command consuming $quote_text>
```

The angle-bracket passages are schema placeholders, not executable commands.
Each branch retains its complete native action batch; the plain branch must have no
quote bindings. Presence is tested locally at Send before substitution, not a
world guard/logged flag. Both actions belong to the SAME existing composer key.
`Remove quote` detaches the packet and restores plain Send with the same words.
There is no second composer, window store, general quote guard or Talk resolver.
Compiled quoted actions have `on:"edit-quoted"`; only plain `on:"edit"` creates
the existing editor. Missing/guard-filtered quoted consumer refuses preparation.
Legacy single quoted action remains supported but still cannot Send without a
quote; migrate such consumers to the paired form above for ordinary Talk.
The limited literal About conflict check inspects both branches.

## Authorized native action preservation (source-prepared only)

Implemented after JEFF c8491: static paired declarations permit guarded native
variants and full batches. After normal guard evaluation, exactly one plain
action and at most one quoted action must be offered. No plain or ambiguous
actions refuse compilation; a nested lens can show its existing refusal
placeholder. Zero quoted leaves ordinary Send available but refuses Comment
preparation. Local quote presence selects just one entire action before
substitution. No second composer, routing change or batch transaction.

Actual world-authored paired subtree: `PAIRED-WORLD-EXAMPLE.txt`, published
verbatim and read-back compared in world note a8468. Rowan's exact a8379
held-quote/commenting-subtree replacements were staged on a deep copy ONLY;
the four normal Send action lines are unchanged. `inspect_paired_copy.py`
uses official read-only Session then deepcopy, no hud_playtest/process helpers,
no dispatch/save. It writes only evidence artifacts beside itself.

Ran `python research/window-lab/selection-menu/inspect_paired_copy.py`:
**5 copied mounted guard cases passed; e18782; events 18784->18784; no dispatch**.
Four actual native ordinary routes compile with full 1/3/3/3-command chains;
empty context also offers quoted, topic/reply/thread contexts filter quoted.
The quoted consumer retains captures/context_from. Conflicting reply+thread
withholds the nested composer as ambiguous. The mounted key remains:
`home/tiles/lens:home-tiling/stage/f5664/body/tiling/a6802/body/lens:jeff-chat/chat/a5082/dock/say`.
Receipt: `PAIRED-COPY.json`. This proves compilation only, not message/capture
delivery, real DOM, browser restoration or source-navigation acceptance.

Ran `node research/window-lab/selection-menu/test_composer_quote.cjs`:
**8 composer quote scenarios passed (source mocks only)**, including native
3/5-command existing-Talk batches retained as one chosen action and filtered
quoted preparation refusal. Ran `test_send_receipts.cjs`: **2 sender receipt
scenarios passed (actual sender/Viewer, mocked door)**, partial-batch error and
lost answer both retain words/gesture; same-id retry uses the same full batch.
Ran snapshot/compiler unittest: **5 tests OK**, including four guarded routes,
ambiguous/no-plain refusal and disposable append-before-cleanup-refusal.
Selected health frontier-try **e18782,18784 events**: python/scripts/bound_words/
snapshot OK, **partial=true,total2.1s**.

**Inherited retry hazard:** a native semicolon batch can append successfully,
then cleanup refuses and later steps stop. Append is not rolled back. Read
deskd.py: all earlier successful events receive the gesture ID despite partial
failure; same-ID retry can return already done without running failed cleanup.
Actual sender/Viewer plus mocked dedup answer clears the draft on that receipt,
which DOES NOT establish cleanup completion. Editing/rebasing to a fresh gesture
can append again. Lost-answer retries retain the same partial-outcome uncertainty.
Server dedup ordering was read, not newly HTTP-tested. The existing batch-stop
behavior conflicts with Alex's broad continue-after-refusal rule; it is
reported, preserved, and outside this narrowly authorized fix. No atomic
success, rollback or automatic cleanup recovery claim.

Main advanced to bf0974894c36c36a3a7f4e4e44d4a35a13e10336 in unrelated followup
files; read diff shows no overlapping files. No merge/main override attempted;
house must merge before eventual landing. Source stays uncommitted, paused,
**not ready/live**. Browser stop/unknown cleanup and all unsupported limits
remain. No browser retry, live Send or process cleanup action.

Highlighting, release, Shift-selection and menu-open/cancel never execute
legacy `on select` acts. World owners still remove these obsolete handlers.
There is no pointerdown suppression, grip/carry rule, tab change, or second composer.

Exact direct `text $text`, `text $title`, `text $frame.text/title` expressions
emit `paint.source: {item: string, rev: integer, field: "text"|"title"}`.
Computed labels, clamped summaries whose DOM differs, and generated names have
no guessed provenance and refuse Comment. Ordinary clipping of an unchanged
source string keeps its source. Markdown uses TextEdit's source anchor; dirty
unsaved source refuses quotation until saved. Selection remains usable for Copy.
Chat-line/thread fields and generated title/reference mappings remain unsupported
and must be reported as gaps, not product-wide coverage.

The packet is:

```typescript
type Selection = {
  item: string; rev: number; field: "text" | "title";
  start: number; end: number; // half-open UTF-16 code units in underlying field
  quote: string; before: string; after: string; // six source words either side
  context: { item?: {item: string; rev: number};
             destination?: {item: string; rev: number} };
  label: string; // displayed source title, never a shown internal id
};
```

`POST /api/selection {session, as, selection}` validates current source/field,
exact range, quote, ordinary `may_read` and context revisions. It returns
`{selection}` or `{error}` and writes no world event/seen cursor/report.
The existing door's actor routing is reused; this adds no authentication claim.
Plain DOM offsets distinguish repeated words. Markdown anchors retain marks.
One local Map, keyed by the actual composer key, holds prepared packets for this
page only. No selection/quote in URL, reports, logged writer props, localStorage,
or another window. Source links contain identity only. Existing words, undo,
attachments and native action/About are not rewritten. Another attached quote
refuses replacement; Remove quote explicitly detaches it. An authored context
conflicting with a concrete native About refuses.

Consumer actions may name `$quote_item`, `$quote_rev`, `$quote_field`,
`$quote_start`, `$quote_end`, `$quote_text`, `$quote_before`, `$quote_after`,
`$quote_context`, `$quote_destination`, inside ordinary quoted command values
as appropriate. The last two are ids, or empty, never implicit About. All facts
and `$value` substitute in a single pass, preventing selected words from
becoming a second template expansion. Source revision is checked before Send
and by `/api/do` under the command lock via `source_quote`; stale source/context
refuses with the draft and attachment kept. Gesture-id deduplication runs first.
Clear only after durable success, not error/lost answer. World owns native
Talk/thread routing and destination choice; no Conversation policy is in source.

Limitations: quote is page-memory only (survives repaint/navigation retaining
the same composer identity, not page reload); existing text draft storage is
unchanged. Full Conversation consumer hunks are Rowan's and are not authored
or applied here. Existing world lenses must retain one composer identity;
the prior two-node consumer still needs Rowan's paired change. No general
history/window migration. No captured heading binding. No live demo/release
or broad product acceptance without the guarded browser result and world hunks.

## Bounded execution handoff

Run `python research/window-lab/selection-menu/explicit_acceptance.py` from
this worktree. It uses a disposable logged copy via hud_playtest.Copy and hidden
Edge with Guard; no visible fallback or repeated pre-page-ready attempts.
All Copy/Cut APIs are page recorders installed before test navigation, never
the shared clipboard. The original steps.py/journeys.py are historical only.

`world-menu-fixtures.json` holds the full exact live lenses read 21 Oct for
Rowan's branch-scoped hunks. The harness requires each hunk exactly once,
stages the same replacements only on its copy, compiles BOTH full lenses and
checks tag/design/dual eligibility, stale fencing and undo through the actual
copy door. It never invokes underlying deletion. No live world/lens apply,
Conversation test sends, desktop input/capture, host restart, settings or install.

Browser recipe currently records the changed plain-text highlight/menu/keyboard/
preparation, kept words, stale refusal, Markdown Copy and staged review menus.
It honestly reports remaining 1280/Cut-undo/full browser journey gaps, rather
than treating the historical checkpoint as acceptance. Execution owner should
complete those in this same copy lane, not start a separate review worker.

## Evidence before browser

- Ran test_selection_snapshot: 3 tests, OK (exact source/repeated UTF-16 ranges,
  permission/refusal/context/title cases, no mutation, compiler provenance).
- Ran selected health on frontier-try at e18572, 18574 events: python/scripts/
  test_selection_snapshot OK, partial=true, 2.7 seconds. Not a full judgment.
- Ran test_scene: 31 printed passing checks, then PermissionError writing
  its temporary base@walk.pickle. No all-tests-passed claim or ACL workaround.
- Ran git diff --check: clean. HEAD and main had identical tracked content
  before editing and again during this checkpoint; no manual main mutation.
- Read neighboring cards: a7987 paint/settle checkpoint is parked; a8138 owns
  tab/show/fetchScene and viewer.js windowValues. Coordination comments posted
  before changes. These hunks are outside those seams.
- Model card observed gpt-6.1-sol; resolved effort medium, actual effort blank
  (unknown). No exact actual-effort validation claim or substituted runtime.

Browser report, source hashes and final execution disposition are recorded
beside this file and on the commission. Nothing is production-ready merely
because a source/checkpoint test passed.

## Stopped browser lane — execution owner takes over

Ran 21 Oct, report `results/20261021-130228/report.json`.
Exactly ONE actual hidden Edge/Guard attempt: Edge started on the sandbox
desktop but failed at `document.readyState` with ConnectionClosedError; its
DevTools port stopped answering (URLError). Edge pid 59660 presence unknown;
cleanup was requested, not certified closed. Guard returned **0**, Alex
untouched (foreground, focus, cursor and input desktop polled every 20 ms).
No browser assertions, screenshots, recording, viewport or Cut/undo proof.
No retry, fallback, new worker, host restart, install or settings change.
Earlier runs corrected fixture setup (notice parsing, surface tag/type,
intended copied actor); none reached Window.open or launched a browser.

Before the browser failure the SAME copy accepted Rowan's exact staged hunks:
home-board **240** nodes, waiting-on-me **46** nodes, both compiled.
For BOTH full lenses the actual copy door proved tag-selected and dual-eligible
rows expose Remove review request, design-only rows do not, stale action refuses
without an event, undo restores exactly the shared tag, and the dual item still
belongs to the design selection. No underlying deletion. These are compiled
scene/HTTP action results, **not browser menu acceptance**.

Final selected health: frontier-try e18572, **18574 events**; python/scripts/
test_bound_words/test_selection_snapshot OK; partial=true, **2.1 s**.
Handbook binder's Lenses/markdown passage labels the contract PENDING.
Notebook entry warns about actor-bound 3-node empty-shell false coverage.

Execution owner Codex must reconcile the retained sandbox ownership receipt
before another browser launch, then complete changed-behavior mouse/keyboard,
Markdown source mapping, editable Cut/undo with recorded clipboard, existing
draft/attachments/About, source/context stale-before-Comment/Send, source
navigation and both viewport journeys in the SAME bounded copy lane. The
fixture Send action targets a disposable note prop only; never the Conversation.
Catch/report Window.open's SystemExit explicitly in the test harness if needed:
the finally report preserved Guard/copy evidence, while the failure text was
printed by the sandbox owner after it. Do not treat the report's missing error
member as a browser pass. Rowan still owns executable production menu/consumer
hunks; no production world changes have been applied.

Bounded follow-up (source/mocks only): ran
`node research/window-lab/selection-menu/test_composer_quote.cjs`: **6 composer
quote scenarios passed**. Executes actual preparation/composer functions with
DOM/door mocks: plain Send, quoted Send plus concurrent duplicate click,
Remove quote→plain, existing quote and both branch About conflicts, stale
preflight refusal retaining draft/quote with zero dispatch, mocked atomic
refusal retaining draft with exactly one action. No Conversation sends or browser.
Ran snapshot/compiler tests: **3 tests OK**, including paired action emission
and malformed branch refusal. This supersedes the earlier quote-required
ordinary-Send limitation only; all browser/ownership/provenance limits remain.
Final follow-up selected health: frontier-try **e18572, 18574 events**;
python/scripts/test_bound_words/test_selection_snapshot OK, **partial=true,
2.2 s**. `node --check lens.js` and `git diff --check` passed. Refreshed hashes
include the source-only composer mock test. No browser retry or cleanup action.

Source is preserved uncommitted per worker sandbox protocol. **Not ready; do
not land this checkpoint** until execution acceptance and paired world rollout
are resolved. Requested model matches observed; requested/resolved medium
effort has no actual-effort receipt, so that validation also remains unknown.

## Retained ownership evidence (read; no process query)

Owned manifest: `scratch/agora-sandbox/playtest-36200.json`.
Its launcher/session name is playtest-36200; the intended hidden desktop is
`agora-sandbox-playtest-36200`. Intended launcher is sandbox_window's Edge
launcher; the actual executable, native creation time and parent identity
are **unknown**, not verified from the session name or wall-clock timestamps.
The manifest records `launches=[{status:"created",at:1792612959.3270879,
pid:59660}]`, `at=1792612960.6460173`, `pids=[59660]`, `owners=[]`.
Metadata acquisition failed: `MetadataUnavailable`, message redacted,
winerror/hresult null; receipt returncode 1, stderr `Access denied`.
DevTools port was 64787; copied page was
`http://127.0.0.1:64621/lens.html?session=frontier-try-playtest-36200&as=worker-a8420&lens=explicit-menu-fixture&view=painter&inspect=0&on=a8426`.

Exact retained profile:
`C:\Projects\Agora4\.worktrees\a8420\research\window-lab\selection-menu\scratch\agora-sandbox\playtest-36200-profile`.
Both cleanup receipts say `{status:"refused",reason:"ownership incomplete"}`.
There is no certified termination or absence receipt. Guard 0 does not prove
cleanup. No additional process query or termination was attempted.
Preserve this profile for the execution owner's reconciliation; exclude
`scratch/` runtime/profile files from any future source landing.

# Canonical paired release checkpoint — 21 Oct

SOURCE/COPY PASS; NOT READY OR LIVE. This supersedes the earlier appearance-ID
menu refusal and earlier “exactly one command” restriction. House preserved the
implementation in 22d7470. This continuation changes tests/artifacts/docs only.
Main is bf0974894c36c36a3a7f4e4e44d4a35a13e10336; no merge/override attempted.
An eventual house merge and execution acceptance remain required.

Rowan's exact corrected direct-note menu, paired with the native-preserving
consumer already printed in PAIRED-WORLD-EXAMPLE.txt:

```text
              let destination_title = join($title of $d.talk) when talk != ""
              let destination_title = "" otherwise
              let destination_id = join($id of $d.talk) when talk != ""
              let destination_id = "" otherwise
              on menu "Comment" prepare home/tiles/lens:home-tiling/stage/f5664/body/tiling/a6802/body/lens:jeff-chat/chat/a5082/dock/say context=$d.id destination=$(destination_id)
```

RAN `python research/window-lab/selection-menu/inspect_paired_copy.py`:
**5 copied mounted guard cases passed** at copied e18947, **18949 events**,
events18949->18949 with no dispatch. Same mounted key in all ordinary branches;
four native ordinary actions preserved byte-for-byte (1/3/3/3 commands);
ambiguous reply/thread withholds the composer. Exact corrected menu plus
consumer accepted in the SAME in-memory actor-bound copy. Fixture setup:
18949->18953 events; assertions18953->18953. Emitted context s8535/rev1 and
destination s8531/rev1 both have integer fences; source is s8535/rev1/text,
UTF16 range[5,9), quote "same", before "same", after "**bold** end".
These are disposable fixture IDs, not production bindings. Unreadable Talk,
stale Talk and stale source refuse. Separate disposable delivery copy accepts
native append to canonical fixture Talk s8531:18953->18954 events. No real
Conversation sends, session writes, browser or private capture-store access.

RAN `node research/window-lab/selection-menu/test_composer_quote.cjs`:
**8 composer quote scenarios passed** plus **2 exact compiled paired-menu
scenarios passed**. Actual prepare/composer functions consume the emitted menu,
fence, validated snapshot and mounted consumer; DOM and transport are mocks.
Preparation makes zero sends and preserves words/capture arguments. Changing
copied viewer and To from Rowan to Pike, then same-key repaint, keeps the quote
and captured Talk. One mocked quoted dispatch targets that canonical Talk,
with both original capture IDs. Remove quote restores exact ordinary Send;
stale preflight dispatches nothing and retains words/quote. Conflicting existing
quote/About and filtered quoted branch refuse preparation.

RAN `node research/window-lab/selection-menu/test_send_receipts.cjs`:
**2 sender receipt scenarios passed** (actual sender/Viewer, mocked door).
RAN `python research/text-desk-lab/notation/test_selection_snapshot.py`:
**5 tests OK**. `git diff --check` clean. Earlier selected health and Rowan
review-menu copy proofs remain historical, explicitly not fresh browser proof.
Review menus home-board240nodes/waiting-on-me46nodes, tag/design/dual
eligibility, stale refusal, undo/tag preservation remain in the same bounded
acceptance artifact; no deletion.

Copy recipe: run the four commands above in order; inspect PAIRED-COPY.json,
PAIRED-MENU-COPY.json and PAIRED-WORLD-EXAMPLE.txt. Use the official read-only
Session/deepcopy path in the script, actor alex; do not open session pickles
directly. Do not run explicit_acceptance.py here: it includes a browser lane
already stopped before page-ready.

Remaining execution/rollout gaps:

- Browser selection restoration, native fallback, editable Cut undo, Markdown
  mapping and viewport journeys unverified for changed behavior. No screenshots.
- Real capture delivery/detach unproven; capture rows and consumer sends mocked.
- Quote display names source/quote only. It does not show captured Talk or
  explain its precedence over To chips: visible destination clarity is a gap.
- Existing-Talk/direct-note initial scope only. No absent-Talk creation,
  generated/paragraph/thread/Reader/standalone Writing quote consumers or reload
  persistence. No production world rollout; inspect legacy held drafts first.
- Native batches remain non-atomic: append may succeed before cleanup refuses.
  Same-gesture dedup can clear draft without recovering cleanup; fresh gesture
  risks duplicate append. Native 3/5-command suffixes are preserved, not repaired.
- The single browser attempt failed before ready. PID59660 native creation,
  parent/executable and ownership remain UNKNOWN; owners=[]; both cleanup
  receipts refused “ownership incomplete.” Guard0 is not cleanup proof.
  Exact manifest/profile/desktop/launcher evidence remains in EXPLICIT-HANDOFF.md.
  No new process query, cleanup action or retry. Preserve retained profile;
  exclude scratch runtime/profile from eventual source landing.
- Requested model matches actual receipt; actual effort remains blank/UNKNOWN.
  JEFF owns execution-owner transfer; recipient acknowledgment is unestablished.

The implementation stays paused. No ready/landing or browser retry by this worker.
