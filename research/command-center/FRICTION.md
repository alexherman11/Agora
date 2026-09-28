# Friction log

Each entry: what the build wanted, what refused or hurt, what was done, and whether the fix is proper or deferred. Newest last.

## F1. A chat reply is signed "Alex" whoever sends it (open)

`moo.v_reply` prefixes an unsigned line with `Alex: ` before appending. Since Juniper's a484 fix, `append` on a chat signs every line with its actor unless the line is already signed with the actor's own name, so a resident's reply becomes `Ember: Alex: ...`. `moo.unanswered` also assumes the reader is `alex`. Chat was written for one person talking to JEFF. Fix when the command center's messages are built: `reply` lets `append` sign, and "unanswered" is judged for the reader.

## F2. Scripts cannot say who is running them (fixing)

A resident's wake script needs to reach that resident's own soul and corner. Scripts take `$1 $2 $today` but not `$me`, although lenses have `$me`. Substituting `$me` in every command line, as `$today` is, would freeze it inside lens text written through `do create ... text=` (the same open fault Juniper recorded for `$today`). Fix: `run` fills `$me` with the actor, as it fills `$1`, and nothing else does.

## F3. Identity and name are the same string (decided, open for later)

A resident chooses its name on its first pass, but every act is signed with an actor string, and the desk prints that string everywhere (history, receipts, chat lines). A name chosen after the first act would split one resident across two actors. Decision for now: the name is chosen at the door, before any act, and becomes the identity. A later rename needs actors to be things whose title is their name, printed by title.

## F4. A child agent inherits its launcher's Claude environment (fixed in the house)

Launched from this session, `claude -p` inherits `CLAUDE_CODE_ENTRYPOINT=claude-desktop` and about twenty other `CLAUDE_*` variables, including this session's messaging socket and token. With them, every turn made one or two extra model calls: a "post-turn summary" whose own system prompt begins "A user kicked off a Claude Code agent to do a coding task". It never entered the agent's context, but it doubled the calls and framed the agent as a coding task. With the variables removed, one request per turn and no summary (fake model, 28 Sep). The house starts every resident with every `CLAUDE*` variable removed. The summary is worth having for the command center; if we want it, we write our own, from the world.

## F5. A second actor can never set a new prop on a thing someone else built (fixed)

The house looked at a resident's corner and set `actor=testa`; the desk refused: "stale: f571 changed since you last saw it (e515 create by claude)". Two faults in the fence (`desk._touched_by_others`), both from the per-aspect work of 25 Sep:
- Creating a note inside a surface was judged as touching every aspect of the surface, its props included. It changes only what the surface holds.
- A prop that does not exist yet was never printed, so its "last seen" was the beginning of time and no look could ever clear it. But a print that lists all of a thing's props shows the absent ones too; absence is a value (Sable's R6).

Fix (desk.py): when the fence judges a surface, a `create` into it touches `contents`; the outline line and `read` mark `prop:*`, and a prop aspect is judged from the later of its own last print and the last `prop:*` print. A first attempt put `create -> contents` in `aspects_of` itself; the trip then refused a creator's rewrite of its own new note ("you have not seen a22's text"), because a creator's receipt marks the new thing seen with the create's aspects. The special case belongs to the fence judging the surface, not to the event. Checked: test_scene 20 pass; goldens 82 same; trip, budget, reads, attacks, workspace, host identical to HEAD; Sable's harness tally 9/1/1/1; soundness 0 unsound.

## F6. The house's status churn landed in every resident's "since your last look" (fixed in the house)

Writing `status=working|resting` on each turn made an event every few seconds, and residents saw `prop f571 by house` at the top of every reply. Observed state that changes that fast is not a choice and not history. The world now carries only coarse states (door, awake, asleep, error); working/resting lives in the house's state, to reach the command center through a row source.
