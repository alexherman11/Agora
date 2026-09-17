# Friction session: building my own desk from nothing (2026-09-17)

The notes for this session live **inside the desk** that was built during it. The desk is its own text form:

    python explore.py home                       # the live session (pickled under sessions/)
    python explore.py fresh --reset < sessions/home.desk.txt    # rebuild it anywhere from its export
    python explore.py home --shape               # the desk without ids, for replay comparison

`sessions/home.desk.txt` is the `export` of the desk: the commands that rebuild it. Replaying it on an empty
desk reproduces the desk exactly (shape diff empty, zero refusals). That is the session's main finding: the text
is the desk.

## What the desk holds

- **Plan**: the `Exploration plan` doc with goal, method, a checklist (5 of 6 done) and a Findings section.
- **Friction**: one note per friction item still open, tagged `friction`.
- **Done**: friction items fixed in the lab source, tagged `fixed` (a rule moved them there).
- **Ideas**: the scripting-layer ideas, tagged `idea`.
- **Today**: what the clock rule and the reply rule route there.
- Six rules and four scripts that maintain the above. `rules` and `scripts` list them.

## Commands added or changed during the session (all in the lab source, all unmeasured on a model)

| area | change |
|---|---|
| creating | `create kind=surface title= layout=`; created things never exceed their parent; runtime arrivals in a tiled parent take a fair share |
| naming | titles resolve everywhere an id is wanted, including inside selection terms (`in:Today`) and `examine "Two words"` |
| properties | `tag add= remove=` (new), `due on= clear=` (no longer hidden); `place` is a real subject verb |
| undo | bare `undo` = your latest change; composed verbs undo whole; a rule's consequences undo with their cause; undo keeps your view |
| batching | `script` definitions keep their `;` |
| rules | `rule when <selection> do <verb> [k=v] [now=1]`, `rule on <verb> [by=actor] do <verb>`, `rules`, `rule drop rN`; receipts print as `~` lines after the command's own receipt |
| scripts | `script name = cmds` with `$1..`, `run name args`, `scripts`; scripts may call scripts |
| time | `clock YYYY-MM-DD`; `today` in `due<`/`due>` terms; the clock re-evaluates rules |
| export | `export` emits the rebuild commands; `explore.py --shape` compares desks without ids |
| receipts | `move` to the current parent is a no-op; `where:` only printed where overlap is possible |

## Still open (also on the desk under Friction)

- The first act on a fresh desk is refused until one `look`; the refusal should say so plainly.
- Ids are not guessable; titles are the practical names, and the create receipt should say that.
- `tile` on an already-tiled surface says ok and does nothing.
- Rules see states and events but not time on their own; the clock is a command.
- There is no way to read a note's text inside `look`; `read`/`examine` are separate calls.
- Order inside a rule-fed panel is arrival order only.

See NOTES.md "Round 11c" for the narrative and `sessions/home.desk.txt` for the desk itself.
