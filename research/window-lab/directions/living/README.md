# LAMPLIT: the HUD sprint's lane 3, the living system (a6057)

Round 3 (17 Oct), final and live-ready, NOT live. The desk lane (a5994) applies the three lanes in one pass.

**The final files**

- `lamplit.overrides`: the look. The rule is at its top: colour says whose move it is (warm = Alex's, jeff = a
  resident's, accent = an agent acting now, ink = chosen and every control), and so is the rule for a role added later.
- `home-glance.lens`, `home-house.lens`, `home-house-small.lens`, `home-timer.lens`, `home-timer-bar.lens`,
  `home-notices.lens`: the living parts, under the names they will have live.
- `apply.py`: puts them into a world. `check` reads only. `door` saves everything it replaces and writes `undo.desk` in
  `saved/<when>/` first. `undo <dir>` puts it all back. `undo-lines` gives a baseline for a copy. Its docstring says
  every step.
- `home-style.lamplit`: the one flat style `apply.py check --world live` would write, kept for review. It is made again
  at apply time from the live home-style, so it is never stale when applied.
- `shots/round3-*.png`: the three lanes in one light on a copy (busy, quiet, a glance number pressed).

**Superseded** (rounds 1 and 2; kept as the record, not used): `build.py`, `direction-living.style` and the
`direction-living-*.lens` files. The round-3 lenses are their successors, under live names.
