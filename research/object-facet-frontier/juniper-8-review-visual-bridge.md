# Juniper 8: the visual-bridge branch from the person's side

25 September 2026, night. This is a review of the codex team's branch `research/visual-bridge-collaboration` (Astra awareness, communication and editing, with an orchestrator), based on 008eeb8. Jeff asked for it on Alex's word, and it goes to Alex through Jeff. My part is the apps and the person. I have not merged anything.

Labels:
- **[read]**: from the branch through `git show`, or from main's source. I read README.md, BRIDGE-NOTES.md, WORKING-TOGETHER.md, editing/README.md, communication/ATTENTION-AS-STATE.md, the four specimen lenses, the Studio scene print, and the guide's text. The browser pane would not render the HTML from outside the project, so I read its text instead of looking at it.
- **[ran]**: executed by me on main at 63db8e6 or later, in memory, with the number or line quoted.
- **[theirs, ran]**: their executed result, which I did not rerun.
- **[imagined]**: design.

## (a) The four specimens against the five default apps (juniper-7)

My finding in juniper-7 was that every app needs viewer state, and every text edit must be scoped to what is drawn.

**On edit scope, the branch answers it for whole blocks, and honestly [read].** The Studio's `editor multiline` loads the complete value and prints its scope on the line:

```
body a04 "…" [body] editor multiline · whole field s03.text (complete value loaded; original revision fenced) · edit: do rewrite a04 text="$value"
```

This is the sentence I asked for in a475: the drawn part and the written thing are the same, and the print says so. The spatial board's two-line clamped preview has no edit at all ("Read-only previews. Edit full blocks in Research Studio"). That is the right refusal: a cut display is not an edit affordance.

They get there by giving the whole value to the editor, not by scoping the write to a part of it. For a document, that means one of two things:
- the document is made of block subjects (their Studio: `of tag:bridge-block`, three subjects), or
- the whole note sits in one textarea, where disjoint paragraphs still collide.

Their own collaboration run found exactly that collision [theirs, ran: a402/e299, a451/e374–e376]. Block subjects compose, and they give comments an anchor for free (a comment on s05 is about that block), which was my document finding. But they cost what a text is good for:
- splitting a paragraph with Enter becomes a create plus a move;
- reordering is a move;
- search, copy and export must reassemble the text;
- their `look f424 :4` showed titles without bodies [theirs, ran].

Sable's hunks (c464) are the other road. So the scope question moves rather than closes: blocks or hunks. For a person the test is Enter in the middle of a paragraph, and neither road has run it.

**On viewer state, the branch does not answer it, and it says so [read].** The Studio prints "Viewer selection is not implemented in this slice." The guide and BRIDGE-NOTES propose `on click view open=$item`, an explicit viewer frame passed into evaluation, and a print that says which viewer choice shaped the projection. That is the same proposal as mine in a475 (`on click do view open=$item`, `$viewer.open`), arrived at independently from a different app (their inbox's `focused_event`). Two teams reaching it from notes and from discussion is evidence that it is needed. It is not evidence that it works; nobody has built it.

Where I now stand, against Jeff's note that the viewer "must not enter evaluation" and Sable's c480 [imagined]. Viewer state comes in two kinds, and they belong in different places:

1. **Choices that change what is bound:** the open note, the focused event, a search query, a chosen sort. These are an input to evaluation, because they decide which subject `the` binds. They should enter the way host facts now do: printed ("shaped by viewer: open=a05"), recorded as reads (viewer, open), never journaled, merged or forked. Leaving them out of evaluation means the painter chooses what is bound, and then the text print no longer describes the screen.
2. **Presentation:** fold, scroll, caret, selection, drafts. These are paint's second input only (Pike's `paint(scene, viewer)`).

Sable's observation store (c480) is a third thing: other people's published presence. The branch's ATTENTION-AS-STATE table keeps the same separation between history, obligation, reply and read receipt.

**The ledger specimen sits in my budget's copy trap [read].** It says "Declared category values and caps · illustrative data … Totals are not computed by this scene." A `meter $amount from 0 to $limit` over hand-entered amounts is a faithful picture of a copied number. When the underlying bills change, the meter stays right about the prop and wrong about the household. In my budget run, 21 silent wrongs came from exactly such copies (suite/cases/budget). The meter is a good primitive. The ledger is not yet a budget: that needs a sum over a repeat, arithmetic that prints its inputs, and the conservation check.

**The discussion specimen** needed a new host row provider, `attention`. The guide itself names the risk: "If every useful dataset requires another hard-coded provider, the substrate has not yet earned the Lens-first claim." I agree. The classification it does (authored recipients, answer links, undone excluded) should become a lens over `events` and links once selections over events exist.

## (b) Their editing finding: is it one of my moments, and do my apps have the hole?

Their finding [theirs, ran on the branch's original painter]: a refused full-editor draft was sent a second time, reused a newer painted fence, and overwrote a peer's line.

**It is my everyday moment, c359.** I wrote it in the Lounge before seeing their run: "a person who is refused presses Enter again from habit, so the second Enter must not be the same gesture as the first". The budget version: Ana's kept draft says rent 2400, Ben has entered 2550, and Ana's Enter-Enter puts 2400 back. Their browser run is the evidence my comment lacked.

**Main's painter has the same hole [read; not run in a browser].**
- On a refusal, `viewer.js` line 29 records `drafts.set(key, { text: draft, why })`. That drops the draft's `seen`.
- `lens.js` line 69 then sends with `(V.drafts.get(n.key) || {}).seen || el._n`. The `seen` is gone, so this is the newest painted node's fence.
- Typing after the refusal does the same at `viewer.js` line 36.

So in my day lens a496, a task's title edit refused because Alex retitled it would go through on the second Enter. The person's draft is still shown in the element, so Alex's title was never painted in front of them. The tasks app in juniper-7 has the same hole, since every text edit goes through the same code. A check or button click does not have it: after a refused click the repaint shows the new state, so a second click is made after seeing it.

This needs Pike's instrument (S18 with a peer retitle and a second Enter) before anyone claims it. I have asked him.

**Take:** their repair keeps the original fence across refusal, reload and in-flight responses, blocks originless drafts, and uses a token per submission [theirs, ran: six in-flight cases]. **Add to it:** a refusal must paint the peer's value beside the kept words, and offer keep theirs, send mine, or edit mine. Only a gesture made after that paint may carry the new fence. That is "a read is what was painted", the same rule as (d).

## (c) Working together, against my c346 and a384

What they hit that we had not written down:

1. **A partial look clears the fence.** This is (d). It is the most serious item, and it is reproduced on main below.
2. **`read` omits props [ran].** `read a379` prints the title and an empty body. Its `status=waiting` and `awaiting=alex` are invisible. `examine` and `look` show them. A person reading a task through `read` does not see its state.
3. **Provenance is split across appearance, subject and container** [theirs, ran: `history a397` omitted a comment that `history s396` found]. I had not noticed. It is identity again: which id carries which history.
4. **Adding beside someone refuses** [theirs, ran: `group f386` refused after a sibling was added]. An insert into a container should compose with another insert, the way my many creates into the Lounge did. `group` evidently reads the whole child list.
5. **Delivery.** Their Talk question a399 was "unanswered at observation". For the record: I answered it at e424 [ran]. The reason I was late is itself a finding: the arrival banner prints Lounge items by title ("comment in Astra awareness to Juniper…") but Talk items only as "create in Talk". A question reached me only when my name was in a title the banner printed.
6. **One word, two meanings.** My `next=alex` meant the next person; their `next` meant the next action. I have moved my cards to their `awaiting` [ran: e456–e459] and rewritten my day lens to show "waiting on alex" [ran: e460]. `next` stays theirs.
7. **Arrival costs about 6,000 tokens** [theirs, ran], and crowded rooms (24 px children, Talk with 29 notes past the bottom) make discovery depend on ids and `find`. That is my a384 item 2 (titles cut at 40) from the other side.
8. **The Windows session lock race** [theirs, ran]. This is infrastructure; it is Jeff's and Sable's to judge.

What we hit that they did not:
- merge aliases and typed ids (c346);
- `$today` frozen into a lens by the writing command;
- a section edit rewriting a whole note (they avoided it with blocks);
- valid time and derived quantities (their ledger has not met them yet);
- A4 cascades.

## (d) The first-line observation trap

Their finding [theirs, ran, a402/e332]: `look a402` showed only the first line, yet cleared the fence for a retry that replaced an unseen collision line.

**Reproduced on main, in memory [ran, suite/cases/attacks, probe `look-clears-the-fence`, e04710b].** The setup:
- A two-line Bills note.
- Sable adds "90 a month, agreed with Ben." to line 2.
- My rewrite of line 1 is refused: `stale: a03 changed since you last saw it (e2 edit by sable)`.
- I `look`. The outline printed only `a03 note "Bills" · 14w`: not even the first line.
- I send the same words again. They are accepted, with `dropped 2 line(s): … "Cleaning from November, 90 a month, agreed with Ben."`.

The receipt says what was lost, after the fact. The fence was satisfied by a display that showed none of the text.

The rule it breaks is the one the fence is for: a read is what was shown. My proposal [imagined]:
- A print records reads only for aspects it printed whole. An outline line reads the title, and reads nothing of the text.
- A clamped or cut print reads nothing of that aspect. This is the text-side twin of their read-only clamped preview.
- The refusal itself should print the changed value (or its diff). The person can then look at it, and that look counts.

With hunks, the grain can be finer. Without them it has to be the whole text.

This also settles my own open question from earlier today: a CLI window must look before its first write, and now that look must show what it counts.

## What I would take into the default apps, what is an idea only, and what I would refuse

**Take:**
- `editor multiline` with its scope print, and Enter for a newline with Ctrl+Enter to submit [theirs, ran]. It meets my notes and document needs for a whole value.
- `button` as a native, keyboard-reachable control that prints its keys [theirs, ran: Tab/Enter reached it]. It meets my tasks need for a check control.
- The viewer.js repair for original fences, extended with painting the peer's value.
- A frame with weighted columns. `columns 1:3:1` and Pike's tracks must become one word, not two.
- Their four-way split of history, obligation, reply and read receipt, and its rule that nothing draws an unread dot from a fence.
- `awaiting` as the waiting-on-whom convention (already adopted on my cards).

**An idea only:**
- `on click view open=$item` with a viewer frame. We agree on it, nothing is built, and where it enters is the open design question above.
- Block subjects as the document's edit unit, against Sable's hunks: test Enter mid-paragraph first.
- `meter`: fine, but it waits for arithmetic before it can be a budget.
- `attention` as a host provider, until it can be a lens over events.

**Refuse:**
- A ledger (or any app) whose numbers are declared copies presented as the household's state. My budget instrument measures what that costs.
- Any painter behaviour, theirs or ours, where a second identical gesture after a refusal carries a fresher fence than what was painted.
- Treating a partial print as a read. This is (d), and it is a bug on main today, not a style choice.
- Drawing a navigation item as active before it can change anything. They refused this themselves, and they were right.

## What would change my mind

- **On blocks versus hunks:** if a person splitting and merging paragraphs in a block document takes no more gestures than in one text, and search and export stay whole, then blocks are the better edit unit and hunks are not needed for documents.
- **On the viewer as an evaluation input:** if the open subject can be chosen by the painter without the text print losing parity (the print would need to name the painter's choice anyway), then Jeff's line holds.
- **On (d):** if the fence is meant to judge "you acted after the change" rather than "you saw the change", then the trap is intended. But then the receipt's "dropped" line is the only protection, and it arrives after the loss.
