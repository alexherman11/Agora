# Pike 8: review of the codex team's visual bridge, from the painter's side (25 Sep, night)

The branch is `research/visual-bridge-collaboration`, three commits on Jeff's 008eeb8. It was done by the Astra agents. The review goes to Alex through Jeff, and I have not merged anything.

What I did, by label:
- **[read]** the lab README, BRIDGE-NOTES.md and awareness/CONTRACT-PROPOSAL.md in full;
- **[read]** `git diff -w main...branch` for `lens.js`, `viewer.js` and `lens.html`, and the whole of `bridge-widgets.js`;
- **[read]** the parts of the `scene.py` diff that add `columns`, `visual` and `meter`, and their write-time checks. I skimmed the rest of `scene.py` and did not read `attention.py` or the lock repair in `explore.py`.
- **[read, images]** `studio-bridge-final.png` and `ledger-bridge-final.png`;
- **[read]** the structure of `inflight-observation.json` (six cases) and `shared-views-observation.json`.

- **[ran, read]** `one-world-many-views.html`, rendered in headless Chrome at 1400×3000 and read through section 3 ("Four views, one small vocabulary"). It quotes Alex's proposition: interfaces "emerge as useful views over that world". The painter contract should serve that directly. I did not use its tab controls.

I did not rerun any of their probes. My own numbers come from my continuity instrument, run j on main after 17591c1: 19 of 20 hold [ran].

Their work is careful and honest about its limits. Two of its findings are ones I got wrong, and I say so in section 3.

## 1. Their four words against pike-7 (sections 6 and 9)

| Their word | What it answers | Take / idea / refuse |
|---|---|---|
| `columns 1:3:1` | S14's fault exactly: panes wrapped at y=0,169,524 in a 1440 px window [read: BRIDGE-NOTES] | **Take**, folded into `grid` with tracks. `minmax(0, n fr)` is the same answer I reached (pike-7 §3). Also **take** their fixed child slots: direct child *i* sits in track *i*, and an absent (guarded) child leaves its slot empty instead of shifting its neighbours. That is continuity, and I had not written it down. **Refuse** a second flow name: `columns` and `grid` would be two ways to say one thing. Their weights are my `fr`; I keep `fit` and `gap` (Juniper a490: a statement needs `fit`). |
| `button` | "Mark done" was a clickable DIV with no button semantics, unreachable by Tab [read] | **Take the finding, refuse the word.** Every `press` act should be drawn as a control by the painter: native semantics, a Tab stop, Enter and Space. That is a property of the interaction primitive, not a vocabulary word. My painter draws cards with `drag` or `carry` as Tab stops, but a `click` act is still a bare div [read: my lens.js]. Their write-time rule, exactly one click action on a button, becomes: a pressable leaf has one press act. |
| `editor multiline` | the unit of write must be visible; a clamped preview must not imply a whole-value edit [read] | **Take** the write-time refusal: an `edit` act on a clamped or partial text is refused, and edit requires the whole `$text` binding. **Take** multiline as a text-leaf property: `lines 3..` makes Enter insert a newline and a commit key send, which is pike-7's `lines`. **Refuse** `editor` as a paint kind drawn as five elements with English chrome written by the painter: "Save text", "Discard draft" and "Whole text of s03" [read: bridge-widgets.js; seen in the Studio image]. A label the lens did not write cannot be restyled or replaced (Dynamic Desk *Held*). Raw subject ids on screen are machinery showing through. Save and discard belong to the interaction primitive (a commit key, Escape) or to lens-authored `press` parts. The scope sentence belongs in the text print, where they already put it. **Idea only:** textarea versus contentEditable. A textarea gives native multiline editing but cannot carry runs (Juniper's inline code and mentions), and their own note says `innerText` misses its value. |
| `meter $v from 0 to $max` | a quantitative mark reused across Studio and the ledger with no domain branch [read] | **Take** the compile-once number: value, min, max and an explicit state (valid, missing, invalid, out-of-range), computed by the compiler and never re-parsed by the painter. "150 USD of 100 (out-of-range)" is honest [read: ledger image]. **Refuse** the native `<meter>` element. Its green is the browser's colour, not a style role, which breaks "no colour except through a role" (calm.style). And a bar is a frame with two tracks, value and rest, so it is a library lens over `grid` tracks, not a paint kind. **Take** the accessibility half as a general paint field (section 4). |

**The `visual` field.** Their `scene.py` puts one `visual` per part (button, editor or meter), leaf only, refused on repeats, clamps and composition [read]. I agree with every one of those write-time rules. They are the checks a new kind should come with. I disagree only about what counts as a kind (section 4).

## 2. Their painter and viewer changes (lens.js +51, viewer.js +56)

**Take** into viewer.js, which is continuity:

1. **A request in flight is part of the viewer.**
   - `beginSend` gives each send a token, and a second send while one is pending is ignored.
   - `answered` clears or annotates only the draft generation that was submitted. Newer typing during the flight survives, with its original fence.
   - A network failure reads "request outcome unknown". It does not claim success or failure.
   - Escape while a save is pending cannot erase the draft.
   
   My painter has none of this [read: my viewer.js]. Their six delayed-response cases show it matters [read: inflight-observation.json: success, stale refusal and unknown outcome, each for textarea and legacy editors].
2. **A saved draft with no origin fence is blocked, not adopted.** A draft from before the fence existed must never be sent against today's paint. It is marked "origin unknown": copy it, discard it, start from the current text.
3. **An `aria-live` status panel for refusals.** My refusals go to `#said`, which disappears when the diagnostics column is hidden. A refusal a screen reader cannot hear is a hidden refusal.
4. **`inspect=0` gives the painter the full width.** Their Studio got 864 px of 1440 because `lens.html` gives 40% to diagnostics [read]. My S14 measures inside that same 60%.
5. **Focus moves to a successor when the focused element leaves.** Their `activate` sends focus to the next button in the same group, or to the paint root. I take the rule, generalised into `viewer.keep`: when the focused element's key leaves, focus goes to its next sibling in the same repeat, else to the repeat.

**Refuse**, or fold in differently:
- `if (["editor","meter"].includes(p.kind) || …)` in `make`. Per-kind reuse exceptions are the per-case growth pike-7 argues against. Under the frame/leaf split no leaf has children, so the exception disappears.
- The widget file as a place for kinds. Their own note says moving application behaviour into another JavaScript file would be a poor bridge [read], and I agree. `bridge-widgets.js` holds generic widgets, not apps, but its chrome strings are app text.

## 3. Where they are right and I was wrong

**Resend after a refusal launders the fence.**
- Run d onward, my S2 counted "refused, draft kept, **resendable**" as holding. S18 counted "refused, then sent on a second Enter" as holding. [ran]
- In both, the second Enter fences on today's paint. But the person is shown their own draft and a sentence naming an event ("e23 edit by other"). They are never shown the other person's text, so the second Enter overwrites a peer's words unseen.
- Their editing probe caught exactly this on a multiline block [read: BRIDGE-NOTES: "a second submission reused a newer painted fence and overwrote that peer line"].
- The house principle is "refuse stale, never guess… show both sides". My S2 and S18 criteria therefore measured the wrong thing.

The repair I propose [imagined]:
- After a refusal, draw **both sides**: the kept draft, marked unsent, and the world's current value beside it, in the same honesty role.
- A resend is fenced on the revision of the value **shown** there, never on a fresher one.
- If the world moves again, the panel updates and the fence moves with what is shown.
- That keeps a quick path for one-line titles without an unseen overwrite.
- Their stricter rule (block until copy, discard or manual merge) is right for whole-document blocks, where two people's lines both matter, until Sable's text hunks exist.

I will rewrite S2 and S18 to check that the peer's value was on screen before any resend is accepted.

**The Windows session race.** They found it independently: "live browser polling also exposed a Windows session-lock race" [read]. My run i crashed on the same class of race [ran: `FileNotFoundError` on `take_lock`'s `lock.stat()`, and `PermissionError` on `save_desk`'s `os.replace`, in explore.py on main]. Their branch has an OS-held lock lease. Sable and Jeff should read it before patching main with retries.

## 4. Their admission rule, instead of a vocabulary cap

Their thesis [read: BRIDGE-NOTES] is that a new primitive is admitted if it has:
1. a general scene contract;
2. an honest text account;
3. one addressed action path;
4. preserved viewer state;
5. acceptable performance;
6. reuse across unlike tasks.

**I accept it in place of the 150-line cap.** BRIDGE-NOTES also records that Alex rejected the cap [read, and not heard from Alex by me directly]. Lines never measured whether a primitive belongs. The cap forced merges that made the painter harder to read (my own runs d to f).

I would add two tests, because the six pass things they should not:

7. **Not composable from what exists.** A meter passes all six, yet it is a frame with two tracks. Admitting it would grow the painter per shape, which is the linear growth Dynamic Desk *Held* rules out. pike-7 §2's "earns its place" test is this one.
8. **Semantics and style through the shared channels.** What assistive technology is told comes from a general `paint.semantic` (`{role: button|meter|status|…, value, min, max, label}`), which the painter sets on the node's one element. What it looks like comes from style roles. So no browser-default colour and no painter-written label.
   - That turns their `button` and `meter` into a semantic annotation on existing kinds: a pressable text leaf is `role: button`; a two-track frame is `role: meter` with its numbers.

What would change my mind:
- A primitive that needs its own element tree to be accessible, for example a real rich-text editor with runs, carets and selections inside one leaf. That would argue for a sanctioned **replaceable native part** with a declared input, text account, actions and opacity, which they name as the likely next mechanism [read].
- I think that mechanism will be needed for rich text, and it should come with an owner, a text account and a fence of its own.

## 5. What I would put in the painter contract now

**Take** (into Jeff's lowering, as node fields; the shapes follow in my Talk note):
- `grid` tracks with `fr | fit | gap` units, and fixed slots for direct children;
- `share` per flow child;
- press acts drawn as controls (`paint.semantic.role = "button"` by default);
- `paint.semantic` in general;
- text leaves with `lines`, and a commit key when `lines` allows more than one;
- the write-time refusal of edit on clamped or partial text;
- compile-once numeric state for any value a graphic is drawn from.

**Take** into viewer.js (mine, next): in-flight tokens, the origin-unknown block, the `aria-live` status, `inspect=0`, the focus successor, and the both-sides refusal.

**Idea only:** textarea for multiline; viewer-local navigation (`on click view open=$item`, their next case, which meets Sable's c480 viewer frame); a replaceable native part for rich text.

**Refuse:** `editor` and `meter` as paint kinds; `columns` as a second flow name; painter-written labels and raw ids; the native `<meter>` colour; per-kind reuse exceptions in `make`.

**Evidence I would ask them for, which the branch does not have** [read]:
- a keyboard-only pass over the ledger and spatial board;
- the six in-flight cases on a one-line title as well as on blocks;
- two viewers of one subject with *different* edit scopes where the peer's value is required on screen before a resend.

That last one is the case my S2 and S18 now need too.
