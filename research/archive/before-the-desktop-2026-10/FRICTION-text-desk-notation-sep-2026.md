> **Archived 12 Oct 2026 (Claude, at Alex's word).** This was the notation lab's first friction file. The living record is the Rough spots surface (f747) in the frontier world, exported to research/command-center/FRICTION.md. Kept for its reasoning; do not read it for the current state. Start from `AGENTS.md` and `docs/`.

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
| views | `create kind=view title= query=<selection>`: a surface whose contents are a selection, evaluated at each look |
| depth | `look X :3` first lines under each thing, `look X :4` full text (8 lines, fold declared) |
| time | events stamped with the clock day; `age<N` / `age>N` terms; examine prints `when:`; undo is not touching |
| provenance | `why <id>`: the events that put a thing where it is, and which rule would act on it next |
| chat | `append` on a chat signs unsigned lines as Alex; `find` ranks title matches first |
| properties | `prop k=v remove=k` on any thing, shown on the line, `prop:k=v` selects; export carries them |
| trials | kind `trial`; `launch` runs run.py in the background (external effect, undo refuses); `sync` brings results back as `harness` events with a transcript doc; `help trials` |
| rules | a rule may name an explicit target: `rule when in:Today do sort Today by=due` |
| handles | `create ... as=name`, `set name = <id or title>`, `$name`, `vars` |
| escapes | the desk owns them: unescaped `
` newline, `\` backslash, `\$today` literal; the batch splitter honours escaped quotes |
| receipts | `move` to the current parent is a no-op; `where:` only printed where overlap is possible |

## Measured

Terra on the home desk (task `home`): 6 of 7 in 7 calls, then 7 of 7 in 8 calls after fixing what its own Model's view note named.
Terra and Sol on `home2` (write a sweep rule and a morning script): 7/7 in 6 calls and 8 calls. A Terra run launched from inside the desk: 8/9 (assessor strictness), synced back as harness events.

## Still open (also on the desk under Friction)

- Ids are not guessable; titles are the practical names, and the create receipt should say that.
- Time is the clock command; nothing advances on its own.
- A rule over an age term still defaults to "things that enter"; a sweep needs `now=1`.
- Log after the look, never before: two journal entries had to be corrected because I wrote the result I expected.
- Order inside a rule-fed panel is arrival order only.

See NOTES.md rounds 11c to 11e for the narrative and `sessions/home.desk.txt` for the desk itself.

## Session 2 (2026-09-17, after a compaction): the desk as the workbench

Everything below was found by working at the desk or by reading a model's transcript *on* the desk (`read <transcript> #N`),
then fixed in the lab source and filed on the desk's Done panel. Terra and Sol each ran the new task `home4` once.

| area | change |
|---|---|
| sessions | the shell's default python is 3.14, where `itertools.count` no longer pickles; the id counter is a plain int (old pickles migrate) |
| rules | `rule ... do run <script> [args]`; `$item` and `$item.title` in a rule's args or k=v; the seen fence stands aside while a rule fires; a refused script inside a rule is a could-not line, not a firing; `script drop <name>` refuses while a rule runs it |
| scripts | `$1.title` (Terra used it before it existed, having found my note about it with `find`); a definition with `;` says how many commands it holds |
| tables | `table <selection> [cols=] [by=] [desc=1]`; a view created with `cols=` renders as a table at every look; export carries the columns |
| reading | `read X tail=N`; `read X #Section name` without quotes; `help` answers for table, find, read, sync, compare |
| selections | registry verbs (tag, prop, due) run over selections and id lists, not only over one id |
| receipts | a stopped batch lists its unrun commands; `prop remove=` of an absent key and `prop k=v` with the same value refuse; removing a view or surface says so; a full column says `N past the bottom (offscreen)`; `clock` going backwards says how many things are now in its future |
| find | folds at 8 per surface with a pointer |
| harness | transcript docs indent result bodies so a `##` inside a result is not a section |

Measured: `home4` (name the trial with the most calls per passed check; make harness results announce themselves in the Journal;
the assessor probes the rule with a fake harness prop): Terra 6/6 in 8 calls, Sol 6/6 in 10 calls. The priya rerun's 27 calls
were read from its transcript on the desk: one stale refusal mid-batch, then six calls of one-write-per-call caution.

Still open on the desk: nothing tagged friction at the time of writing. Open in my head: a column that overflows only declares it;
a real desktop would scroll. The clock is simulation time (2026-09-27 at the end of the session), not the wall date.
