# Magnetic preview: prepared, default-off source checkpoint

22 October 2026, worker-a8588 (Codex builder-2). This supersedes the
always-on activation and landing instructions in MAGNETIC-PREVIEW.md.
That file and SOURCE.patch retain the original design and historical evidence.
No live world change, native launch, restart or activation occurred.

## Preparation and source inventory

Read house receipt a8588-e29444: checkpoint a3916623f052eceead86fe4a57dbbc047f8c0dd4,
prepared HEAD c6a49251a12d25ae8f51f2f7e16b90384d1f2375,
captured main 09ef2530ec848cbbcf0afc5d0934737095c3cc69, clean merge.
Ran verification of all eight checkpoint committed-file hashes: 8/8 match.
The two differing raw/committed manifest representations in the receipt are
kept as recorded, not silently equated.

Production delta against that main is exactly scene.py, partition.js and
partition-ui.js. No lens.js, viewer.js, house, runtime, selection or window
store edit. Their prepared-main bytes are preserved; pending peer changes
still require explicit reviewed composition, not an assumed integration.

The lens word is:

    partition <prop> min <width> <height> gap <pixels> [focus <prop>] [magnetic]

Only an explicit final `magnetic` enables neighbor preview, frozen snap
targets/hysteresis, strict feasible-plan fallback and continuity restoration.
Absent option emits the old painter spec exactly, without a false-valued
extra property. Only Boolean true enables the adapter; malformed strings or
numeric truthy values do not. Existing pointer, keyboard, receiver and refresh
behavior remains on the default path. No live lens asks for this new option.

The production-only exact patch is MAGNETIC-OPT-IN.patch. Exact hashes and
receipt provenance are in MAGNETIC-OPT-IN-HASHES.json. Historical SOURCE.patch
is not the current landing patch.

## Ran on the prepared tree

All commands used this worktree and disposable in-memory/DOM fixtures:

| Check | Printed result |
|---|---|
| test_partition_ui.js, explicitly magnetic | 347 partition DOM gesture checks passed |
| test_magnetic_preview.js | 104 magnetic preview geometry checks passed |
| test_partition.js | 167 partition geometry/model checks passed |
| test_pointer.js | 12 divider pointer/keyboard/fence scenarios passed |
| test_navigation.py | Ran 10 tests, OK |
| test_partition_magnetic.py | 3 passed |
| test_magnetic_optout.js | 12 captured-main/off-path byte-identical DOM/command traces passed |

The differential test compares complete serialized DOM/preview/tool state,
commands, holds, busy state, refresh calls and selection clearing at each
gesture stage. It covers absent/false/string/numeric settings with pointer,
keyboard and cancel. Baseline fixtures are exact captured-main git blobs,
verified with hash-object, not rewritten approximations.

The compiler check compares absent and explicit painter options, preserves
read fences, and confirms zero events in its in-memory world. Definition
hashes necessarily change when the authored option changes; tests require
that difference, not suppress its freshness protection.

Development iterations failed on a wrong parse-root lookup and an overbroad
definition-hash equality assertion; corrected tests now check actual renderer
contracts. A child-process git lookup in the first differential harness was
refused (spawnSync git EPERM); the final harness uses explicit captured source
fixtures and starts no child process. An initial VM setup lacked document/
ResizeObserver; evaluating the real modules inside each isolated VM fixed
that harness error. These are not claimed product regression failures.

No broad health, browser, real frame/drop timing, screenshots, native caret,
iframe/media continuity or live world gesture was run. Prior CPU samples and
browser timings in MAGNETIC-PREVIEW.md remain historical, not new measurements.
No latency gain or painted acceptance is established by these doubles.

## Scoped world/documentation stage and rollback

World authors may append ` magnetic` to one freshly read partition line only
after source acceptance and their activation decision. Keep its current
property, minima, gap and focus property unchanged; do not copy an old entire
home-tiling lens. Reverse only that suffix to return that lens to the old
path. Preserve tree, pins, shelves, extents, music, selection and chat state.
This is a recipe, not an applied world patch.

For the Handbook's partition grammar, stage the optional final `[magnetic]`
and the sentence: "magnetic previews the candidate allocation of neighboring
panels during pointer or keyboard carry; absent means the existing drop-box
preview." Re-read its exact current passage before scoped replacement.

Source rollback is one revert of the eventual house landing commit, after
checking later edits, with all authored options off. There is no world schema
migration or layout reset. Leaving the option off already selects old behavior.

## Remaining gates

Sable c11240 authorizes ordinary default-off source judging before paint.
Current card waiting_on=a11327 remains: live module/crew lenses depend on
source absent from committed main. Read its current transfer state at e29857;
not landed. Do not repeatedly ready against that known incompatibility or
remove the lenses. Resume judging after its actual landing and a compatibility
check; new main conflicts return through the supported house process.

Guarded copy acceptance still needs the admitted shared paint lane, actual
2560x1440 and 1280x800 CSS viewports at DPR 1.5, both option-off and explicitly
enabled lenses, native draft/caret and media preservation, edges/tab fallback,
external dock, cancellation/refusal/new-scene convergence and measured preview
frame/pickup/drop times. Use the detailed journeys in MAGNETIC-PREVIEW.md,
with the option enabled on the copy only and current reviewed hot-file hunks
composed by exact scope. No native attempt or live apply is authorized here.

## Exact scratch exclusion and judging handoff, 22 October

Codex-builder-1 resumed under JEFF c11649 and Sable c11668. Added only the
anchored `.gitignore` entry `/pytest-cache-files-vc77xj4l/`; the directory is
retained untouched. `git check-ignore -v` confirms this exact rule for the
root and a synthetic child path. No broad cache pattern or permission change.

The staging dry-run was NOT successful: after correcting PowerShell pathspec
quoting, Git refused creating the worktree index.lock (Permission denied).
No staging workaround was used. Read-only inventory instead used the house's
same sessions-excluding pathspec with `git ls-files --others --exclude-standard`,
plus `git diff --name-only HEAD` and `git diff --cached --name-only`.
All three succeeded; the cached diff is empty. Prospective new/modified files:

- .gitignore
- src/text-desk/notation/desk-shell/partition-ui.js
- src/text-desk/notation/scene.py
- src/text-desk/notation/test_partition_magnetic.py
- src/desktop/hud-dividers/test_partition_ui.js
- src/desktop/hud-dividers/test_magnetic_optout.js
- src/desktop/hud-dividers/MAGNETIC-OPT-IN.md
- src/desktop/hud-dividers/MAGNETIC-OPT-IN-HASHES.json
- src/desktop/hud-dividers/MAGNETIC-OPT-IN.patch
- src/desktop/hud-dividers/magnetic-baseline/README.md
- src/desktop/hud-dividers/magnetic-baseline/partition.js
- src/desktop/hud-dividers/magnetic-baseline/partition-ui.js

No cache/session path occurs in that inventory. Existing checkpoint a391662
also supplies the original eight preserved files (including partition.js,
historical evidence/patch and geometry tests); they were not discarded.
All nine opt-in manifest hashes still match, including production and captured
baseline bytes. House must perform the actual source checkpoint and staging;
these read-only checks are a prospective inventory, not a completed commit.

RAN again: 347 DOM gesture checks; 104 magnetic geometry checks; 167 model
checks; 12 pointer/keyboard/fence scenarios; 12 byte-identical option-off traces;
10 navigation tests in 0.105s; compiler 3 passed in 0.18s with cache provider
disabled; diff-check passed. Current-main comparison shows no partition model/UI
drift; scene.py has only main's separate lexical row-field correction, disjoint
from this parser suffix. The house's merged-result judgment remains required.
No production edit was needed this round. Ordinary default-off source judging
is authorized; painted acceptance, native continuity and timings remain owed.
No world activation or latency improvement claimed. Rollback remains one revert,
and removing the authored option returns its lens to the default path.
