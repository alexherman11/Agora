# a6646 — ready for house landing, 20 Oct

The earlier draft record below is superseded by this takeover record.

## Final takeover recheck (worker-a6646, 20 Oct)

Read git status/log/diff, this card and comments, builders notebook, live
standing rules, existing world widget/settings and Handbook before acting.
World application e13073–e13079 was verified as preserved, not repeated.

- **Ran:** `test_plan_usage.py`: **16 tests OK in 1.253s**. Extended the existing
  gauge test to inspect evaluated fill roles at 69/70/89/90/100%, confirming
  green/amber/amber/red/red, rather than counting names in a style definition.
- **Ran:** `test_builders.py`: **all passed**, with TEMP/TMP/TMPDIR/AGORA_TMP
  pointing to `local/usage-check-temp`, made with os.makedirs in this worktree.
  The preserved inherited-ACL fixture fix is still required.
- **Ran:** `test_usage.py`: **all passed**, 21 printed ok checks.
- **Ran:** `verify.py frontier-try` with the existing house metadata: copy
  **e13082, 13067 events**, all five affected lenses current; Claude **72%
  five-hour / 17% weekly**, as of **20 Oct 13:13**, resets 17:10 and
  26 Oct 15:00. Codex says unavailable. Two native copy cards produced one hit
  and one resume notice, with states cleared. This loads metadata through its
  existing parser, never transcript grep; the copy is not saved.
- **Ran:** changed Python Ruff F checks **All checks passed!**;
  `git diff --check` exits 0.
- **Not run here: needs a browser-capable run:** real gauge shots, hover and
  geometry inspection. No repeated browser launch, account/profile access,
  live provider limit, real model trial or full-health pass. The earlier real
  Codex quota probe remains blocked by inventory validation; it was not bypassed.
- No main merge attempted. The house owns commit/merge/judgement under the
  sandbox protocol and will return conflicts as source edits.

The installed world half need not be recreated. After landing, the house
restart supplies Usage rows. Browser follow-up: inspect 70%/90% gauge colors and
hover percent/reset/source/as-of at Alex's scale, glance and reader settings,
queued card text at threshold, paused/resuming/cleared states at reset +60,
resident pending-line retention, and one hit/resume notice per provider episode
with two cards and two providers. Confirm actual toasts on a copy, not merely
the native notification records. No screenshots or recording exist here.

Ran in this worktree:

- `test_plan_usage.py`: **16 tests OK**, including retained sibling pause targets
  across a repeated limit, and a stalled Codex metadata request that cannot block
  future turns or accumulate requests. The SDK request itself has no timeout;
  the adapter waits at most two seconds and retains one daemon request per client.
- `test_builders.py`: **all passed** after fixing its fixture to use uuid plus
  os.makedirs, inheriting the parent ACL. Setting TEMP/TMP/TMPDIR/AGORA_TMP alone
  was insufficient: TemporaryDirectory still made an inaccessible child.
- `test_usage.py`: **all passed**, 21 printed ok checks.
- `test_transport.py`: **5 passed in 0.79s**, with a local pytest plugin replacing
  only tmp_path with a uuid/os.makedirs directory under this worktree. Ordinary
  pytest: 4 passed, 1 ACL setup error. The test bodies were unchanged.
- `verify.py frontier-try <main house-state/frontier>`: copy **e12976, 12961
  events**, five affected lenses current; real read-only Claude metadata
  **62% five-hour, 17% weekly**, as of **20 Oct 13:04**, resets 17:10 and
  26 Oct 15:00. Two fake paused cards produced one hit and one resume notice,
  native acknowledgements confirmed, states cleared. No copied world was saved.
- Changed-file Ruff F checks passed; git diff --check clean.

World integration applied through Desk MCP after fresh reads, e13073–e13079:
independent style and three lenses, body-scoped glance/board additions, and only
the house settings role (no threshold or account setting changed). These use
existing lens words; before the source lands the absent Usage rows render empty.
Native compilation receipts pass; they are not painted/window evidence.
Exact pre-edit glance/board/settings text is saved in live-before.json.
Handbook a639 updated at e13083; Rough spots a6662 remains unchecked.

Still unverified:

- **Real gauge shots: not run here: needs a browser-capable run.** No visible
  test window or toast was shown on Alex's screen, and no recording was made.
- Actual Codex quota probe still refuses worktree worker-model-catalog.json
  inventory validation before service contact. The checker was not bypassed,
  no credentials or account profile were touched, and its Usage row says unavailable.
- test_scene.py printed 31 ok checks, then stopped at its existing Temp fork
  fixture with PermissionError. This is not a full scene-suite pass.
- No real provider limit, real model trial, full health, main merge or running-house
  recovery cycle was run. The house judges the source against current main.

The checked world half is already installed; do not recreate it after landing.
Source landing/restart publishes the real Usage rows. A browser-capable worker
should inspect the top bar, hover detail, reader settings, board states and reset
recovery on a copy. A valid Codex inventory is needed for a real quota read.

## Earlier draft record (historical)

Source and world files are in worker/a6646. Nothing is applied live, committed,
or marked ready. The sandbox cannot merge main or run the required painter.

The draft adds native Usage facts, separate from existing context-token readings.
Claude stream quota observations and Codex's read-only account/rateLimits/read
feed one row per reported window, with observation time and source. Publication
runs on resident and worker result events; the existing house pass expires old
readings. No new polling process. Restart seeds Claude from the existing usage
metadata parser, preserving its original timestamp.

Plan state and provider notice episodes persist in house-state/<world>/plan-usage.json.
Limit pauses preserve existing pending-message/session/worktree recovery.
Known exhausted windows determine reset + 60 seconds; absent reset means a
five-minute retry. Provider cooldowns cover new starts and disposable resumes.
Cards/corners carry usage_state; the board draft displays it. A retry shows
Resuming, and the one resume notify follows a successful model result, never
just a successful stdin write. A durable notice outbox checks the native
notification record after a lost acknowledgement before retrying. Existing
Claude-to-Codex handoff remains in place.

The house's claude_start_threshold accepts a percentage or off (default).
Only new Claude worker starts are deferred; queued cards remain asked.
The Usage reader offers Off / 70% / 90% buttons on the house settings note.
No account settings or credentials are read or changed.

World half: apply.py generates lines only after checking the current glance
and board passages. It installs an independent light style, a slot=bar widget,
a source/age reader, a glance line and a board usage_state label. A distinct
usage_available flag avoids the lens numeric-versus-empty-string trap.
Usage placeholder rows are retained as facts but hidden once real windows arrive.

Ran:

- test_plan_usage.py: 14 tests, OK. Fake quota thresholds, expired unknowns,
  Codex metadata sanitation, two providers, restart dedup, native facts, scene
  roles, resident unanswered-turn retention, worker pause, real disposable
  resume gate at reset + 60, success-only resume notice, and completed-turn
  survival when usage publication fails, lost notice acknowledgements and
  rejected notice retry. State-file writes are mocked. The initial fixture
  counted notify emissions without having the native verb: corrected to seed
  the real notify verb/chat, reject MISS, and verify native acknowledgements.
- verify.py frontier-try against live house metadata: copy e12913,
  12898 events. Five affected lenses current. Latest read: Claude 29% five-hour
  (20 Oct 17:10 reset), 14% weekly (26 Oct 15:00), as of 20 Oct 12:37.
  Native copy with two cards: one limit notify, one resume notify, states cleared.
  This is an in-memory copy, not a window check or a running-house playtest.
- test_usage.py: all passed (21 printed ok checks).
- test_transport.py: 4 passed, 1 setup error (Temp directory denied).
- health.check_python: no failures. Own style: 1 read,
  0 properties the painter draws nothing for.
- git diff --check: clean before final handoff edits.

Blocked, without bypass:

- screen.py frontier-try at 2560x1440, scale 1.5: WinError 5 creating
  Temp/screen-door-.../desk-shell, before Chrome. No shot or facts inspected.
- test_builders.py: WinError 5 creating Temp/.../house-state.
- read_plan_usage.py: pinned adapter catalog validation stopped before service
  contact (worker-model-catalog.json bytes missing or mismatched). Codex real
  account numbers are unverified; its row says unavailable.
- git merge main: ORIG_HEAD.lock Permission denied. HEAD remains 82e3528;
  main has a6452 at 433bcf6. New Markdown files do not overlap source edits here,
  but the draft must be merged and checked on that version before landing.
- Pytest left two inaccessible pytest-cache-files-* scratch directories at the
  worktree root. Git status warns about them; they are not task content.

Read primary sources:

- https://code.claude.com/docs/en/statusline — subscriber five-hour/seven-day
  used_percentage and epoch resets_at; fields can be absent.
- https://learn.chatgpt.com/docs/app-server — ChatGPT account/rateLimits/read,
  primary/secondary windows and multi-bucket response, usedPercent and resetsAt.
- Installed openai_codex generated schema and client.request signature.

Before landing/activation:

1. Reviewer checks lifecycle paths and unknown/reset semantics. No real model
   trial has been run or authorized by this card.
2. Host merges main and reruns ordinary checks. Builder and transport fixture
   checks still need a writable sandbox. Full health was not run here.
3. Run the sandbox painter and inspect top-row gauge, hover, settings press,
   glance, board paused/resuming/cleared states, and one notice per provider
   episode. Need a running-house fake-feed playtest, not just scene compilation.
4. Run the read-only Codex quota probe with its valid pinned inventory. Do not
   bypass the pin or change account settings.
5. Update Handbook a639 (Commissions workers keeper) through exact read/replace:
   add claude_start_threshold; native Usage row fields; usage_state and paused
   resident status; durable provider notice episodes and reset + 60 behavior.
   Current Implementation.md has not been edited.
6. After source landing and successful copy checks, use Desk MCP to apply the
   checked lines. Never use a shell localhost request as the Desk route.

Rough spots note a6662 records the missing world word. Notebook entry added at
e12911 under The desk from code: quota units differ; SDK params=None is explicit;
expired readings are unknown.
