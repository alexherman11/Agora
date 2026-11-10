# Rules and grants meet shared kinds

> **Draft 2 (28 Oct, after the security review `review/privacy-authority-review.md`).** Draft 1 is kept below, from "The property" on. **Its premise was wrong**, as the review showed (ran): a kind name is not a trust boundary.

## Draft 2: trust is about whose act, not which kind
**What the review found (ran):**
- **Kind names are free to anyone.** Any member can make a thing of kind `taskboard-task`, and Alex's rule `on=make of_kind=taskboard-task` then acted *as Alex* on Pike's thing (H3).
- **Lists don't fix it.** "List the own kinds you trust" names kinds, not people. `implements:` would widen it to every member who makes a declared kind.
- **Rules were rewritable (C1, fixed tonight).** A leader could rewrite a member's rule, which then ran as the member. Now only a rule's maker changes what it does; leaders may switch it off or forget it (`words.py` set_, `tests/test_chat.py`).

**Proposal (imagined; a design point for Alex):**
1. **A rule says whose acts fire it:** `by=`.
   - **The default:** the rule's maker, their agents, and the leaders of the rule's group.
   - **`by=anyone`** has to be said on purpose. It's shown on the rule and in `look`.
   - Today's rules keep firing for anyone until their maker says otherwise. The default applies to new rules, and `look <rule>` says which it is.
   - **Why:** a rule runs as its maker, so it should act on what its maker trusts. Who acted is the honest signal; which kind the thing is, isn't.
2. **Alternative, stronger:** a rule fired by someone else's act runs with the maker's rights ∩ the trigger's, the way a module answers its caller.
   - That's safer, but it may break Alex's own announcement rules, which post on others' dones.
   - The review weighs (1) as cheap and (2) as safer. Alex's call.
3. **Lists in `of_kind`** (draft 1 proposal 2) are still fine as a convenience, with the review's guards:
   - an empty list matches nothing;
   - no globs (`of_kind=*` would reach `said`);
   - kernel kinds refused.

   They're no longer the trust mechanism; `by=` is.
4. **The refusal for a filter naming a kind nothing is** (draft 1 proposal 1) stays, with the review's fixes:
   - it lists only kinds the rule's maker can see;
   - it gives the log a `kept=` with no kind names;
   - it uses the scope-aware `decl`/`shape`, not `is_open` across every scope.
5. **`implements:`** only after (1), declared by leaders of the rule's scope or above, bound at make/set time like `do_bound`, and never naming kernel kinds.
6. **Grants:** `only=kind:X` is safe as it is, because a module acts with its caller's rights, narrowed. A module on its own (installed `for` someone) acts with that person's rights on any `X` a member made. Same fix: a grant may say `by=` too.

**What would change my mind:**
- **If Alex wants his announcement-style rules to hear everyone,** `by=anyone` is the common case, and the default should be the other way round, with a warning on `make`.

## Built, 28 Oct, late (Alex: "You, your agents, leaders")
- **A rule's `by=`:**
  - **`maker` (the default for new rules)** hears the maker, their agents, and the leaders of the rule's group;
  - **`anyone`** hears everyone, said on purpose;
  - **rules made before this** keep hearing everyone.
- **A sealed act** fires only `by=anyone` rules.
- **`by` is maker-only steering.**
- Code: `kernel.py` `_rule_hears`, `words.py` `_rule_by`. Tests: `tests/test_rule_by.py`.
- **Not built:** `only=maker:` on grants (item 4 below), and the notice to makers listing their `by=anyone` rules.

## Draft 2.1: the security review's round 2
**Fixed in source (ran, with tests; live since the 22:47Z restart, 28 Oct):**
- A leader switched a member's parked rule back on, and it ran as the member. Now a leader may switch it off, never on.
- A leader's `undo` of the member's fix put the old `do` back. Now someone else's undo that re-points a rule, or switches it back on, leaves it off.
- A person may now steer a rule their own agent made (`rule_maker`).
- A member's closed declaration replaced the steward's. Now one declaration per name per scope, closed ones too, and a nearer one needs a leader.

**Added to the proposal (imagined):**
1. **A sealed act fires only `by=anyone` rules.** Otherwise a rule `by=Pike on=vote` tells its maker when Pike voted, and on what. That breaks sealing (SHAPE §8). It needs a test.
2. **`by` is part of a rule's steering:** maker-only, like `do`. `look` shows the resolved set, as `do_bound` is shown.
3. **For a module's act, `by` matches its `for`.** A module on its own (a relay) never fires a default rule.
4. **On grants, `by=` is the wrong word.** A grant limits its *target*, so the enforceable form is the target's maker:
   - `only=maker:<me|leaders|anyone>`, beside `kind:`/`thing:`/`fields:`;
   - `made_by` and `for` are kernel-kept, so it can't be spoofed.
5. **Option 2 (rights ∩ the trigger's) needs three things specified** before it's a real option:
   - whose `once` budget it spends;
   - whose seal a sealed word uses (the maker's);
   - whose sight it reads with.
6. **The transition:** existing rules keep hearing everyone, with one notice per maker listing their `by=anyone` rules.

---
# Draft 1 (superseded)

> **Draft 1, by Claude, 28 Oct 2026.** Friction 3 in `trials/FRICTION.md`. In review, not built.
> - **Labels:** **read** (code, file:line), **ran** (as printed), **imagined**.

## The property
**Classifying never adds power** (decided with shapes, `kinds.py` header). A thing whose shape fits `task` doesn't fall under a rule or grant written for tasks unless its own kind is named.

That stays. The friction is that pointing authority at a shared kind fails **silently**.

## What happens today
- **Rules (read, `kernel.py:1535`):** `of_kind` compares one kind literally.
  - The trial (ran) found `set dk168 of_kind=task` stopped Alex's own Done announcements (0 posts).
  - `of_kind="taskboard-task,issue"` matched nothing, because a list isn't read as a list.
- **Grants (read, `kernel.py:955-957`):** `only=kind:a,b` already takes a list. But `only=kind:task` admits nothing, because nothing's own kind is `task`. The board widget then can't move issues, with no word about why (ran).

## Proposal (imagined)
1. **Say it, don't swallow it.** When a rule's `of_kind` or a grant's `only=kind:` names a kind that nothing visible *is*, and that kind is a shape (it has needs, or others extend it), refuse at make/set time and list the own kinds that fit:

   > of_kind matches a thing's own kind, and nothing here is a task. task is a shape: taskboard-task, issue, gh-issue fit it (rows task lists them). Say of_kind="taskboard-task issue" to include those you trust.

   A kind nothing is *yet*, and that isn't a shape, stays allowed: a rule written before the first thing of its kind exists.
2. **Rules read a list as grants do:** `of_kind="taskboard-task issue"` (spaces or commas). Each kind is named by whoever writes the rule, so trust stays explicit.
3. **Later, only if Alex says yes to producer spellings** (shape-reads §6):
   - `of_kind=implements:task` would mean "own kinds whose declarers said they implement task";
   - that's a nominal opt-in by a leader, never a structural fit.
   - **Never `fits:task`:** a member could shape their own things to wake a steward's rule, which runs as its maker. That amplifies the member.

## Why not structural matching for authority
- **A rule runs as its maker** (`kernel.py` `_fire_rules`). If it matched by shape, anyone able to make a thing with the shape could make the steward's rule act, on things the steward never vetted.
- **A grant narrows a module.** Widening it by shape lets a member's shaped things into a module's reach. Its acts still carry the caller's rights, but a module on its own (installed `for` someone) would act on them with that person's rights.

## Cost
Small: a check in `make kind=rule` / `set <rule>` / `grant`, a list split in `_rule_matches`, and tests. About 60–100 lines.

## What would change my mind
- **If stewards in practice always want "every task-like thing"** and the lists go stale every time an app arrives, `implements:` (step 3) becomes the main path, and step 2 a stopgap.
