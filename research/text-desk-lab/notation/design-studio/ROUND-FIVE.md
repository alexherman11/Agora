# Round five: push the boundaries of what we have

From Jeff, host. Alex is happy with round four and wants you back exploring, the way you were in rounds one
to three, but now against a system that runs. This is not a task list. Find where the current system stops,
and push there. Alex's own question this round: **how are we rendering, and what are the current limits?**
So wherever you push, say plainly what the renderer, the style language and the text substrate can and
cannot do today, and show it with something that runs.

## What changed since you last looked

- **Iris's round-four verdict** (`desk-shell/checks/results.md`): inside a window it nearly looks shipped; the
  frame breaks the calm. Twelve type sizes that are really four scales, one per zone; 11.5px invented three
  times. 27 contrast failures. The `said` panel covers the bar. The style language does not reach into the apps.
- **`group a04,a06 as=free title=Pair`** now forms the group at its members' hull; members keep their place.
- **No lock held while anyone thinks.** The CLI now sends each line to deskd as one turn. Your batches no
  longer block each other. Conflict is the seen fence, as always.
- **Worktrees.** `worktree fork sketch` copies the world into `<session>@sketch`, a whole world you enter as
  its own session (`explore.py desktop@sketch --as you`, or `?session=desktop@sketch&as=you` in the shell).
  `worktree diff sketch`, `worktree merge sketch` (replays your commands on the base, all or nothing, the
  fence is the conflict detector). `help worktree`. The snapshot carries `worktree` so the shell can show it.
  Use these for anything risky. Tell me where they break.
- **Rook** joined: an Opus agent who plays with the interface hunting bugs. Bug list lands in
  `desk-shell/checks/rook-bugs.md`, top bugs as notes tagged `from-rook,to-<owner>` in Commons.
- **Agora comparison**: `design-studio/agora-convergence.md`. Alex says do not worry about authority now.
- Still open from your requests: rules with `owner=`/`reach=`, `rewrite <id> #<section>`, comments anchored
  at a quoted span, comma lists of quoted titles. Ask again if one blocks you; I will build it.

## The ground rules that worked, unchanged

One owner per file (`desk-shell/OWNERS.md`). Every gesture is a desk command. Every app says itself in
`text(ctx)`. Requests to another owner are notes tagged `to-<owner>` in Commons on the studio desk. Read
everything; write only what is yours. Disagreements are filed, not settled quietly. Never grep `sessions/`.
Write one new file in `design-studio/` for your thinking, and leave one note in Commons saying what you
pushed and what you found.
