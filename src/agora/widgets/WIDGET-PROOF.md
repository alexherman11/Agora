# Widget builder handoff

24 October 2026. Built for Claude's review and commit. No `git add`, commit, push, checkout, branch, worktree or other git state command was run.

**Ran, pinned Python:**

```text
python -m pytest -q src/agora/tests
79 passed, 30 subtests passed in 109.00s (0:01:49)

python src/agora/widgets/proof.py
23 of 23 widget checks passed

Native window widget sandbox: 10/10 checks passed
Native nested bar widget sandbox: 10/10 checks passed

python -m unittest test_kdesk test_sysread test_stream_windows test_widgets test_widget_native test_widget_overlay
Ran 42 tests in 158.795s
OK
15 hidden Chromium windows; native SSE on 15 origins; Lines help: 18.5 ms (<1000 ms); world delivery: 15/15

python -m unittest test_widget_overlay -v
OVERLAY: real Chromium -> 300x252 RGBA -> invisible native sink; visible alpha; desktop y=1774
Ran 1 test in 7.250s
OK
```

The short widget proof uses a fresh scratch desktop, real modules and HTTP, a real mouse drag and a stale competing write. Hostile code tries fetch, cookie access, localStorage, top navigation and an ungranted pin. Off releases its lease immediately and destroys the frame. Principal tests cover per-instance observations, viewer rights, scoped writes, authorship, revocation, a fresh instance after undo, guarded-host admission, kit authority exclusion, and off/undo of an actual window intention. The WebView2 tests run **never-shown** windows, including the nested sandbox in a bar; they verify that a self-navigation request does not reach the scratch HTTP server. The native API positive control succeeds from trusted chrome while the frame's message is not delivered.

The offscreen pipeline test additionally runs the production Chromium/capture loop and checks multiple nonempty RGBA frames in an invisible sink. It rejects an opaque rectangle behind the companion. Its first version caught the readiness-object/boolean bug that the simpler page proof missed. Native pixel inspection caught the post-navigation background setting; the startup source now reapplies alpha after the widget document loads. Chromium uses a temporary private profile, prefers installed Chrome and falls back to private Edge, and owns an explicit target rather than whichever startup page appears first.

**Ran, all kernel proofs:**

| Proof | Printed result |
| --- | --- |
| `byo_agent.py` | `25 of 25 checks passed` |
| `council_night.py` | `21 of 21 checks passed · 144 records` |
| `hidden_hunt.py` | `16 of 16 checks passed · 57 records` |
| `kits.py` | `21 of 21 checks passed` |
| `web_host.py` | `20 checks passed` |
| `local_model.py` | `LOCAL MODEL: 27/27 checks passed` |

The real model proof completed as short local checks after the gaming gate cleared. Its inference results are functional evidence, not a factual-reliability evaluation. This builder did not edit the model module or taskboard app source.

**Ran live:** Rocket League initially ran, so all work stayed in scratch worlds and hidden software rendering. The process inventory and full-screen gate were checked before live effects. After the gate cleared, `deploy.py` saved the taskboard baseline, restarted the desktop, registered the existing summarize module and ran the idempotent v2 installer without reseeding. It then installed the widget definitions and opened the requested windows. The v2 verifier reports 25 cards, all 25 original identities/facts/history prefixes preserved; task-only summarize grants, undo metadata, repeat installation and v2 painter/style checks pass. Live task summaries are explicitly labelled literal fallback; the independent model module remains the other builder/coordinator's installation responsibility.

**Correction / deployment boundary:** the requested single-restart target was missed. The first live deployment exposed renderer bugs despite the page proof passing. One bounded recovery restart installed the readiness, DPI, private-target and native handle fixes. A live supported CDP background/viewport setting was reapplied after navigation; no further desktop restart was used. Its same setting is in the startup source for subsequent starts. Subsequent browser cleanup handling adds retry for Windows' transient profile/port locks; it does not change the running renderer's authority or display.

**Looked at actual native pixels:** [live desktop](evidence/live-desktop.png), [live bar](evidence/live-bar.png). Both board windows are arranged side by side in the same live world, with Guy studio alongside them. Existing user windows can cover them; they were not closed, rearranged or forcibly displaced. The live companion is visible over real window tops with transparent space around it; the media pill shows the actual Windows session's song/artwork and reported progress. The editor's live profile edits were retained. The Python guy remains available as fallback and word provider.

**Looked at hidden captures:** [JS board](evidence/taskboard-js.png), [card menu](evidence/taskboard-menu.png), [notes/history editor](evidence/taskboard-editor.png), [Guy studio](evidence/guy-editor.png), [alpha overlay](evidence/guy-overlay.png), [media pill fixture](evidence/now-playing.png). The pill's scratch album image/song are a labelled visual fixture, not live media evidence.

Off: `off taskboard-js`, `off guy-editor`, `off now-playing`, `off desktop-guy`. The Python fallback returns when the JS overlay lease ends; `off guy` stops that fallback too. Undo restores an activation with a new page instance. The existing **Agora desktop off** control stops the whole desktop.

Not proved: hard CPU/memory quotas; immediate visual teardown of an infinite-looping renderer; multiple monitors; portable website/phone mounting; or elimination of deception by widget content. SES was considered but not added. See [the contract and source-friction ledger](WIDGETS.md).

**Final live readback:** 26 cards including this builder's Done card; the v2 verifier again confirms all 25 original identities, facts and history prefixes. The JS companion and Guy studio have since been switched **off** in the live world. This builder left those off switches intact. The Python guy is active; the JS board, v2 lens board and now-playing pill remain live. Earlier screenshots record the requested JS companion/editor demonstration, not their final on/off state. `evidence/live.json` records the final holds.
