# Adding a HUD playtest step

Add **one uniquely named `.py` file here**. Do not edit `hud_playtest.py` or
a registration list. Public `.py` files must export `STEP`; files beginning
with `_` are shared support, not steps. The runner sorts by `(order, name)`.
Existing orders are 100 apart; use a number between neighboring steps.
Equal orders are allowed and sort by name, so simultaneous additions merge.

```python
from playtest_steps import Step
from playtest_steps._support import press


def bind(play, opened):
    async def check():
        play.needs("your-card", "feature description", ("lens-name", "feature text"))
        return await play.timed(
            "!!pt.leaf('Done', pt.part('lens:your-lens'))",
            press(play, "pt.leaf('Start', pt.part('lens:your-lens'))", "Start"),
        )
    return check


STEP = Step(
    name="unique_name",
    description="press Start and see Done",
    order=2450,
    needs=(("your-card", "feature description"),),
    script=bind,
    assertion="Done appears after Start",
    budget=(100, 300),
)
```

`bind(play, opened)` returns a no-argument callback returning an awaitable. `play` is the same
runner/copy/window as before; `opened` is the first-paint result. The press
script keeps its assertions together with each press (including intermediate
assertions and `play.timed` predicates). `assertion` describes that condition;
it is not a second assertion executed later. `needs` describes dependencies
for `--list`; keep `play.needs` inside the callback so conditional probes,
`--assume`, missing-feature verdicts and skips retain their existing behavior.
Use `play` attributes for state intentionally passed between steps.

Migration from an in-flight branch: move the original `s_…` callback into
`bind`, returning it; put the old append tuple's id, description and budget
in `STEP`. Translate its position in the old order list into `order`.
Move helpers used only by this step into its file. Reuse `_support` for
existing shared fixtures; do not add a new shared registration. The seven
scroll callbacks are already individual files; `hud_scroll.steps` remains
a compatibility adapter.

Run `hud_playtest.py --list` and `test_playtest_steps.py`. For browser
acceptance run `hud_playtest.py --report none` on the same copied-world
snapshot before and after; compare ids, outcomes, scripts and budgets.
Milliseconds measure real presses and naturally vary. This refactor's
browser comparison was **not run in the Codex sandbox**. The captured
`playtest_steps_baseline.json` records 35 registrations and
AST hashes from main at 43e352b (including the equal-footing step that
landed during this extraction); the migration tests check those original bodies
without copying or changing their scripts. Adding a new step does not
require updating that historical baseline. An intentional change to an old
script should explicitly update its baseline entry.
