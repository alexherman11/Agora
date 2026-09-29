# Worker trial help-list

Commission a598, asked by alex in a copy of frontier, run by a real worker in a throwaway checkout. Ended: landed.

## The commission

**help should list only verbs this desk can do**

What: help lists reply among the verbs, but 'help reply' answers 'no verb reply here'. The list seems to come from moo.py's registry, which the knife desk (desk_knife.py) does not fully serve. Make help's verb list show only verbs this desk will actually do. Why: F21 in research/command-center/FRICTION.md: a resident who trusts help hits a refusal. Done when: every verb that help lists can be asked about with 'help <verb>' without a 'no verb ... here' answer, checked in a copy of the world; test_scene and the session goldens (suite/sessions.py --check) unchanged, or rebased with a reason you state.

## The thread (examine)

```text
> examine a598
a598 task "help should list only verbs this desk can do" · commission=landed status=open asked_by=alex worker=worker-a598 landed=87f0fb9 · 99w · 4 comments, 4 open · try: resolve c599 resolve c601 resolve c602
  a task (subject s597) on f150:
    * What: help lists reply among the verbs, but 'help reply' answers 'no verb reply here'. The list seems to come from moo.py's registry, which the knife desk (desk_knife.py) does not fully serve. Make help's verb list show only verbs this desk… (line cut; read a598)
    * c599 worker-a598 (open): progress: fix written in desk_knife.py cmd_help (not yet run). Found the leak: help <unknown> fell through to moo's list (its whole registry: reply, tidy, split… (read a598 for all)
    * c600 alex (open): Your call: keep it small, and say in your done note what you chose and why.
    * c601 worker-a598 (open): done (cb103e2, desk_knife.py cmd_help only): help <unknown> now lists only the knife desk's general+pair verbs (was moo's whole registry: reply tidy split gathe… (read a598 for all)
    * c602 house (open): landed as 87f0fb9: 1 file(s). Health after: python: ok \u00b7 scripts: ok \u00b7 test_scene: 14 passed \u00b7 session prints: worlds at 7731e64, compiler on the… (read a598 for all)
  where: screen 800,16 32x768 · in f150 (row) local 368,8 z10 · clear
  when: last touched 2026-09-28 (0d ago by the clock)
  verbs: due · append retitle rewrite · fold comment resolve link prop tag · move resize raise lower remove · pair: swap beside match link   (help <verb> for args; the target may be a selection: help selections)
```

## What landed on the trial branch

```text
87f0fb9 land a598: help should list only verbs this desk can do
cb103e2 F21: help on the knife desk lists only verbs it does

research/text-desk-lab/notation/desk_knife.py | 21 +++++++++++++++++----
 1 file changed, 17 insertions(+), 4 deletions(-)
```

## The worker

*start 23:03:32: {"cmd": ["-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose", "--model", "claude-opus-5-5", "--permission-mode", "acceptEdits", "--allowedTools", "Read", "Edit", "Write", "Glob", "Grep", "Bash(git status:*)"*

**house → worker** 23:03:32

```text
Your commission (a598), asked by alex:

help should list only verbs this desk can do

What: help lists reply among the verbs, but 'help reply' answers 'no verb reply here'. The list seems to come from moo.py's registry, which the knife desk (desk_knife.py) does not fully serve. Make help's verb list show only verbs this desk will actually do. Why: F21 in research/command-center/FRICTION.md: a resident who trusts help hits a refusal. Done when: every verb that help lists can be asked about with 'help <verb>' without a 'no verb ... here' answer, checked in a copy of the world; test_scene and the session goldens (suite/sessions.py --check) unchanged, or rebased with a reason you state.

Start by reading AGENTS.md, then the code you need. Comment on a598 if anything is unclear.
```

**worker** 23:03:49

```text
I'm looking into where `help` builds its verb list. My attempt to copy the live world was refused (the path is outside my worktree), so I'm reading the code for now.
```

**worker** 23:04:52

```text
I've made the fix. Copying worlds into `sessions/` needs approval, so for now I'm checking the change by loading a world in memory, without saving anything.
```

**worker** 23:05:08

```text
I can't run Python or copy worlds without approval here, so I'm asking alex through the desk.
```

**worker** 23:05:28

```text
I've found the cause and written the fix, but haven't run it yet. This session won't let me run Python or copy the live world into my worktree. I've asked you for access in comment c599 on a598.

**The cause** (checked in the live world, still on the old code):
- `help reply` answers "no verb reply here".
- `help zzz` answers "no verb zzz. verbs: …" and lists moo's whole registry: `reply`, `tidy`, `split`, `gather`, `dedupe`, `done`, `stack`, `reveal`. The knife desk doesn't do any of these.
- A synonym sends you to the same kind of refusal. For example, `help arrange` says "the desk would read it as tidy" and then `help tidy` refuses.
- The "general verbs" list names `link` twice.

**The fix**, in `desk_knife.py` only, in `cmd_help`:
- `help <unknown>` now lists only the verbs this desk does: its general verbs plus the pair verbs, with the duplicate `link` removed.
- `help` on a synonym for a verb the desk refuses now says so, then gives the refusal with what to use instead.
- The "use X instead" alternatives (for example, `append` instead of `reply`) were a table inside the `do` path. I moved them into a shared constant, so `help reply` now says "use append …". The `do` refusals read the same as before.

**Not yet checked:** the fix in a copy of the world, `test_scene.py`, and `suite/sessions.py --check`. The goldens might change where they record a `help` refusal. I also wrote a throwaway `_a598_check.py`. It loads a world in memory and saves nothing. It asks `help` for each listed verb and counts any that are refused. I'll delete it before committing.

To go on, I need:
1. Permission to run the pinned Python on `explore.py`, `test_scene.py`, `suite/sessions.py --check`, `health.py` and `_a598_check.py`.
2. The world copied to my worktree as `sessions/try-help-list-try.pickle`, or permission to do the copy myself.
```

*turn ended 23:05:28: success, 33 steps, $0.77 so far*

**house → worker** 23:05:34

```text
~ alex on your commission (e567): Your call: keep it small, and say in your done note what you chose and why.
```

**worker** 23:05:40

```text
Python still needs approval, so I can't run anything. I'll keep the change small, check it carefully by reading, and say in the done note that nothing was run.
```

**worker** 23:05:50

```text
From reading them (not running): the session goldens are lens prints and `test_scene.py` never calls `help`, so neither goes through `cmd_help`. Committing now.
```

**worker** 23:06:24

```text
I committed the fix (cb103e2) and marked a598 ready, but none of it has been run. This session refused every Python run and the world copy, so the fix, `test_scene.py`, `suite/sessions.py --check` and `health.py` are all unchecked. Please have the house run them before trusting it.

**What changed** (only `cmd_help` in `desk_knife.py`):
- **`help <unknown>`** used to fall through to moo's list, which named its whole registry (`reply`, `tidy`, `split` and others). It now lists only the verbs this desk does: its general verbs plus the pair verbs.
- **Synonyms** such as `arrange` (moo reads it as `tidy`) now say this desk doesn't do that verb. Before, they pointed at `help tidy`, which refused.
- **`help reply`** (and the other verbs this desk refuses) now names what to use instead, such as `append`. `do` already had that table; I moved it into a shared constant so both use it, and the `do` refusal text is unchanged.
- **`link`** is no longer listed twice.

**What I chose and why:** you said keep it small, so I didn't add a new verb. Bringing `reply` to the knife desk (the other fix F21 suggests) is left for you.

**What I know and how:**
- **Ran:** the live `try-help-list` world, on the old code. `help zzz` listed `reply`, `tidy` and `split`, and `help reply` answered "no verb reply here". That confirms where the list came from.
- **Read:** the session goldens are lens prints and `test_scene.py` has no `help` calls, so I expect both unchanged. That's reasoning, not a run.

My throwaway check script is deleted and the working tree is clean. The done note is c601 on a598.
```

*turn ended 23:06:24: success, 14 steps, $1.05 so far*

*exit 23:06:43: {"code": 0, "pid": 55244}*

## Tools the worker used

- Read: 10
- Grep: 9
- Bash: 8
- PowerShell: 7
- Edit: 5
- mcp__desk__desk: 3
- Glob: 1
- Write: 1
- ToolSearch: 1
