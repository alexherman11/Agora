# Lines dock launch repair — 27 October 2026

Codex Lines dock worker, for integration coordinator. Board: Lines terminal fails to open from the bottom dock.

## Read and ran: cause

Live `window.list` had no Lines window, but did have Jeff-chat. Live `wm.windows` gave Jeff-chat both an Agora id and a native key shaped `pid:creation-time:hwnd`. The dock used the icon classifier (`appOf`, matching `chat` to `lines`) to attach running windows to launchers. Thus the Lines launcher adopted Jeff-chat instead of opening Lines. Its action then passed the long native key to `window.focus`, whose `row_for` accepts the Agora id. This explains the large numeric identifier refusal from the source and observed state; the original on-screen error was not captured, and no live click was performed.

## Source repair

- `shell_parts/components/shell-dock.js`: associate launcher slots with the exact view named in the launch command, not the icon classifier. This also preserves explicit aliases such as taskboard → taskboard-components.
- `shell_parts/shell-kit.js`: use `w.agora` for Agora focus/minimise/close; retain native keys for WM actions and window identity.
- `pages/shell/shell.js`: same fixes in the fallback shell.
- `test_dock_launch.py`: real component UI in headless Edge, disposable kernel and mocked WM readings reflecting the observed mismatch; accepted open/focus/minimise/close receipts from the scratch window module, and preserved external WM routing.

## Ran: verification

Pinned interpreter, from `research/window-lab/kernel-desktop`:

```
python -m unittest test_dock_launch -v
Ran 1 test in 11.023s
OK
Dock: chat stays separate; Lines opens; native WM keys preserved; Agora focus/minimise/close accepted; external WM routing preserved.

python -m unittest test_shell_components -v
Ran 9 tests in 15.077s
OK
```

`git diff --check` passed (unrelated existing CRLF warnings). First test invocation used an incorrect destination path and failed import; corrected before the passing run. No visible test windows, live reload/restart, commit or push. No Lines-page, JEFF-lens, WM or House source edits. Pre-existing work was preserved.

## Activation handoff — not performed

The live shell stores component and widget code in the world; source edits alone do not activate this repair. Coordinator should review these shared shell hunks with the JEFF worker, update the shell-dock component from `cards.code('shell-dock')` through existing component review, and refresh shell-top/shell-dock widget code using `shell_install.shell_code()` / the supported installer. Preserve edited lens arrangements; do not pass `--reset-lenses`. The existing `shell_install.py --live` is the supported broad installer with gaming guard, but review other pending shell changes before using it. Its output explicitly says bars change when their pages next load. Coordinate any reload with active user work; no whole-kernel restart is inherently required by these JavaScript-only changes.

Live acceptance still needed: with chat open and Lines closed, click Lines; then confirm restore/minimise and close address Lines. The hidden test verifies source behavior, not live activation.

## Rough spots

Missing world-level distinction at this adapter boundary: launcher target identity versus visual icon family, and native WM key versus Agora window identity. All three source edits repair those mappings without adding kernel vocabulary. The regression supplies evidence for that boundary.

## Seabright Map follow-up — 27 October 2026

**Read / ran:** Alex reported the same opening problem for Seabright Map. Live map pin names `window.open seabright-map`; the existing map window shows `seabright-map`. Live WM reported it minimised with native key `106164:134376107497969028:60167110` and Agora id `dk880`. Thus its pin mapping is correct, but the same pre-repair action routing sends the wrong identifier. No distinct map mapping defect was found. No map data or additional production source changed.

**Ran:** expanded `python -m unittest test_dock_launch -v`: `Ran 2 tests in 9.772s`, `OK`. Real hidden dock: custom map pin opens the scratch map, separate Map/chat items focus their own Agora ids, Map closes; Lines/chat separation and Lines/external actions still pass. Live Map activation is not verified.

**Additional finding for window-host owner:** an earlier close-then-immediately-reopen scenario failed twice despite waiting until `window.list` omitted Map. A diagnostic rerun showed successful close followed by `Seabright-map is open already: brought forward (new=yes opens another)`, with no new window. Read: `window.list` filters current world records, whereas `window.open` searches cached `self.rows` until reconciliation. This is a distinct close/reopen cache race. The final test checks initial launch, focus and close independently; it does not claim this race is fixed. No `kd_window.py` changes made because that shared host needs owner coordination. Activation handoff above remains applicable to both Lines and Map.
