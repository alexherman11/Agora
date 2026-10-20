# Reader acceptance handoff — a6460, 20 Oct 2026

The source and world drafts are preserved on worker/a6460. They are **not live**.
JEFF c6765 authorizes source ready without sandbox acceptance; the house merges
main and judges. Visual acceptance is delegated to a browser-capable Claude
worker after landing. Do not interpret the scene playtest as painter acceptance.

## Current decision and checks (20 Oct, supersedes earlier blockers)

- **Read:** JEFF c6765/e13070: set ready, do not merge; house returns unresolved
  conflicts as file edits. Apply world half only after source landing, through
  native Desk MCP, one command at a time. Stop at a refusal.
- **Ran:** `test_reach.py` in this worktree and the main checkout both print the
  same **4 failed** checks: repeated refusal shape row; miss row; successful
  line not recorded; rows reaches printing. Main was
  `99486b602a39f23230b104740197acc78407fdda`; its test_reach.py and verbs.py
  had no uncommitted changes. This establishes a shared failure in this
  environment, not its filesystem cause.
- **Read:** universal-chat source landed as 4e22d74. Its world application is
  being coordinated separately. Reader's installation draft now drops its
  duplicate Ask JEFF box and direct Conversation send; questions use the shared
  Conversation. Selection anchors already frame the writer note: article
  quoting=document; paragraph quoting=paragraph; both quote_in=document.
- **Ran:** the refreshed scene fixture includes a real `review=later` item;
  expected answers now respect Later / Not later. Requeueing one design
  fixture for three distinct answer checks clears its previous answered
  timestamp, avoiding a same-second duplicate-prop refusal in the test.
- Earlier browser and temp-dependent health limits below remain documented.
  No new browser run, screenshot, recording, raw-id count, or full-health pass
  is claimed.
- **Ran:** final `test_reader.py` at copy event e13082 prints `reader: ok`
  (3 tagged / 4 designs); `test_reader_words.py` prints `reader words: ok`;
  `git diff --check` exits 0. These are in-memory scene/action and expression
  checks, not visual acceptance.

## Exact delegated acceptance checklist

Use a sandbox copy only; never Alex's screen. Use Alex's 2560x1440, 150% scale.
Record the world event, source revision, commands run, shots/film paths and any
failure separately from checks merely read.

1. Save collaboration report **before and after** shots at the same viewport
   and position, including “What blocks many workers”; save a waiting design
   shot showing **Build it**, and a **Skim** shot.
2. Inspect the header: brief / For Alex / opening-prose summary, recommendation,
   question, read time, honest author or separately labelled sender, Sent time.
   Legacy missing authors/writing dates must remain explicitly unknown.
3. Inspect real Markdown headings, lists, code, quotes and tables, comfortable
   roughly 70-character measure and spacing. Check paragraph designs too.
4. Count **zero visible raw ids** in article, header, navigation and references.
   Click a prose line to activate its caret and audit again. Check a long
   reference shows only four words, full name on hover, repeated references
   become small numbered markers, and comment/event references are arrows.
   Press those links and verify the correct thing opens in the middle.
5. Wheel a long article and a long design to the bottom and back. Confirm
   scrolling stays inside the body, header and decision/navigation bar stay
   visible, outer HUD stays still, and answers remain reachable at this scale.
6. Open a waiting note, task and design in one press from waiting list and board;
   open a waiting note in Writing. Test Read/Write and Skim/Read; skim shows only
   headings and each section's first sentence, including list-first sections.
7. On the copy press Looks good, Later/Not later, Send back + note, Build it and
   Not now; inspect actual card/tag/design changes and message destinations.
   Dual-tagged designs occur once and each answer clears both waiting marks.
   Previous/Next cross the tagged/design boundary, and answering keeps the
   reader open with the next item offered.
8. With universal Conversation live beside the reader, confirm no duplicate
   Ask JEFF box; type a question and inspect its about=document context.
   Highlight article and paragraph text; comment through the Conversation;
   inspect quote/document/paragraph anchors, routing receipt, retained
   highlight and agent reply in that same Conversation.
9. Run `test_reader.py`, `test_reader_words.py`, full health and HUD playtest.
   Include the scroll group (`hud_playtest.py --only scroll --report none`)
   and universal-chat about/anchor/reply groups. Extend playtest for reader
   actions as needed. Do not claim full playtest from a scene print.

## Required live application and restore

After the house confirms reader source landing, reread the current shared
lenses through native Desk MCP. Confirm universal-chat's world half is live
before installing this reader draft without Ask JEFF. Reconcile moved passages
with a6638/search; never replace a whole shared lens from this draft.

Before any replacement, save the exact current text of **each** affected lens
and style (home-viewer, writing, home-board, waiting-on-me, home-style, review)
in a note in JEFF's corner titled **Restore: reader**. Include the precise
expected post-application text and a one-step restore verb. That verb should
read each target and replace the exact installed passage with its saved old
passage; use a stop-on-refusal batch and refuse if an installed passage moved.
Preserve concurrent edits. Newly created reader notes may remain inert after
restore; do not delete them. Name the restore command on this card.

Then read/check each exact old passage immediately before its mutation, send
one command per native Desk MCP call and inspect its receipt. Do not use
`apply.py door` for this live pass; it is only the preserved recipe/test driver.
After applying, look-only scene checks; update binder a243's pending qualifiers
and document the live reader integration, and comment what is live versus
what still awaits the checklist above.

## Latest takeover, 20 Oct, worker-a6460

Read the card/comments, notebook, live charter, current shared lenses and the
a6638/a6642 coordination. No interrupted live effect was repeated.
`git merge main` was refused at ORIG_HEAD.lock (Permission denied), before a
merge began. Main includes the a6549 scratch/wheel tools and a6642 search source;
this branch has not incorporated them. The previous documented browser
failure was not retried.

The reader now has doc-page-compatible selection anchors in both its Markdown
article and paragraph designs. The person's writer note holds `quoting=` (the
paragraph or document), `quote_in=` (the document), and `quote=` (held words).
The article keeps its held highlight; a person without a writer note can still
read. This prepares the universal chat composer from a6638; it does not prove
that chat integration live. a6638 was notified in Shop talk m6741/m6744 and asked
to include reader acceptance in its browser-capable run. The reader's requested
Ask JEFF answer remains until the combined experience is live and checked.

Header attribution is now explicit: `by=`/`author=` are authorship; `sent_by=`
is labelled “Sent by”; otherwise it says “Author not recorded”. `owner=` is
never credited as authorship. The tag/design timestamp is labelled “Sent”;
original writing dates remain unavailable for legacy documents without them.

Ran on the refreshed copy at e12976: `test_reader.py` prints `reader: ok`
(3 tagged items, 4 designs after adding one copy-only dual-marked fixture),
including article selection, paragraph/document anchors, retained highlight,
rendering without a writer, honest author/sender labels, unique queue positions
and all three answers clearing both waiting marks. The words test
prints `reader words: ok`; `git diff --check` passes. Native Desk MCP preflight
found all ten exact old passages once; that read is not a live application.
The final rerun includes the attribution and dual-marked-design checks.
The dual-marked design case matters because the universal `review` verb tags
designs too: the old reader counted such a design twice and left its tag behind
after Build it / Not now / Send back. Navigation now excludes waiting designs
from its generic tagged segment; design answers remove an existing review tag.
Notebook entry e13063 records that gotcha and the paragraph/document distinction.

Reran `test_reach.py`: four failures remain, all empty reaches rows. Read:
its fixture uses `tempfile.mkdtemp`, and `verbs.record_reach` silently catches
OSError while writing there. That is consistent with the known tempfile ACL
problem; no passing rerun or measured filesystem cause is claimed here.
Full health and the visual/raw-id/wheel acceptance still require follow-up.

After the adapter repair notice e12728, the Desk MCP route was rediscovered
through the runtime tool metadata and used to reread the card and notebook.
The normal screen.py command was retried: it still fails before Chrome starts,
with WinError 5 creating the temporary desk-shell directory. Both reader tests
and git diff --check passed again. The adapter repair does not resolve this
filesystem blocker. No earlier live mutation was repeated.

## Verified

- **Ran:** `test_reader_words.py` prints `reader words: ok`.
- **Ran:** `test_reader.py` against frontier-try at e12671 prints `reader: ok`.
  It applies or upgrades the reader in memory, without saving the world.
  The copy has 3 tagged items and 3 waiting designs. Checks cover opening each,
  answer choices, queue position and neighbours, Skim/Read, Later/Not later,
  send-back and Ask JEFF submission, Looks good, Build it, Not now, staying in
  the reader after answering, one-press opening from the waiting list and board,
  Writing's default Read mode, and a paragraph design with multiple paragraphs
  and lists under each heading.
- **Ran:** `apply.py check --as worker-a6460` finds the live replacement passages
  once each. This is a preflight only; rerun immediately before any live apply.
- **Ran:** health against frontier-try at e12671 reports `64 compile,
  0 unexpected refusals, 1 expected (p-if)`, but exits 1 overall.
  Many tests fail on temporary-directory permissions; textedit cannot acquire
  its lock, door times out, painter checks fail without browser answers, and
  test_reach reports 4 failed checks. The latter failures were not diagnosed
  or established as baseline failures.

## Blocked acceptance

Update from worker-a6549, Shop talk m6683 (e12897), acknowledged here on
20 Oct: its UUID + `os.makedirs` scratch-directory fix passes child writes and
painter copying, but Edge still disconnects on the first readyState websocket
evaluation. Its source and wheel checks are awaiting landing; this reader
checkout has not incorporated them. JEFF applied the tiling/feed lens fix
himself. These changes do not establish reader browser or wheel acceptance.
After a6549 lands, a browser-capable worker should include its
`hud_playtest.py --only scroll --report none` checks, with `--assume a6460`
and the reader world-half files when testing this unlanded reader.
Do not repeat the known browser failure merely because temp allocation passed.

`screen.py frontier-try --as alex --lens home-viewer --size 2560x1440
--scale 1.5 facts home-viewer 1 shot screen-reader-resumed.png` failed before
Chrome started: WinError 5 creating the temporary desk-shell directory.
No shot was produced. No alternate permission path was attempted.

Still required in an environment allowed to run the sandbox browser:

1. Collaboration report before/after at Alex's scale, a waiting design with its
   Build it bar, and skim. Check the bar stays visible, article measure, tables,
   link hover, repeats, comment/event arrows, and the caret-line id fix.
2. Count visible raw ids and press references; a scene contains source ids by
   design and cannot establish this visual result.
3. Run the HUD playtest and full health. No recording exists.
4. Check header attribution and sent-date labels. Authors without by=/author=
   are explicitly unknown, or the sender is labelled separately. Legacy
   documents still lack original authorship/writing dates; owner is not evidence
   of authorship.

## Landing and world application

The existing WIP commit is 3912ed4; later edits remain uncommitted per the worker
protocol. Do not commit sessions/. The preserved try.desk, try2.desk and try.out
are earlier generated scratch files, not the current installation recipe.

After source landing, follow **Required live application and restore** above.
The older `apply.py door` recipe is superseded for this live application by
JEFF's native Desk MCP, one-command-at-a-time instruction. Do not apply before
source landing: the reader requires the new expression functions.

The world draft is reader.lens plus home-style.roles/review.roles; apply.py
patches the viewer, Writing, board, and waiting list. Its UPGRADES are for an
earlier already-applied experiment copy, not the fresh live world.

## Desk record

- Handbook Recipes: a6581, “Preparing proposals and reports for Alex”, contains
  the requested For Alex rule, at most five lines, for everyone tagging items.
- Rough spots: a6583 names the missing world functions and painter behavior
  behind each source file changed by this commission.
- a6109 received defect report c6579: the grey raw id is Markdown's active-line
  source syntax. The fix is in markdown.js/textedit.js, pending landing.
- Binder a243, “Lenses: one scene, two printers”: the names and derive/functions
  rows describe this branch explicitly as pending landing. Remove that qualifier
  after landing; document live reader integration after the world half applies.
- No changes were made to Alex's screen or .env files.
