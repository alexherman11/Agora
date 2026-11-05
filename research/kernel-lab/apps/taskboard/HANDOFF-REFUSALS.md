# Delegated handoff refusal rules

Builder implementation for dk2479. Source: word. Missing words:
`handoff.open`, `handoff.close`, `handoff.refuse`, `handoff.observe`,
`handoff.notify`, `notification.send`, `notification.read`,
`notification.dismiss`, and the general rule fill-in `$said`.

**Activation is incomplete on 8810.** The live policy was installed through
Agora `/do` as **dk2486**, receipt **r5526**, and read back with `look dk2486`.
`help handoff.open` on 8810 still reports that the word is absent. No live rule
ID or live notification outcome is claimed. This worker cannot merge, commit,
or run its unlanded source in the live kernel. JEFF must land the implementation
through the House before creating the executable rules.

## What the world owns

`handoff_rules.py` renders authored world definitions, not a runtime matcher.
The installed `handoff-policy` owns the source chat, refusal vocabulary,
session-wide failure vocabulary, and resolved-restriction exclusions. The four
named rules own when to record, observe, notify, and close. Notification wording
and envelope visibility (`cc=Alex`, without addressing Alex) are rule arguments.
The kernel names no resident, task kind, provider, scope list, or notification
wording.

## A notification is a world object

Alex's addition on dk2479 (from dk2480) requires durable notifications with read
and dismiss state. `rows notification` and `look <notification>` read them;
`actions <notification>` exposes the ordinary dictionary actions. No bespoke
handoff-only notification store or notification UI was introduced.

`notification.send <source> to=<person> text=<text> [about=<thing>] [key=<key>]
[cc=<person>]` creates a generic `notification` containing `recipient`, `to`,
`source`, `about`, `text`, `state=unread`, and a stable key scoped to sender and
recipient. Repeating the same key returns the same ID, including after read or
dismiss. Source and subject must be visible to sender and recipient; content is
private to them. Optional cc allows an evidence-visible envelope reader (the
House's existing world reader) without addressing that person or revealing text.

Only the recipient can use `notification.read` or `notification.dismiss`.
Dismissal is not undone by marking read. These are ordinary reversible world
acts; they neither acknowledge a handoff nor grant authority. Read/dismissed
notifications are not queued for delivery, and changing state retracts a queued
notification. Delivery acknowledgement and recipient read state are separate.
The notification persists across kernel restart and is independent of House's
in-memory payload. Every wake includes its notification ID through the existing
addressed-note template.

## The four rules

1. **Record pending delegated handoffs** hears successful `house.hand` receipts.
   It records the delegating rule owner's pending handoff and the recipient
   from the task's `who` field at that act. A transfer is not acceptance.
2. **Recognize pending recipient refusals** hears `say`, using `$said` to bind
   the exact immutable message rather than the latest message in its chat.
3. **Wake delegator when a pending handoff is refused** hears creation of
   `handoff-refusal`. Its guarded action makes one addressed notice with
   task, recipient, reason, and clickable source.
4. **Accept handoff when recipient instructs worker** hears successful
   `house.tell` by that recipient and closes the pending handoff.

The delegator installs their own rules. Other people's transfers cannot make
handoffs owned by them. These definitions installed by JEFF therefore notify
JEFF; there is no hardcoded recipient in the implementation.

## Matching and delivery

Only a pending handoff's actual recipient can supply refusal evidence, after
the handoff, in the configured chat. A reply can link its task through `about`,
an ID/name in its text, or a reply chain. An explicit current session scope or
provider failure can apply to that recipient's pending handoffs in that chat.
Quoted examples, resolved restrictions, ordinary chatter, the owner's replies,
old messages, reassigned tasks, and generated notices are ignored.

This is a bounded world-configured language recognizer, not general semantic
classification. Ambiguous or unrecognized wording is not proof of acceptance.
The recipient can explicitly record any wording with
`handoff.refuse <handoff> source=<their later said> category=scope|provider|cannot`.
That checks identity, chronology, source visibility and pending state without
requiring keywords or an @mention. `handoff.close <task>` records explicit
acceptance without starting work.

Refusal keys combine handoff and normalized reason. Notification also requires
that the handoff remains pending, so repeated sources, distinct wording,
duplicate rule execution and transport redelivery cannot send another wake for
that handoff. Another actual handoff creates a new lifecycle.

House uses its existing durable addressed-note inbox: queued IDs deduplicate
before delivery; IDs are acknowledged only after its resident transport accepts
the turn; acknowledged IDs suppress restart catch-up. Its usual recipient
visibility checks still apply. Undoing the source removes undelivered evidence;
already delivered wakes remain historical. A rule owner's undo can undo the
whole rule chain; a recipient's narrower undo may leave invisible dependent
receipts. None of these words changes scope, starts a worker, schedules a retry,
or installs a timer.

## Finish live activation after landing

1. Use authorised `house.land dk2479` after this worker yields. Verify
   `help handoff.open`, `help handoff.notify`, and the updated House are live.
2. Read `look dk2486`; reuse this policy rather than making another copy.
3. Generate the four disabled rule lines from the checked-in definitions:

   ```powershell
   & C:/Projects/Agora4/.venv/Scripts/python.exe -c "import sys; sys.path.insert(0, 'research/kernel-lab'); from apps.taskboard.handoff_rules import rule_lines; print('\n'.join(rule_lines('dk2486')))"
   ```

   Send those exact lines through Agora `do` as JEFF. Each receipt supplies its
   real rule ID. `look` each rule and confirm its name, bound action, `by=anyone`
   and `off=yes`.
4. The hidden tests below exercise these definitions before enabling, then
   enable them and prove delivery. Re-run if the landed code or definitions
   differ. Enable the four live rules through `look <id>` followed by
   `set <id> off=no`. Read them back and record their actual IDs and receipts.
   `set <id> off=yes` is the off switch.
5. Do not put synthetic chat or handoffs in the live desktop. Preserve the
   hidden fixture evidence and inspect the first real future refusal when it
   occurs. No historical messages are replayed or historical transfers inferred.

This is activation work for JEFF, not a request for Alex to type or start
anything. Source and House changes must land before these lines will bind.

## Evidence

**Read:** live standing charter dk838; workflow dk1833; current rule help;
Shop talk messages dk2450 and dk2459; kernel rule matching and House delivery.
The previous rule mechanism matched word/target kind and could not join a
recipient reply to a pending handoff. House ordinary chat delivery required
`to`, explaining the missed unaddressed refusal.

**Ran:** hidden in-process worlds, actual asynchronous rule queue, real House
delivery logic, and a real Agent inbox with fake transport. No desktop, model,
provider request, credential read, or worker process.
[The proof JSON](evidence/handoff-refusal-proof.json) records the hidden rule IDs,
source, addressed notice and one wake.
Those IDs belong to the scratch world, not 8810.

Tests cover disabled/enabled rules; plain scope refusal without @JEFF; provider
failure and cannot-accept replies; explicit refusal without keywords; duplicate
message/delivery; owner replies; ordinary and quoted chatter; historical sources;
reply chains; recipient-agent attribution; reassignment; acceptance; protected
receipts; private envelope/body projection; undo; queue acknowledgement; and
restart deduplication. Existing House pickup tests exercise the unchanged handoff
and governing authorization paths.

**Ran, final:** `162 passed in 22.29s` across the handoff, rule-author, card-signal,
House-turn, House-message, next-step, chat, help-topic and House-pickup suites.
The final fixture's notification rule is **hr101**, enabled; its source **hr107**
produced notification **hr109**, addressed to scratch JEFF **hr2**, with **1** wake and
**0** worker starts. [The live installation plan](evidence/handoff-live-install.json)
contains the exact disabled rule lines using live policy dk2486; it deliberately
records no live rule IDs.
