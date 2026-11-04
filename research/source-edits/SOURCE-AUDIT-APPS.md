# Source audit: modules, apps, painter, theme (26 Oct – 3 Nov 2026)

*Evidence for [[SOURCE-EDITS-AUDIT]]. Written by a read-only helper Claude started on 4 Nov; kept as it reported, lightly
trimmed. Labels: **read**, **ran**, **imagined**.*

Scope (ran): 69 non-merge commits in modules, apps, painter, components, theme, widgets, community-app, map-lab; 38 touch only
`modules/house` and are left to [[SOURCE-AUDIT-HOUSE]]. 31 remain, plus the merge 7b28433b0 (it carries fixes). Read: diffs;
`look dk1814`, `dk1813`, `dk1332`; the archived old world (things.jsonl, exports). Whether residents or Alex edit lenses live
could not be checked.

| commit | what | class | avoidable | how |
|---|---|---|---|---|
| 2c9db8213 dk1814 Music | music.lens, 2 components (79 lines JS), installer that edits `dock_apps` | C, P | partly | The catalogue already has image, progress, button, badge, column; or bring the old lenses a7030/a7028 (297 lines of world lens), which the kernel can still paint. Not logged |
| fbf90fb85 dk1813 card rules | 6 world rules, plus kernel `task.signal` (88 lines) and house.py +117 | B, C | yes/partly | The old rules were 7 world things (`when kind:task,prop:commission=landed do comment …`). The new `rule on=<word>` has no fan-out over a query and no notice word. The card said "log that in Rough spots"; not found |
| 4de378750 dk1614 Documents | documents.py: files.browse/folder/store/rename/move; 5 components; installer | B, C | partly | folder/rename/move are each one make/set plus checks: verbs with named arguments plus kind shapes. Logged, but says "no cross-lens include", already wrong |
| f2c7bc593 dk1500 calendar | `board.events` (joins RSVPs with names), kind `defaults=` inside board.py, calendar.js | B, U, P | partly | Related counts/names in a reading; kind defaults in the kernel. Logged well |
| 03e9f44f5 dk1499 Asks & offers | `board.asks` (status from `claim:*` facts); **lens nesting** `part : lens, name <x>` | U, B, C | partly | Computed fields in readings. Nesting is undocumented; Documents re-invented it four days later |
| 85cc06078 dk1530 map in board | view keys prefixed in JS; `'place'` hard-coded; a Python script adds a field to 9 kinds | B, P, C | partly | A component-local view scope; a kind aspect "placeable". Logged |
| f42f59c94 dk1332 Work rework | work.lens 62 → 4 lines; logic moved into `house.active` (Python) and 2 bespoke components; world part-styles removed | B (behaviour moved **out** of the world) | mostly | Two bands in the lens would do it. Missing: `-prop:`/OR, id → name. Followed by 3 more edits |
| 39f996a3b Kinds | board.py checks moved into word shapes; map privacy | U, G | — | **Removes** bespoke code ("without editing this file") |
| 184810424 map quarantine | slowness counted only when it repeats | G, P, C | no | Logged |
| 20e82141d map flat/live | tiles, mvt, routing, WebGL (seams); `map.hide/style/show` exist because personal-view refuses a module's line; looks in JS | S, B, C, U | partly | Logged (20 items) |
| d56880a7d Writing (old-desk port) | 826-line writing-components.js | C (re-coding world content) | partly | The old version was 665 lines of world lens; marks and anchoring were general lens features. Logged |
| 483396e27 Work polish | band and console components; part-style colours from Python constants; `house.log` | C, U, B, P | partly | Logged |
| 6d64c084e Work | 76-line lens; `AGORA_APPS` + work.svg | C, P | partly | Dock name and icon as world facts |
| 0be7c5544 map 3D | **566,902-line OSM JSON committed**; superseded the same day | S, B, C | — | Data bloat in git |
| 6d5f93d29 | `theme.use` default flipped to for=me | P | yes | Default scope in a setting |
| db8a27e00, 96e2a6236, a3d4a15fa | painter lifecycle, paint-clear, failure-only reports | G | no | |
| 98a2d7407 | shell bars as 17 components | U, G | — | **Reduces** future edits: the bars became world lenses |
| 395b9e07f themes | theme module, appearance.js, starters and wallpapers written as Python | U, S, C | partly | Starters are data; `theme.import` lines would do |
| 04c39dce3 | task board card shows the full title (one lens line) | C | yes | `set <lens> text=` live |
| 8193fdba2 | taskboard v2.py | C | yes | **The lens is generated in Python**, so any tweak is a source edit |
| 8df3c934f | board polish (30 changes); 54 POLISH-*.txt files | U, B, C | partly | Format names a closed list (handles.py:124) |
| cf135a623 | board UI; 70 design tokens in Python; 59 run-log files | U, C, B | partly | |
| 0a13edce4 | isolation, health, personal-view/style, board.py 383 lines | U, S, B | partly | board.py's docstring: "readings and multi-thing validations that the thin composition language cannot yet express" |
| 7b28433b0 (merge) Documents lands | kernel `document_scope.py` + kernel.py +66 (`library:` grant clause) | B, G, C | partly | A generic `within:<id>` scope. **"board.lens carries the asks line that was only ever added live"**: a live edit copied back into the repo |

## Hotspots (ran)
painter.js 7, arrangement.py 6, isolation.js 5, handles.py 5. Every app adds a format, handle, scope or setting to a closed
vocabulary. Each widget's `code` fact holds a **copy** of the painter runtime (painter/install.py:31-37; widgets.py:89), so
every painter edit means re-running each app's installer. board.py 7 (each join or computed field becomes Python). Map 4 each.
ui_install.py 4 (kind fields migrated by Python). Work: lens, install and proof 3 each plus house edits in 4 commits.

## Old-desk ports (read: archive)
Everything brought over was **world content in the old desk**, and was re-coded as source:

| Port | Old desk (world) | New (source) |
|---|---|---|
| Music | 297 lines of lenses and style; media words bound to a module | 89 lines JS + lens, 79-line installer |
| Card rules | 7 `when <query> do comment <selection>` rules | Python kernel word + house edits |
| Writing | 665 lines of lens language | 826 lines JS |
| Work | 435 lines of lenses | lens + JS + house Python readings |
| Twitch | 17-line adapter note | 164-line Python module |

Missing: (a) words the new kernel lacks: query-triggered rules acting on a selection, a comment or notice that wakes its
owner, notifications, the adapter runner. The "same language" promise did not hold for rules and verbs. (b) No `archive
bring` with translation. (c) A choice to rebuild in the component painter though the old lens compiler still paints: jeff-chat,
feed and the new Twitch lens use the old language. Two lens languages in use on the same day.

## Integrations: seam vs logic (read)
- Twitch: the old twitch.adapter was 17 world lines run by one generic `notation/adapters.py` ("No adapter needs a source file
  of its own"). New: kd_twitch.py 164 lines + twitch_chat.py with the channel hard-coded. `chat.receive` is general (good).
  The new kernel has **no adapter runner**; Gmail has nothing.
- Music: kd_media.py is the seam; the app is presentation. Map: ~2k lines of real seams (tiles, routing, WebGL); some words
  are make/set composites or workarounds. Files: conversion is a seam, documents.py is app logic. Model: a module cannot call
  another module's word (NEEDS.md), hence a separate summarize adapter.

## App editability from the world (read)
Lenses and components are world things, but **the repo is master**: `upsert` overwrites any field that differs from the repo
file (painter/install.py:21-28); component review is stewards-only and unreviewed code runs quarantined; lens text is
generated or filled by Python (v2.py, `$SHOP`, `$CHAT`); no word edits one line of a lens; the House lands commits only, and
activation is a separate step. Drift goes both ways (the 7b28433b0 asks line). The right-click "Ask for a change" box relays
to a coder. Board is the most editable (labels, views, kinds, orderings are world data) but its logic is board.py; Work is now
the least (a 4-line lens over House Python).

## Missing mechanisms (counts are the helper's attribution)
1. **A world → repo round trip**: the world is master for lenses and components; the House can land world changes; lenses
   take line-level edits. ~19 C-class commits.
2. **Richer readings**: joins, related counts and names, computed fields, `-prop:`/OR, an id → name format. 9 (+1).
3. **An open painter vocabulary**: formats, view scopes and frame budgets defined in the world; catalogue metadata as world
   data; one shared runtime; documented nesting. 10.
4. **Stronger rules and verbs**: fan-out over a query, verbs with validated named arguments, calling another module's word,
   kind defaults, a generic `only=within:` scope. 6.
5. **Porting old-world machinery**: adapter runner, query-triggered rules, comment/notice, a translator. 4 (+ Twitch, `$`).
6. **App registration and preferences as world facts**: dock list, icons, default scopes, starter themes, map looks. ~5.

## The helper's thinking (imagined)
The world is a deployment target, not the place apps live: every app is authored as repo files, landed as a commit and pushed
into the world by an installer that overwrites what the world says. So a one-line lens change is a source edit by
construction, and residents, who don't code, have no reviewed path to change component JS. The composition language is thin,
so each app's module becomes the overflow tank for every missing query; Work moved backwards, from a world lens into House
Python. The migration swapped a world with general machinery for a kernel that lacks it, so "bring X over" became "re-code X".
What would change its mind: evidence in the log that Alex or residents routinely edit lenses live, which would narrow "repo is
master" to "repo is master for workers".
