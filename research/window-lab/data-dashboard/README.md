# Reusable data graphics and the Crew observatory

Local terminal revision, 22 October 2026. These are Agora lenses, world style roles,
and one source module. No new frontend or painter. No house restart required
to use the separate preview.

The revised observatory is a quiet, light terminal-style panel: 12px monospace,
square rectangular bars, compact resident rows and two-line active-worker rows.
It fits the observed seven residents and two active workers in a 480x640 viewport.
Per-person context remains separate from account quota; names/tasks open ordinary
evidence folds, and inactive workers and secondary explanations start collapsed.
Studio keeps its original visual style and demonstrates a different use of the
same chart transform. This remains a local preview, not an installed live desk lens.

Open while the preview is running:

- [Crew observatory](http://127.0.0.1:8896/lens.html?lens=observatory&inspect=0)
- [Studio exhibition example](http://127.0.0.1:8896/lens.html?lens=studio&inspect=0)

Run from the canonical checkout with the pinned interpreter:

```powershell
& C:/Projects/Agora4/.venv/Scripts/python.exe -B research/window-lab/data-dashboard/preview.py --port 8896
```

Ctrl+C stops only this preview. It binds loopback only. There is no model call,
session pickle load/save, house restart, provider/queue change, or writable desk
API. The two examples are seeded into an ephemeral in-memory Desk using normal
world commands; the existing scene compiler, style generator and browser painter
render them. The preview polls published data every 15 seconds and names/queue
at most once a minute. A new preview process discovers the new source module;
an already-running production process does not gain it until a coordinated reload.
These example lenses have not been installed into Alex's live world.

## Foundation

**Read:** Board note “Building together: the stream as a room, Agora as a medium”
(21 October, discussion draft; a9341) and JEFF's c10248 response, plus live charter
a6529. The note is context, not an approved design or commission. The concrete
missing word was a bounded numeric transform: turn author-supplied rows into
scaled pictures **and inspectable words**. Existing picture, roles, pulse, folds,
grids, row sources and host-window gestures already cover the other needs.

Only new files are owned here. No changes to scene.py, lens_ir.py, lens.js,
house.py, workshop.py, provider/queue code, home-chat, or shared design documents.

## Author a chart

Create an ordinary note whose text is JSON, then repeat `charts:<note>` in a lens:

```json
{
  "title": "Materials",
  "mode": "stack",
  "unit": "sheets",
  "basis": "counted inventory",
  "maximum": 120,
  "records": [
    {"label": "Posters", "value": 42, "role": "chart.teal"},
    {"label": "Programs", "value": 28, "role": "chart.blue"},
    {"label": "Uncounted", "value": null}
  ]
}
```

```text
root : column
  chart : column
    of charts:<your-note> as g
    each graphic
graphic : column
  picture : text "$g.picture"
    picture
  words : text "$g.summary"
  evidence : column
    fold "Data & scale"
    body : text "$g.detail"
```

The placeholders in the two supplied `.lens` files are replaced with the actual
notes by `preview.build()`. The same lens words work with ordinary world notes.

Modes are `bars`, `stack` and `line`. A line can be a small sparkline or a larger
time series. Supply strictly increasing numeric `x` and `x_unit` for uneven time
spacing; otherwise it uses sample order. Missing samples break the line. No
smoothing or interpolation. `maximum` supplies a fixed positive scale, not a
guess at capacity. Without it the graphic scales to observed values and says so.
Stack remainder is “unassigned”, never assumed free.

`charts:<note>/marks` exposes individual bar pictures plus normal text labels
and values, allowing the author to choose spacing and typography at small sizes.
Returned fields: `item`, `title`, `summary`, `detail`, `picture`, `status`,
`count`, `known`, and, for marks, `label`, `value_text`.

Optional `corner_radius` (0..4, default 3) controls both full bar/stack and compact
mark rectangles. `0` sets both SVG `rx` and `ry` to zero, including tracks.
Optional `mark_height` (4..64 SVG units, default 10) controls compact marks;
narrow context cells use 28 so their bars remain legible. Defaults are compatible
with the original Studio. Geometry errors remain errors even if `state` is stale.
Compact picture accessible titles include their status as well as value/unit/basis.

Instead of inline records, a note may name any existing non-chart row source:

```json
{"title":"Reported context","mode":"bars","unit":"tokens",
 "basis":"last provider report","source":"witnessed:usage kind=agent",
 "fields":{"label":"actor","value":"tokens"}}
```

Field mapping supports `label`, `value`, `role` and optional `x`. Row selection
is handled by the existing source grammar. Recursive chart sources are refused.
An empty external source is **unknown**: this contract cannot distinguish a real
empty dataset from an unavailable producer. Inline `records: []` is **empty**.

Optional `state` is `stale`, `error` or `unknown`; `note` explains it; `as_of`
states the actual observation time. The function never invents a timestamp.
Maximum 160 records, 100,000 configuration characters, 240 characters per label;
larger record sets need an explicit author-chosen aggregate. Values must be
finite and at most 1e15 in magnitude. Negative bar/stack values and values above
an explicit maximum withhold the plot with a visible error. Labels are escaped,
colors come only from role names, and SVG contains no scripts, URLs or callbacks.
Full long labels within the bound are retained in words and compact bar rows;
the full SVG's plotted labels are shortened to fit.

## What the examples know

The observatory reads the existing house status, witnessed usage and account
quota publications. It displays:

- Resident names and all reported active workers; inactive entries are folded. Fold names
  for reported status, alive flag, provider/model evidence, turns and age.
- Last reported context tokens divided by reported capacity. This is a derived
  percentage of reported totals, not cumulative use or a semantic breakdown.
- Account-wide quota percentages, observation times and reset times in UTC.
  Expired windows become unknown. This is not billing or per-worker usage.
- Queue cards whose commission is `asked`, from a read-only desk selection.

Unknown provider/model fields stay unknown. A fallback model is prefixed **~**
(the header explains "~ last model")
because an older usage observation does not prove the current configuration.
Reported activity does not establish process health. House heartbeat older than
60 seconds is labeled stale. Token measurement age is unavailable even when the
publication is fresh. Internal context composition, hidden model thinking,
cumulative token spend, billing and elapsed durations are unavailable. There are
no invented slices or fabricated usage histories. Private `said` text is never
rendered or exported. The Studio example is explicitly illustrative planning
data; it demonstrates segmented allocation, legends, time gaps, zero, unknown,
and empty observations using the same transform and renderer.

## Evidence and limits

**Ran, terminal revision:** 23 generic-graphics tests and 9 preview tests pass
(32 total); both lenses compile with the edge-case fixture. Added checks cover
square geometry including zero/full/unknown, default compatibility, invalid
geometry under stale state, accessible stale labels, per-person chart binding,
separation of unknown worker context from full account quota, and privacy-safe
telemetry whitelisting. Earlier repeated-update and stable-identity tests remain.

**Ran, actual hidden browser:** live view at 480x640 and 640x600; no horizontal
overflow (paint widths 480/480 and 640/640). Seven residents plus two active
workers/tasks and account quotas fit. Click opened Jeff's evidence and Enter
closed it. The synthetic fixture at 640x640 shows seven residents and four active
workers simultaneously, with zero, unknown, full and stale states. A long task
opens its complete text; expanded evidence scrolls vertically without horizontal
overflow (625/625). Inactive worker disclosure works. Every rendered terminal bar
has rx=0 and ry=0. Resting panel computed animation names are empty. Studio was
rechecked at 900x700 and preserves default 3px corners and its illustrative data.

New revision viewport captures are `evidence/terminal-v2-live-480.jpg`,
`terminal-v2-live-640.jpg`, and `terminal-v2-edge-cases-640.jpg`. Old screenshots
and their Library identities remain unchanged. New Library saving failed before
preparation with "Library prepare_uploads is not available"; no new Library IDs
were issued. See `terminal-v2-library-manifest.json` for local paths and status.

The terminal panel requests no continuous animation. Native fold transitions
reuse the existing reduced-motion-aware styles. The browser has no media
emulation capability, so a real reduced-motion preference was not emulated.

**Correction to the initial regression attribution below:** the architecture
worker isolated a global row-source field collision with world property `status`.
Disabling charts alone was inconclusive while modules remained loaded. It owns
the narrow scene/lens_ir fix and regression; this task makes no core edits or
whole-suite pass claim. The original observation is retained as history.

Fixture run (synthetic only; choose an unused local port):

```powershell
& .venv/Scripts/python.exe -B research/window-lab/data-dashboard/preview.py --port 8898 --fixture research/window-lab/data-dashboard/terminal-edge-cases.json
```

### Initial version evidence (retained)

**Ran:** 19 generic-graphics tests and 6 preview tests pass. Tests include
same-row-count source changes through the actual compiler, 15 repeated config
edits, stable person identity as worker selection changes, missing/zero/large
values, malformed inputs, long labels, safe SVG, stale/missing telemetry and
expired quota. Both example lenses compile. Commands:

```powershell
& .venv/Scripts/python.exe -B research/text-desk-lab/notation/test_data_graphics.py
& .venv/Scripts/python.exe -B research/window-lab/data-dashboard/test_preview.py
& .venv/Scripts/python.exe -B research/window-lab/data-dashboard/preview.py --check
```

**Ran:** hidden in-app browser inspection of both actual rendered lenses,
clicking Jeff's evidence fold, repeated live updates, and viewport widths 1280,
680 and 380. Paint scroll width equaled client width at compact widths. Captures
are under `evidence/`; these are viewport captures because Agora scrolls its
paint panel internally, so additional lower-panel screenshots are supplied.

**Read and inspected in DOM:** the existing pulse uses a 2.5-second cycle;
keyframes are gated by `prefers-reduced-motion: no-preference`. The browser tool
does not expose media emulation, so actual reduced-preference rendering was not
tested. Standard keyboard-accessible folds and text remain available; color is
never the sole data label. Small full-SVG labels scale with the plot; the bar-row
variant keeps its normal text size, and Data & scale gives normal text details.

**Ran, existing regression limitation:** test_scene.py passed its first 32 tests
then failed `test_freshness_words_are_host_reads` at line 845 (`$changed.status`
was empty). The same test fails with the new charts source removed from both
registries in memory. This task does not fix or claim ownership of that code.

The existing `host window` navigation gesture was exercised but did not produce
a second tab in the hidden IAB; use the verified direct links above. No native
Windows paint/held-action fence test or live installation was attempted. This
preview has no data-mutating actions and only chart-note identity, not individual
plot-point actions. It is not evidence of a new plugin security boundary.

**Architecture critique, imagined next experiment:** a third unrelated chart
should require only authored configuration if the numeric transforms suffice.
For an unseen transform, try the existing source-module seam against frozen core
hashes before inventing a registry. Trusted Python sources still receive a full
mutable Desk; declared dependencies, immutable reads, producer status and module
version ownership are future contracts, not guarantees supplied here. Keep any
effects as typed host-admitted requests, not rendering callbacks.
