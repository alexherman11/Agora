# Standing rules: a6536 acceptance handoff

Source in `worker/a6536`, 20 Oct 2026, prepared for house landing under JEFF
c6735/c6737. Live spawn/compaction acceptance is deferred to JEFF after landing.

The live source is the placed note with `role=agent-charter` (currently a6529).
`charter.py` reads that source at a fresh worker/resident start and at provider
compaction. A plain resume retains the cached charter. A newly assigned card
gets its own start read, including a standing builder taking another card.
For migration, a saved session without a cached charter gets one initial read.

`start=` on the resident corner or worker card adds read commands at those
boundaries. Non-read commands are refused by the hook. The default charter is
included even without that prop. Its injected block is at most 500 words;
an oversized source yields whole-rule extracts, a full-note read link and a
warning to JEFF. Missing/empty/ambiguous sources produce a banner and allow
startup. Missing/empty sources explicitly say once in the injected start block
`charter: not read: note missing or ambiguous` / `charter: not read: note empty`,
followed by “starting without standing rules.” Additional `start=` reads are
separate from this charter budget.

Claude receives the charter in its initial system prompt. Its documented
`SessionStart` hook with matcher `compact` supplies fresh `additionalContext`
after compaction. That hook supplies context, not a replacement system role.
Codex receives initial `developerInstructions`; its `contextCompaction`
completion triggers `thread/inject_items` with a developer message. Legacy
`thread/compacted` duplicates are suppressed. Inference was not run to verify
the timing of the injected item relative to the next model request.

The house records a `charter read (reason: start|compaction)` receipt without
waking residents. Corners are surfaces and cannot have native comments, so
their last receipt is a `charter_read` prop. Worker cards get native comments.
After a successful worker process spawn, the card gets `rules injected
(<n> words, as of event e<n>)`. A cached ordinary resume says so explicitly.

The existing house pass regenerates only the marked block in both local
AGENTS.md and the carried AGENTS.md note when the source changes. The block
contains the first ten rules in source order; JEFF can prioritize them there.
Surrounding human edits are preserved. Marker damage refuses regeneration.
Warnings are deduplicated within a house process, not across house restarts.

## Ran

- `test_charter.py`: **16 tests, OK**, final run 0.639s. Includes changed rules in both provider
  stub prompts, fresh/resumed sessions, compact-hook paths, failed reinjection,
  missing/empty and oversized sources, warning deduplication, generated mirrors,
  surrounding edits and rejection of non-read/multiline start commands.
  `test_rule_edit_updates_both_mirrors_without_knocks_or_session_nudges` edits
  as Alex in an in-memory world and uses the real mirror updater, house knock
  recorder/resident news and workshop worker-hearing logic. Both mirrors change,
  no knock event or resident call/news appears, the worker hears nothing, and
  start/send/Popen spies stay untouched. Cached rules stay unchanged; ordinary
  resume retains them, compaction and fresh start read the new rule.
  Missing/empty fixtures exercise both providers and assert exactly one explicit
  not-read line in the startup prompt, while starts continue.
- `pytest research/codex-residents/test_transport.py -q -p no:cacheprovider`:
  **5 passed in 1.02s**.
- `test_builders.py`, `test_worker_pool.py`, `test_worker_grant.py`: each printed
  **all passed** after the final worker resume correction.
- `test_house_words.py`: **all passed** on this takeover.
- Prior builder: `health.check_python()`: **[]**, copy at e12976 with 12961 events.
- `verify_charter.py`: copy at **e13175, 13162 events**, current charter **404**
  injected words. Changing one rule only in memory reached both actual
  Worker.start paths with stub processes. Their native copy card receipts were
  **rules injected (411 words, as of event e13178)** and **e13181**, respectively.
  It explicitly printed that no world was saved, process or model started.
- Ruff checks for charter, its tests/verifier, both Codex transports and the
  transport test passed. `git diff --check` passed.

The three older lifecycle tests and transport test now use the landed
`agora_tmp.directory` helper because the sandbox refuses normal temporary
directories. Their behavioral assertions were retained.

## Read

- [Claude hook reference](https://code.claude.com/docs/en/hooks):
  SessionStart compact matcher and JSON additionalContext.
- [Codex app-server reference](https://learn.chatgpt.com/docs/app-server):
  contextCompaction item lifecycle, legacy compact event and
  thread/inject_items raw messages visible to subsequent model requests.
- Installed SDK 0.147.0 generated ThreadInjectItems response and request types.
- Card and refinement, builders' notebook, house/workshop and provider transports.

## Preserved effects and remaining acceptance

Shop talk m6700 coordinated the AGENTS block with Claude and Codex before the
edit. There was no Claude listener; the unavailable Codex listener queued it.
Only this commission's generated block changed in the worktree AGENTS.md.
Main's uncommitted human edits have not been edited.

Live documentation effects already completed: e12995 inserted only the
generated block into carried AGENTS.md a3973; e12996 marked a6529 with
role=agent-charter; e12997 added Rough spots a6728 naming the missing world
word. The actual live charter text and wake lines were not changed.

Real worker spawn and real Claude/Codex compaction are **not verified**. The
requested real-start injection receipt must be observed on an ordinary worker
after reviewed source landing; the copy receipts are not substitutes. Existing
interactive Claude/Codex app sessions have only the generated AGENTS block
available to read; this patch cannot force an already running app to reread it
or install its compaction hook. Residents' old per-wake reads remain until JEFF
accepts the new hooks and removes them.

`git merge main` was refused at ORIG_HEAD.lock (Permission denied). No retry,
commit or permission workaround was attempted. The house must reconcile current
main and preserve its uncommitted AGENTS edits before landing.

The Handbook's “Residents: the house” (a637) and “Commissions, workers and the
keeper” (a639) are updated for source landing, with live acceptance explicitly
pending. The exported source documents file was not edited. The house must
preserve/reconcile main's human AGENTS edits and the overlapping runtime-pin
transport changes from a6498; no merge was retried here.
