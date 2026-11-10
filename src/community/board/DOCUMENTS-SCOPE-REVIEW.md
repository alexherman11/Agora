# Documents library scope — source proposal for JEFF

Closeout continuation, 3 November 2026. Supersedes the broad provider permission
option in the earlier handoff; does not change that draft or its published note.
No grant, activation, restart, installer or live input was performed.

## Smallest deliverable

Source draft adds an opt-in `library:<id>` conjunct to the existing `only=`
write-admission grammar. Intended future provider authority, **not issued**:

```
target: existing files module dk288
words: make set
only: kind:document-folder,document-entry;library:<reviewed-library-id>
```

This is limited make/set authority, not unrestricted make/set. Under this clause:

- Creation accepts only a named `document-folder` or `document-entry`, its exact
  library, a parent in that library, and `within=<same-library>`; a document entry
  also needs a visible admitted file. Handles and the matching group are allowed.
- The new row must inherit library visibility. Library and metadata must have
  exactly one matching group. No arbitrary text, policies, visibility overrides,
  library creation, uploaded-file changes or unrelated facts are admitted.
- Editing permits only name and parent on an already inherited metadata row in
  that library. Parent traversal refuses cycles, missing/invisible ancestors,
  other libraries and inconsistent visibility/group membership.
- An unattached indexed file must belong to the caller. A visible attached file
  must have its visible attachment source in the library's group. Indexing never
  attaches or publishes bytes; ordinary upload/attach authority stays separate.
- Person ownership, ordinary may checks, grant issuer checks, fences and atomic
  module admission remain in force. `make kind=post` now checks the grant before
  its compatibility delegation, closing a bypass of a restricted make grant.

Unknown clauses continue to refuse. Existing unscoped grants retain their
behavior; any overlapping broader grant could independently admit a write.
JEFF must review the target's complete active grant set before approving a
limited grant. The live provider currently has only `rows file-result`.
This source does not narrow or replace any existing live grant.

The current `grant` implementation always stores `where=<world-place>`; merely
adding `in=<channel>` to a proposed grant line would **not** create a channel
limit. The new library clause enforces object identity, metadata shape and
matching group at admission instead of relying on that unsupported claim.

## Exact held decisions

1. **JEFF chooses and separately approves a real library identity and group.**
   Read-only world lookup still finds no `document-library` named
   `seabright-documents`; no id is invented here. Intended group is Research &
   documents dk313 (channel dk314). A root needs independent reviewed creation;
   the restricted provider cannot create it.
2. **House reviews source before publication.** Tests were added to
   `test_shapes.py` for positive metadata/ownership, extra creation fields,
   inheritance, cross-library moves, cycles, hidden libraries, the post
   compatibility bypass, file indexing and immutable upload records. They are
   not executed here. The earlier scratch denial remains held; no fixture
   relocation or alternative runner was used.
3. **JEFF resolves provider authority.** Provider target remains dk288; existing
   grant dk289 is `rows file-result`, where=dk1, issuer Alex dk2. Additional
   `make set` must carry the exact conjunct above. Alex/existing grant issuer or
   an explicitly authorized steward resolves issuance. No grant is supplied by
   this task, Alex's general close-Now request, or source review.
4. **Recover and adapt the final Documents source, not an old substitute.**
   Reviewed base `30f97d32b059` plus three coordinator corrections is still held
   under dk1561; those corrections are absent from this checkout. Its make
   answers must add `within=<library>`; existing legacy rows without inheritance
   deliberately refuse scoped edits. No automatic migration is proposed.
   Provider publication must add the five Documents words, not just declare
   `publishes=files.*`. Current provider offers only `files.convert`.
5. **Board authority remains separate.** Target dk368, active grant dk446
   (Alex-issued, where=dk1), lacks `files.browse files.folder files.store
   files.rename files.move` and `hear:attach hear:files.* hear:file-result`.
   The new clause protects provider metadata writes, not arbitrary module reads
   or the outer Board word. It does not enforce a library restriction on
   `files.browse`. JEFF must resolve whether caller-visible browsing plus the
   restricted provider writes is sufficient, or require a separately reviewed
   outer-call/read boundary. No broad `files.*` execution grant is proposed.
6. **Activation is not authorized.** Current calendar/asks nesting, Board
   widget/draft, map grant holds, standalone Documents subscription hold and
   lifecycle holds remain untouched.

## Original held authority evidence recovered

Read through Agora `refusals`, not raw log files or retries:

- Refusal **#386**, 2026-10-29 05:38:58Z: actor/person JEFF dk827,
  `house.stop dk1535` (original Documents worker).
- Refusal **#387**, same time/principal: `house.stop dk1536`
  (original map worker).
- Both reasons: `house: house.stop <person>: the house runs JEFF, Sable, Rowan,
  Pike`. These are wrong-target lifecycle refusals, not evidence granting
  permission to stop builders or restart House.
- Refusal **#420**, 2026-10-29 08:06:54Z: actor dk36/person Alex dk2, malformed
  `house.tell dk1558 ...`; batch text explicitly retained holds on restarting
  House, lifecycle repair, clearing sessions and broadening Rowan authority.
  It also describes the hosted site as a separate sanitized demo without
  native synchronization. This refused command is historical context, not a
  successfully delivered instruction or a new authority receipt.

The 705 retained world refusal entries inspected do not contain an original
`house.restart` or module off/on denial proving the broader lifecycle claim.
Original shell/executor denial receipts remain unavailable in the inspected
records. JEFF must retain that hold; do not replace missing evidence with a
guessed denial or route another executor around it.

Documents' exact subscription hold remains dk1561/r3366, later reviewed in
dk1632: proposed standalone widget lacks `hear:component
hear:component-action`; it has no current live widget id. Board already has
those subscriptions. Map hold remains dk1563/r3332/r3376 and dk1632:
five Board reads `map.layers map.tile map.find map.where map.place`, no grants.

## Read-only child reconciliation

Current Board lens dk366 is still revision 3413, including both calendar and
asks. Channels dk310/dk319 still route `calendar`/`asks`. Readings
`board.events in=dk309` and `board.asks in=dk318` both succeed with zero rows.
These prove readable empty results and unchanged authored routing, not native
paint/input, event creation, RSVP or helping acceptance.

Original child cards dk1499, dk1500, dk1512, dk1501 and dk1530 still have stale
next actions mentioning queued/original workers. Calendar/asks source and
activation are recorded completed in dk1558/dk1560, but owner outcomes remain
unverified. Reconcile those next actions to their existing continuation cards;
do not duplicate workers or mark the end-to-end acceptance Done.
The map fixture correction is preserved in current HEAD `7257c8108`; no edits
to that file or test execution occurred this continuation.

## Validation limits

Ran: pinned Python AST parsing of four changed Python files:
`AST parse: 4 files passed; no tests executed`. `git diff --check` passed.
No security or feature tests ran; the draft is not accepted as working.
Initial `git status --short` again warned about the already-denied scratch
directory; it was not inspected, relocated, removed or used for execution.
No further status enumeration was attempted.
