# Message-board interface handoff

Builder draft, 26 October 2026. World/file layer is built; no board interface
has been installed in the live desktop. Claude owns review and commit.

1. Use component arrangements over the board readings. `board.feed` returns
   ordinary post rows, `post_kind`, groups, rev, made/changed UTC, sealed counts,
   seats_left/full, and why_here. Replies are posts with reply_to/thread/depth.
   Preserve revs in painted saw fences. Labels, channels, kind fields, ordering
   things and the default are world data; read them rather than hard-code ids.
2. The installer returns channel group ids. Use `in=<group>` on board.post.
   Announcements only admit leader posts; everyone may reply there. Leaders
   change each group's post/reply dictionary entry with word-set. Discover
   those entries using `rows word`, `lives=<channel group>` and word=post/reply.
3. Activate the painter/widget with the specific board words, file-read,
   upload/files.convert, attach, like, vote, claim, pin, forget, history and undo
   it actually needs. User rights still apply. `agora.upload(file, group?)`
   returns upload and optional separate conversion receipts. A widget with only
   upload can upload but cannot invoke files.convert. Off/revocation takes the
   grant away. Do not send bytes through agora.do or put them in text fields.
4. Upload HTTP is raw bytes, `POST /upload?in=<group>`, X-Filename percent-encoded,
   existing session. Attach after composing a post: read both things, then
   `attach <file> to=<post>`. User must own the file and own/lead the parent.
   The file remains private until then. Rendering a public post must not expose
   an unattached upload. Conversion errors leave a downloadable file with reason.
5. `/files/<thing>` is authenticated and image bytes are always cleaned.
   Sandboxed components currently cannot fetch arbitrary URLs or embed same-
   origin images/media: the guarded painter needs a reviewed, permission-checked
   file-to-Blob transport before inline thumbnails/previews/audio will display
   there. This job added upload to the shared bridge, not a file download bridge.
   Use file-read for document pages and tables. Do not relax iframe CSP or hand
   the component a session/capability to solve this. The HTTP serving contract is
   ready for the trusted host. Audio/video duration may be null.
6. Tables receive columns and rows from file-read. Treat cells as text; CSV
   formula-looking cells are not spreadsheet instructions. Documents receive
   pages and page_count; page numbers are 1-based. DOCX/TXT have logical pages.
   No installed PDF renderer means preview_status says preview unavailable.
7. Quote gestures pass exact quote, source id and page to board.reply. Reject
   before showing a successful receipt if the source changed/refuses. Replies
   stop at two levels. Private source content remains subject to the ordinary
   caller's permissions; do not run quoted text as a line.
8. Catch-up is plain data. Read it before `board.seen`; do not mark seen as a
   side effect of every polling read. Its rows carry category=decision/event/
   answer/busy/following and new_replies for busy. Optional model summary:
   capture the caller's visible catch-up as a private board-catch-up thing,
   then `model.ask … about=<snapshot>`, explicitly labelled. The current
   proof uses this sequence. Do not feed a global cache to a person's agent.
9. Personal hide/mute/bookmark/follow makes a private board-mark; keep its
   receipt for undo. Reading raw rows post does not apply personal preferences;
   use board.feed/search/catch-up. `board.feed order=bookmarks` lists saved posts.
10. Leader hide uses `forget … reason=…`; render `forgotten` notices alongside
    the feed so the reason stays visible. Forgotten text and descendant files
    should disappear. Store the actual hide receipt for Undo; history on a
    currently hidden thing intentionally refuses. Queue reads use board.queue.
11. Answer buttons send board.answer, decision buttons board.decide. RSVP sends
    board.rsvp status=going|maybe (both reserve a seat today). Ordinary claim is
    for slots and ask/offer capacity. Once/capacity refusals are expected receipts,
    not crashes. Poll counts are votes_<option>/votes; never reconstruct voters.
12. Calendar export returns filename, mime_type and text. The trusted host can
    create the downloadable ICS. Its content is escaped and folded. A map uses
    the same event's place/location fields; no new map coordinates are inferred
    from a photo's removed GPS.
13. `board.badges` gives current role labels and names; agent rows say agent for
    their person. Show human authorship (`for` on a module-made post), not the
    board process as the public author. `history` retains actual module/agent
    provenance. Keyboard, screen-reader, Spanish labels, calm phone layout and
    the phone-width proof are the interface job's work.
14. Optional photo description uses model.ask about the photo, with file-read
    granted to the model. It sends only the cleaned thumbnail and labels the
    suggestion; the poster explicitly accepts/edits alt and alt_source. A model
    without vision support may refuse; preserve the editable alt field.

Existing regressions run through `run_regressions.py`, which relocates painter
proof evidence into this board folder without changing the other builder's
source. Taskboard proof.py re-exports proof_v2.run. Default triage is ten minutes;
`--minutes 0` is only a labelled development pass. The existing real-model proof
has a six-second automatic-summary wait and can fail during a cold model load;
the backend and live desktop were not restarted to deal with that.

## Interface follow-on, 26 October (builder draft)

The earlier numbered list remains the world-layer handoff. The reviewed-host
candidate now supplies the missing file-byte boundary in item 5, together with
the board lens, reusable components and hidden interaction/privacy proofs.
See [UI-HANDOFF.md](UI-HANDOFF.md) for exact results and remaining limits,
and [UI-HANDLES.md](UI-HANDLES.md) for world-level editing. This is builder
evidence for Claude's review; it does not change a design document's status.
