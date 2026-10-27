# Writing (kernel-lab app)

*Builder draft by Claude, 27 Oct 2026, from Alex's ask: "lets make a new writing center, closely modeled off the old one but using the new component style", with two plans moved in "for me to review". Not Alex's words unless quoted.*

The old desk's Writing app (lenses `a5911 writing` and `a6079 doc-page`, exported in `old-desk/`) rebuilt as an ordinary component lens on the kernel desktop. It holds nothing of its own: documents and comments are world things, and every press says the line it runs.

## What Alex sees

- **On the dock: Writing** (a `button` with `does=window.open writing`). One click opens the window. It wears the place's theme like every window (Dusk today).
- **The rail**, as the old app had it: *Find a document* (title and text, as you type; `Ctrl+K`), then folding collections: **Plans** (Waiting, Answered; renamed from "Designs for me"), **Notes**, **Agora documentation**, **Personal writing**, **Files and unsorted** (uploaded files and documents in no collection; this replaces "Paragraph documents", which has no counterpart here). `+` on a collection starts a document in it. Newest first.
- **The top bar**: Back (`Alt+←`), Home, **New document**.
- **Home** (nothing open): plans waiting for you as cards, recently changed, a way to start.
- **A document**: its title (edit in place), who made it and when, *Draft by Claude* where it is Claude's, its word count, a link to its design page. Markdown is drawn; press a part to write in it (that part shows its marks, the rest stays drawn); `Esc`, `Ctrl+S` or leaving keeps it. `Ctrl+E` shows the whole source. `[[` opens a picker and writes `[[id|Title]]`; `[[Title]]` and `[[FILE-NAME]]` resolve too, and a link to nothing yet starts that document. Task boxes tick in the text. **Linked from** lists every document that links here.
- **A plan** has Alex's call on it, as the old design review did: *Build it*, *Build it, with my comments*, *Not yet, I have questions*, *Wrong shape*, and *Back to waiting*. *Still open* shows what is not answered.
- **Comments**: select words, right-click: **Comment** puts a note beside them in the margin; it says *under § heading*, *moved*, *changed* or *gone* as the text changes (the old desk's ONE RULE, measured on the drawn words). Reply, Resolve, Reopen.
- **JEFF**: right-click selected words (or a part), **Send to JEFF**; or **Send to JEFF** on the whole document; or **JEFF** on a comment. It says a line in his **Conversation**, as Alex, with the passage quoted and a `[[link]]` back, and `about=` the document. **Sent to JEFF** under the document lists what went.
- Right-click menus end with the world's *Ask for a change…* box (`right_click=ask`), as every painter menu does.

## Things and words

| Thing | Facts |
|---|---|
| `kind=document` (the world's existing kind, "Keep useful information together") | `title`, `text` (Markdown), `collection=plans\|notes\|documentation\|personal`; a plan adds `plan=waiting\|answered`, `verdict=build\|changes\|questions\|wrong`, `still_open`, `page`; `drafted_by=Claude` marks what is not Alex's; `source=` the repository file it came from |
| `kind=note` | the world's notes (the Rough spots) show under Notes and edit the same way |
| `kind=comment` (new, declared with help) | `about=` the document, `quote`, `before`, `after`, `heading`, `text`, `reply_to`, `resolved=yes` |

Why `document`: it already exists and means what this is; the files module also makes `document`s for uploaded files' pages, which the rail shows read-only under *Files and unsorted*. Why a new `comment`: no kind meant a remark on some words (`board.reply` is for posts; `say` drops `quote=`).

Gesture lines (all in `writing.lens`): `set $d.id text=…`, `set $d.id title=…`, `set $d.id collection=…`, `set $d.id plan=answered verdict=…`, `make kind=document …`, `make kind=comment about=$d.id quote=… text=…`, `say Conversation text=… about=$d.id`, `set $c.id resolved=yes`, `forget $d.id`. Edits carry the document's revision: a change made meanwhile refuses the save, and the words are kept on the page to add again.

## Files

| File | |
|---|---|
| `writing-components.js` | seven components: `writing-shell`, `doc-rail`, `doc-shelf`, `doc-row`, `doc-home`, `doc-page`, `doc-comment` (Markdown parser and drawing, block editing, link picker, comment anchoring, menus and composer) |
| `writing.lens` | the window's arrangement: collections, home, the open document, every gesture line |
| `install.py` | the comment kind, component cards (reviewed with `component`), lens, widget with grants, dock button, the two plans and a short guide; `--live` or `--door <sandbox>`; opens nothing |
| `sandbox_here.py`, `look.py`, `proof.py` | a hidden copy of the live world in this process (house off, no model), a headless window, the walk below |
| `old-desk/` | the old app's lenses and notes, read-only exports |

## Evidence

- **ran** `proof.py`, 27 Oct, hidden copy of the live world, headless browser signed in as Alex: **18 of 18 steps pass** (`evidence/proof-output.txt`): home; a plan opens with its 8 tables and its call; `[[MOVING-IN]]` resolves and opens; Linked from; Back; select + right-click + Comment (marked, "under § The short version"); select + Send to JEFF (a `said` in the Conversation, quoted, `about=`); the whole document to JEFF ("Sent to JEFF · 2"); a plan's call and Back to waiting; a new document named, written in place with `[[` picking *Shedding clutter*; a task box; `Ctrl+E` source and back; editing commented words turns the comment to "changed"; Resolve; Find; the guide; Home's order; no script errors. Pictures: `evidence/proof-*.png` (looked at).
- **not verified**: the window on Alex's real screen (WebView2) and its dock icon; two people writing one document at once; a phone; very long documents (the plan of 3,968 words projects in about 90 ms, with the whole text carried in each gesture's environment).

## Rough spots (frictions; no source outside this folder was edited)

1. **A Conversation line cannot carry a quote.** `say` keeps `about=` but drops `quote=`, so the passage travels inside the text as a Markdown quote. Missing: `say … quote=` (or `about=` plus a quoted span) that jeff-chat can draw as "Answering: …". The conversation-draft's `quote`/`reply_to` is only for answering a said line, so the window sends rather than preparing JEFF's composer.
2. **No word opens a web address.** A plan's design page (claude.ai) can only be shown and copied. Missing: `window.open url=<https…>` for the person's own browser, admitted per person.
3. **The dock draws a plain plate for Writing.** The dock picks an icon from the lens name (`shell-kit.js` `appOf`); a button's `icon=` fact is not read. Missing: an `icon=` the dock honours, or an app-icon thing.
4. **`api.part` writes `null` attributes as the string "null"** (`readonly="null"` made the title read-only). The components avoid passing nulls. Missing: the painter's `el` skipping null and false, as most element helpers do.
5. **A said line is not bound into the view**, so sending to JEFF repaints nothing; the page re-reads `rows said about=` itself, uncached (`api.rows`), because `api.read` is cached per paint.
6. **Editing focus survives a repaint, `change` does not.** The painter hands a focused input's value to the new element, which then never fires `change`; the title saves on Enter and blur instead.
7. **No exclusion in a lens query.** The old "Notes" was `-prop:collection`; here `prop:collection=` (empty) matches the absent fact, which is enough, but there is no `-prop:` for "not this value".
8. **Plans' state is a fact the page sets, not a workflow.** "Answered except T1" is `plan=answered still_open=…`; a per-question state would need each question as its own thing.
