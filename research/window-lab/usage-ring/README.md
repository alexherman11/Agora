# Composer usage rings

Alex requested circular plan-usage indicators beside chat, hover details, and
removal of the header usage display on 20 October 2026.

The implementation uses native lenses and styles. `home-usage.lens` draws the
existing visible usage-window facts as 32-pixel SVG rings, with a 5h/7d label.
Hover or keyboard focus reveals provider, percentage, reset, observation time
and source. Activation opens the existing plan-usage reader. Missing readings
remain unavailable rather than becoming zero. Amber begins at 70%, red at 90%.

`apply.py WORLD` applies the change through the authenticated Desk interface,
re-reading shared notes before narrow edits and saving their exact prior text in
ignored `local/usage-ring/`. Its native IDs belong to this Frontier world. Run
with the repository's pinned `.venv/Scripts/python.exe`. The helper adds style
roles, puts the rings below the composer, and removes both header insertions.
It does not change the usage collector or require a service restart.

## Verification

Ran against a private native-world fork before live application:

- All three affected lenses compiled: home-usage, jeff-chat, home-base.
- Browser hover showed the full usage tooltip.
- Keyboard Tab reached the ring; Enter opened its details. A draft entered in
  the test copy survived that interaction. No test message was sent.
- The 360-pixel-wide composer and tooltip fit the viewport. The full home view
  had no horizontal overflow and no old header usage widgets.
- Changed-helper Ruff F/E9 checks passed.

Applied to Frontier at events e13465-e13471. A separate in-app browser then
visually confirmed three live rings below the composer. Screenshots and the
exact pre-change backup are under ignored `local/usage-ring/`. These are UI
checks; they do not test provider-limit exhaustion or automatic resumption.

## Prompt caching observation

Read existing production usage metadata on 20 October, without making a new
model call: a JEFF Claude response reported 710,186 cache-read input tokens,
769 cache-creation input tokens and 2 other input tokens. A Codex worker's last
usage event reported 152,832 cached input tokens out of 155,378 input tokens.
Both therefore showed actual prompt-cache hits in those samples. Cache hits
are separate from plan quota and context-window occupancy; the rings show plan
quota, not cache percentage. No cache configuration was changed.
