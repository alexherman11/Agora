# Magnetic preview: prepared source rejudging evidence

22 October 2026, codex-builder-1, worker-a8588.
Authority: Sable c12687; actual preparation c12810. Source judging only;
no world activation, native/browser launch or restart performed.

## Read

House prepared main c60a1423d252e94fdd26a2ea7a2d021b2e948d0a into this
branch at 77d41f495d14769f71e5c5a15fdef9d24b1850a0, clean merge.
Read the live charter, collaboration guide, full commission/comments,
prepared opt-in evidence and source diff. Tracked tree was clean on arrival;
only the house-supplied frontier-try session was untracked and was not read.

Observed newer main 8dbab71c8cb79f900fd9a26269b627eef9dadc29 includes the
browser continuation and its documentation. Diff of prepared main to that
main is empty for scene.py, partition.js, partition-ui.js, lens.js and viewer.js.
Diff of candidate to main is empty for lens.js and viewer.js: the accepted
race/selection work is preserved. Apparent browser-file deletions in a direct
main-to-candidate diff are newer main additions, not requested removals;
the house must preserve them during its ordinary merge.

Production changes remain only scene.py, partition.js and partition-ui.js.
The grammar is opt-in:

    partition <prop> min <w> <h> gap <pixels> [focus <prop>] [magnetic]

Absence retains the original path; only Boolean true enables the adapter.
No lens, structural tree, focus, pin, shelf, draft or world policy was changed.

## Ran on prepared source

| Command suffix | Printed result |
| --- | --- |
| test_partition_ui.js | 347 partition DOM gesture checks passed (stand-in; no browser) |
| test_magnetic_preview.js | 104 magnetic preview geometry checks passed (no browser) |
| test_partition.js | 167 partition geometry/model checks passed |
| test_magnetic_optout.js | 12 captured-main/off-path byte-identical DOM/command traces passed |
| test_pointer.js | 12 divider pointer/keyboard/fence scenarios passed (DOM stand-in; no window) |
| test_navigation.py | Ran 10 tests in 0.205s; OK |
| pytest -p no:cacheprovider test_partition_magnetic.py -q | 3 passed in 0.42s |
| test_repaint_races.js | 18 assertions passed (controlled doubles; no browser timing proof) |

JavaScript commands used Node. Python commands used the pinned repository
interpreter. node --check partition-ui.js and git diff --check exited 0.
No broad health run was performed here; house merged-result judging is next.
An initial inline Python hash-read command failed from PowerShell quoting
(NameError); corrected read-only invocation succeeded. No fixture failed.

## Hashes and inventory

Current SHA256:

- partition.js: 5f69b2c66407b31d693d4e5dcacd39623e8a5c6ff433f4c83b3bd453ba58c3a2
- partition-ui.js: 54b2617839a9bf6f7e1329071a424b44c0f75e056f614e654b4047ccd52e863f
- scene.py: 449c5135a109e604a4c2a6b3b51b3c76d5d380929414a6926a9aa051bb1e21ff
- historical MAGNETIC-OPT-IN.patch: 1a2aafb9183a22c2720069914fddfb61fa8121c5191a63061e1be1cd12b6c671

Eight of nine historical opt-in manifest hashes match. scene.py differs due
to current-main integration; its complete diff against prepared main was
read and contains only the reviewed magnetic parser/help/text additions.
The old patch and manifest remain immutable historical artifacts; they are
not substitutes for the house's current merged tree.

Read-only candidate inventory against prepared main contains 18 retained
source/test/evidence paths, plus this new evidence document. No cache/session
content occurs. Both exact retained scratch exclusions pass check-ignore:
/pytest-cache-files-vc77xj4l/ and /pytest-cache-files-pgxvchi0/.
No cache deletion, permission change, broad exclusion or Git index mutation.

## Limits, author action and rollback

What an author can express: opt a partition into reversible neighbor
allocation preview, with frozen snap targets and feasible tab fallback,
through the final magnetic word; ordinary lists/windows do not opt in.

No screenshots, real frame/pickup/drop latency, native caret/selection/media
continuity or visual quality have been measured in this round. All painted
acceptance at 1280 and 2560 remains owed through the shared guarded lane.
No latency gain claimed. Historical Twitch judgment and index-lock refusals
remain historical; no feature checks were disabled or relabelled as passes.

Rollback: one revert of the eventual landing after later-edit review.
Per-lens reversal removes only the magnetic suffix after a fresh read.
JEFF/Sable own activation after painted acceptance; no live world hunk applied.
