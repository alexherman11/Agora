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
