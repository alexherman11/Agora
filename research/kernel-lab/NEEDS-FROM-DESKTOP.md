# Kernel word handoff to the desktop builder

Builder note, 24 October 2026. **Read:** `research/window-lab/kernel-desktop/kd_media.py`, `Media.offer`. No file in that folder was changed, and no live desktop was restarted or installed by this builder.

The kernel already accepts an offer's `undo`, and now provides steward-held `word-set` to edit an existing entry. Please declare `"undo": "external"` on **media.play**, **media.next** and **media.prev** in `Media.offer()`. Keep **media.now** a see word (`undo: no`, or omit it). For example:

```python
{"word": "media.play", "kind": "do", "takes": "", "may": "anyone",
 "undo": "external", "help": "media.play: play or pause …"}
```

The current call answers already return `external: true`. Keep that declaration too: the offer describes the word before anyone runs it, and the answer describes the particular effect. The kernel now records a do entry marked `undo=external` as external even if its answer omits the flag, including within mixed compositions. Undo refuses the effect record.

**Existing entries are intentionally never overwritten by re-offer.** After adopting the reviewed kernel, use the ordinary steward door to read each existing media entry and say `word-set <entry> undo=external` with that look's fence. Use rows/help to resolve the actual entries; do not assume historical ids. Adding the offer fields alone fixes fresh worlds, not the metadata of an existing world.

The new painter fills `$carried`, checks both participants' observations, supplies `history:<thing>`, `$today`, `$made_at` and `$changed_at` (the explicit names avoid the compiler's reserved `$changed` event frame). The word-only board now uses bare `task-add`, `task-move`, `task-assign`, `task-done`, `task-note`, raw history and its Done rule. Dotted names remain for module implementations. No host-side task logic is needed. The old installed board is not migrated by this source change; review/adopt the updated definitions separately while preserving its cards. Native window visibility and the quoted `window.open` issue remain with the desktop builder (the earlier observations are in the board's NEEDS).

**Ran:** scratch task board `21 of 21 checks passed`, including actual headless lens.js drags, successful-first/stale-second. This does not establish live desktop adoption or native-window visibility.
