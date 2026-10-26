# Painter rough spots and source boundary

Builder draft for Claude's review, 24 October 2026. No git state changed.

Small general kernel additions in `kernel/words.py`:

* `component`: the missing steward word for reviewing inline component bytes;
  `reviewed_code` is reserved so ordinary `set` cannot forge review.
* `look-view`: the missing data-only description word for arrangements and facts.
* `components` and `help <component>`: the missing discoverability words/cards.

Their implementations live in `painter/arrangement.py`. The stopped run had
already added `component`, `look-view` and the reserved hash; this run finishes
and tests them. Existing grant/undo scope edits in `kernel.py` and `words.py`
belong to the pixel-guy builder and are preserved. No edits to kd_guy.py, sprite.py,
the old lens painter, git index, branches or history.

The painter runs through the existing guarded widget host. No native desktop
code changes are needed to serve inline world modules. Live verification found
that `window.open`/`window.focus` said "brought forward" even when Windows refused
keyboard activation and Chrome still occluded the requested board. A small
`kd_window.py` repair now checks actual activation, then raises the ordinary
requested window without activation if necessary. It never makes it topmost,
attaches input threads or synthesizes input. Four fault-path tests cover this
opening contract; native pixels must still establish the final visible result.
`widget_browser.py` also accepts optional test-only background-throttling flags;
its default host/runtime behaviour is unchanged.

Known boundaries to measure: components are trusted and can use ambient DOM;
cards/lanes are five app components above primitives; per-person state is an
owned world preference; rich text is a safe display subset and source editor;
virtualisation currently windows fixed-height arranged rows after binding, not
server-side pagination. Core focus defaults do not establish screen-reader QA.
The native shared Comment mechanism has not yet been attached to this painter.

New source is a proposed implementation until Claude reviews and adopts it.
Running scratch tests imports the candidate; it does not alter a resident/live
kernel. Live installation must verify that the running kernel answers the new
words before writing component definitions.

## 26 October: failure boundaries and missing editing words

Builder draft; Claude reviews/commits. No git state changed. Missing world-level
capabilities and the source seams that now supply them:

| Source | Missing word or capability |
| --- | --- |
| `kernel/words.py`, `painter/handles.py` | A part-style write that cannot paint must refuse atomically; exact alpha colours, CSS spacing shorthand and safe motion tokens. |
| `painter/arrangement.py` | Compact `look-view`, full `plan=yes`, node-local validation, display labels/formatters, personal modifiers and declarative event/fact motion. |
| `painter/health.py`, kernel dispatch | `component-health`, `component-action`, private viewer reports and happening targets, revision-checked previous-version recovery, steward-only quarantine clear; `personal-view`/`personal-style` shortcuts. |
| `painter/isolation.js`, `painter/painter.js` | One component's stopped card, callback ownership, stale last-good DOM, timing and observed text/computed styles. |
| `painter/quarantine.js` | A terminable execution thread for a looping part; bounded DOM/control vocabulary when sandboxed sibling frames share a renderer. |
| `painter/install.py` | Install the new painter support and explicit health/control/hear grants; publish the updated guide. |
| `components/{card,lane,catalogue}.js` | Visible display values independent of domain settings. No component-specific kernel word was added. |
| desktop `pages/widget-host.js`, `widgets.py` | A trusted parent's phase/heartbeat watchdog that can record quarantine while its painter thread is frozen; blob Workers inherit the existing no-network CSP. |
| desktop `widget_guard.py` | Renderer failure recovery and a native ownership check before terminating a hung renderer. No PID comes from JavaScript, no shared renderer is killed, and opaque frames have no native recovery authority. |
| `painter/process_gate.py` | Remove the old full-screen-browser exception; both games and full-screen foreground programs block live steps. |
| `painter/browser.py`, proofs, desktop native test | Updated explicit plan contract and hidden/native acceptance seams. Hidden native pointer tests cannot await stopped compositor frames. |
| kernel building guide, ARRANGEMENT.md, ISOLATION.md | Agent-discoverable handles and a precise separation between projected structure, reported paint, native liveness and live adoption. |

The first in-page loop needs external recovery and can pause that view. Worker
quarantine is a thread boundary, not process-memory isolation; arbitrary browser
APIs are not emulated. See ISOLATION.md for the measurements, test outputs,
initial cold-model proof failure, and live adoption status.
