# Work

> Builder record by Claude, 27 Oct 2026. Alex: "Also bring forward a worker monitoring page as well that used to exist", and on the design page: "a coder terminal style interface where i can see worker progress (basically a really good overview of all the work being done), where i can click in and view more closely or chat with workers directly."

One window, `window.open work`, in the dock as **Work**. Brought forward from the old desk's home-work and home-board panels (`old-desk/`), in the component painter's style (`painter=components`, like the Task board).

- **Left:** AT WORK, one line per agent the house runs (`reading:"house.who"`), with a coloured word for what it is doing and Open. Then the task cards: NEEDS YOU (`who=Alex`, not done), BUILDS (a card with `build=` and `builder=`), IN MOTION (lane Now), LANDED (lane Done, the last 8).
- **Right, after Open:** what they are doing now (their current acts while working), their lines and receipts in their own chat (`chat <their chat>`), their record outside any chat (`house.activity`), and a box that says into their chat, or into Shop talk with @name for an agent with no chat of its own.
- **Colour says whose move it is** (the old board's rule), as part-styles on the badges: mint at work, sky idle, amber Alex's, lilac a build on its way, rose stuck.
- **Live:** the house announces `house.doing` (never recorded) when what an agent is doing changes, so the page rereads.

**Builders appear by themselves:** every `house-agent` is a row of `house.who` (its `chat=` and `task=` facts say where to talk to it and what it builds), and `task.build` (MOVING-IN step 3) only needs to write `build=asked|building|landing|blocked|landed` and `builder=<name>` on its card.

Files: `work.lens` (the arrangement), `install.py` (through the door, as Alex: lens, widget and grants, his `work-view`, JEFF's `chat=`, the dock), `proof.py` (hidden).

## Evidence

- **Ran** `proof.py`: a fresh hidden desktop (`test_kdesk.Desk`), headless browser, scripted model: 7 of 7 checks (`evidence/work-proof.json`, pictures `work-overview.png`, `work-jeff-open.png`, `work-jeff-talked.png`). The box said "from the Work page" into the Conversation as Alex, and JEFF answered there.
- **Ran, live (8810):** installed; `look-view work` compiles (11 rows, 11 badges, the styles); `dock_apps` ends with `work`; `house.who` gives JEFF with his chat. No window was opened on Alex's screen; the Work page itself has not been seen live yet.

## Rough spots

- A component widget without the `components` grant paints nothing, silently (it took a bisection to find). The missing word: **a refusal the painter shows** when its own words are not granted.
- The component painter paints only a page that is seen; headless proofs must bring their tab to the front.
- `pages/shell/shell.js`: one line, `work` in `AGORA_APPS`, plus `apps/work.svg`. The missing word: **an app's dock name and icon as world facts** (today the dock knows its apps in source).
