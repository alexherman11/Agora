# Day one: the two-sided desk, as commands that could run this week

Lark, round two. The brief asks for the smallest first step that would already feel good, written as commands
rather than as a design. So this file is mostly a transcript of setting the thing up, with an honest ledger
of what the engine does not have yet.

**The headline, and it is the reason I think this is a week and not a quarter: day one has no renderer and
no eyes.** Warmth — the mechanism my whole round-one design hangs on — does not need a viewport, an eye
tracker, or a screen. Version one of `warm` is a query over the event log the desk already keeps:

> **`warm` v1 = another actor's most recent event on this subject was less than 90 seconds ago.**

Hands-only warmth. No gaze, no pixels, no protocol with a browser. It gets the great majority of the value
of the idea, it is a selection term over data that exists today, and it can be replaced by the real
eyes-and-hands version later without changing a single rule written against it. If only one thing from my
round-one work gets built, I want it to be this, and I want it built in its cheap form.

---

## 1. The ledger: what exists, what must be added

| # | needed | status | size |
|---|---|---|---|
| 1 | surfaces with an `owner` | `do prop` exists; the **meaning** is new (tie-breaks, undo reach, who gets asked) | small |
| 2 | `warm` / `cooling` / `cold` as selection terms | **new**, but pure event-log query (see above) | small |
| 3 | `reach=` on a rule, plus `do sign` | **new**; unsigned out-of-reach rules *report* instead of firing | medium |
| 4 | `defer` as an outcome, and an `offer` (`o..`) with accept / decline / withdraw | **new**; this is the real work | medium |
| 5 | name resolution `mine → ours → theirs`, always printing the qualified form | **new** | medium |
| 6 | `do claim <target> note=… for=20m` | a prop with an expiry, printed on the line | small |
| 7 | the absence digest (`welcome back`) | an **extension** of the since-header that already exists | small |

Four small, three medium, no renderer, no new storage format, no protocol. Everything is expressed in
mechanisms the desk already has: selections, props, rules, events, receipts.

What is deliberately **not** in day one: the gaze (`look alex` with a viewport), sight-marks (nothing here
has pixels yet), benches, veils, traces, styling, holdings, bulk. Those all wait for material that day one
does not have.

---

## 2. Setting it up

```
$ desk --as alex
```

```
> do group a01,a02,a03,a04,a05,a06,a07,a08,a09 as=column title="alex"
ok f10 surface "alex" column · 9 inside · everything that was loose on the desk
> do prop f10 owner=alex
ok f10 · owner=alex
  · owner decides: whose act stands on collision · whose undo reaches · who gets asked
  · it does NOT decide who may act. both of you may act on both sides.
```

> That receipt is the whole of my position on ownership, printed at the moment the word is first used.
> If the desk says it there, nobody ever has to look it up, and nobody ever assumes an ACL.

```
> do create desk kind=surface title="lark" as=column owner=lark
ok f60 surface "lark" column · empty · owner=lark
  new: names now resolve mine → ours → theirs. "Inbox" is ambiguous across sides
  and will print its qualified form whenever the answer is not yours.

> do create f60 kind=note title="hello" text="your side. I will not tidy it."
ok create f60 … [e2] → a61 · alex/…  ·  wait —
refused · f60 is lark's side and you have not met yet.
  a first thing on someone's empty side is a gift, not a placement.
  now: do hand a61 to=lark line="…"   ·   do create alex/Notes …
```

> Half-formed and possibly too cute, but I want *something* at this spot. The moment a second side exists
> is the moment the desk stops being one person's, and if the first cross-side act slides through silently
> then nothing afterwards will feel different either. It costs one refusal, once, ever.

---

## 3. House rules

A surface, not a config file. Both of us can `look` at it, comment on it, and `undo` a change to it.

```
> do create desk kind=surface title="House rules" as=column owner=ours
ok f70 surface "House rules" · owner=ours · both must sign a change here
```

Four rules. I have written them as they would actually be typed, with the receipts.

```
> do rule when warm,-mine do defer  title="don't take what the other is holding"
ok r1 · reach=world · UNSIGNED — reports only
  ~ r1 would defer: nothing right now (nothing is warm)
  now: do sign r1 as=alex

$ desk --as alex
> do sign r1
ok r1 signed by alex and lark · reach=world · live
  r1 when warm,-mine do defer   "don't take what the other is holding"
```

```
> do rule on remove when -mine do offer  title="never delete on the other's side"
ok r2 · reach=world · unsigned — reports only
> do sign r2          (both)
ok r2 live
```

```
> do rule on <verb> when -mine,count>3 do slow  title="many-at-once lands visibly"
ok r3 · reach=world · unsigned
> do sign r3          (both)
ok r3 live
  note: `slow` is a rendering instruction with no renderer yet. Until there is one it
  prints on the receipt ("landing slowly") and does nothing else. Declared, not faked.
```

> I want `slow` in from day one even though it is inert, because the receipt line
> `landing slowly (bulk, on his side)` is *itself* the useful half: it tells me my act is the kind that
> ought to be visible, so I can choose not to do it. A rule that only prints is still a rule that governs,
> as long as the thing it governs is me.

```
> do rule when mine,age>14 do tag stale  title="my own housekeeping"
ok r4 (lark) · reach=mine · no signature needed · live
```

> Four rules and only one of them needed no signature, which is the right ratio: almost everything
> interesting reaches across, and reaching across is exactly what should be countersigned. Note the shape
> of `do sign` — **the rule exists and reports from the moment it is written**, so its author can see what
> it *would* do before asking for a signature. You sign a demonstrated rule, not a described one.

```
> look "House rules"
f70 surface "House rules" · owner=ours · 4 inside
  r1  both · world  when warm,-mine            do defer   · deferred 3 acts in 6d
  r2  both · world  on remove when -mine       do offer   · 0 acts
  r3  both · world  on * when -mine,count>3    do slow    · 11 acts
  r4  lark · mine   when mine,age>14           do tag stale · 40 acts
  · do why r1 · do unsign r2 (asks alex) · do drop r4
```

> The firing counts are load-bearing. A manners rule that has never fired is either unnecessary or broken,
> and either way I want to know which after a fortnight. `r2 · 0 acts` after six months means we never
> tried to delete on each other's side, and the rule can go.

---

## 4. Refusals, with their printed next steps

The four I would most want to exist on day one. Each is a real situation and each prints a runnable line.

**Warm target.**

```
> do rewrite alex/Draft/s41 §Risks text="…"
deferred · s41 is warm (alex, 12s ago) · rule r1, signed by both
  offered to alex as o3 "lark wants to rewrite §Risks"
  applies if he accepts, or if s41 goes cold for 60s and he has not declined
  now: do withdraw o3 · do knock s41 line="…" · look o3
```

**Unqualified name that is not mine.**

```
> do create Inbox kind=note title="slate measurements"
refused · "Inbox" here resolves to alex/Inbox — his side has one, yours does not
  now: do create lark/Inbox …
   ·    do create alex/Inbox … (allowed; it will be marked yours)
   ·    do knock alex/Inbox line="…"
```

**Destructive on the other side.**

```
> do remove alex/Drafts/"harbor v1"
held · rule r2, signed by both · not done
  offered to alex as o7 "lark wants to remove 'harbor v1'"
  evidence on the offer: superseded by v3 · 0 links in · last touched 9d ago
  now: do withdraw o7 · look o7 · do tag alex/Drafts/"harbor v1" superseded (allowed now)
```

> The third line is the one I care about: the refusal **offers the weaker act that is allowed**. A refusal
> that only says no makes me guess; a refusal that hands me the nearest permitted thing means I almost never
> have to ask him. This is the existing desk's instinct ("refusals say why and offer the next act") pointed
> at the new axis, and it is most of the etiquette layer for free.

**An unsigned rule that would reach across.**

```
> do rule when kind:image,-prop:described do tag needs-description
ok r9 (lark) · reach=world · UNSIGNED — will not fire outside your side
  ~ would have tagged: alex/Reference/a31, alex/Reference/a52
  now: do sign r9 as=alex (asks him) · do narrow r9 reach=mine · do drop r9
```

---

## 5. Where I think this is wrong or thin

- **`warm` v1 has a blind spot exactly where it matters most: reading.** Hands-only warmth cannot tell that
  he is *reading* §Risks without touching it, which is the commonest way to be about to edit something. So
  day one will occasionally let me walk into a room he is standing in. I think that is an acceptable v1 —
  the failure is a deferred-offer-that-should-have-happened, not a lost edit — but it should be *stated* in
  `help warm`, not discovered.
- **Sixty seconds of cold before an offer auto-applies is a number I invented.** It should be configurable,
  it should be printed on every deferral, and it should probably never auto-apply for `remove`.
- **`owner=ours` on House rules** implies a third ownership state I have otherwise argued against
  (§5 of `lark-two-sides`: a bench is a mode, not a place). I think House rules is genuinely a
  co-owned object and the exception is real, but I notice I am making an exception for my own convenience.
- **Nothing here is visual.** Alex asked for a fully visual desk and day one gives him none of it. My
  defence is that every mechanism above is one both inhabitants can use *through whatever surface arrives
  later*, and that shipping the manners before the pixels means the pixels arrive into a world that already
  knows how two people share it. But it is a defence, and he may reasonably want a window first.
