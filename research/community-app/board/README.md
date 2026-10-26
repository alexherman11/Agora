# Board world and files — builder handoff

Builder draft, 26 October 2026. Claude reviews and commits. No git state changes,
live desktop restart, live world installation, or visible test window.

**Read:** `MESSAGE-BOARD.md`, `Communities and the Dictionary.md`, SHAPE §17,
HOW-TO-BUILD-HERE and repository AGENTS.md. The live charter could not be read:
the door returned acknowledgement unavailable; the read-only local attempt
refused because the world server holds Frontier. No server was restarted and
no pickle was opened. This handoff records that boundary rather than claiming
the charter was read.

The design's world/file layer is implemented here. `definitions.json` contains
the six channels, nine initial kinds and five ordering things. `install.py`
speaks ordinary words through an authenticated door; it does not connect to a
live target by default. `modules()` returns reviewed genesis specs for two
separate Python processes. Use the pinned interpreter for both.

## Kernel additions first

| Missing world capability | General implementation |
|---|---|
| Upload bytes without putting them in lines/logs | `upload`, `POST /upload`, CAS at `<world>/blobs/<sha256>` |
| Attach and read converted content | `attach`, `file-result`, `file-read`, authenticated `/files/<thing>` |
| Permission inheritance | `within=<thing>` on make/post; kernel-owned `visibility_of`; every read follows ancestors, fails closed on cycles/deleted/hidden parents |
| Local dictionary controls | `dictionary-copy` makes a scoped copy of a kernel word; group leaders may `word-set` their local entries |
| Make/rename channels with words | `group [id] name=… open=yes|no in=<parent>` |
| Read time and moderation notices | `clock`, `forgotten` |
| Rich posts and timed actions | post accepts ordinary fields and narrow `sees=`; `pin until=UTC`; `vote` accepts any thing with options and honours `closes` |
| Correct composed admission | inner words resolve in their group; grants use that same scope; `once` counts component uses, including earlier steps in one transaction |
| Human ownership of module-created data | maker permission includes immutable `for`; undo-created empty things disappear from readings |

`make kind=post` remains compatible, including private drafts, but passes through
the scoped post's may/once. `rows` now includes a derived `groups` list. Existing
votes, likes, claims, role appointment, history, fences, sealed authorship and
undo are reused.

These source edits and the world words they were missing are also recorded in
[Rough spots](BOARD-ROUGH-SPOTS.md). No edits were made to painter/ or components/
source. The shared guarded widget host gained `agora.upload(file, group?)`;
the component painter uses that same bridge. The model module can now read an
explicit photo context through `file-read` and send its cleaned thumbnail to
the existing vision-capable local model. It labels the suggestion and writes
nothing automatically.

## Words and world definitions

All published words have dictionary help. Read `help board.post`, etc.
Names below are words; substitute ids returned by readings in actual lines.
All acts return receipts, and undo restores their facts subject to the ordinary
later-edit fence. See words make no records.

| Word | Contract |
|---|---|
| `board.post text=… post_kind=… in=<group>` | Validate a world kind's fields/required fields, then use that channel's post word |
| `board.reply <post> text=…` | Reply, or reply to a reply; refuse level three; inherits parent visibility |
| `board.reply … quote=… source=<post/document> page=2` | Exact passage from currently visible source text; saves source/page attribution |
| `board.answer <question> reply=<reply>` | Asker or leader marks one reply; undo restores needs-answer state |
| `board.decide <thread> text=…` | Leader outcome and decision thing, one act; catch-up includes it |
| `board.rsvp <event> status=going|maybe` | Existing claim plus status marker, one undoable act |
| `claim <ask/offer/slot>` | Existing capacity/once/closing checks; filled slots have zero seats left |
| `like <post>` / `vote <poll> yes` | Existing sealed acts; only counts are read; no downvote word |
| `pin <post> until=<UTC>` | Pin whose reading expires at the kernel deadline; undo restores previous pin state |
| `forget <post> reason=…` | Existing hide plus reason; `forgotten` reads a notice without hidden text; undo restores descendants/files |
| `board.report <post> reason=…` / `board.queue` | Report visible only to the post's group leaders |
| `board.personal <post> action=hide|mute|bookmark|follow` | Private mark shared with your agents; undo removes it |
| `board.seen` / `catch-up` | Private last-seen marker; decisions/events/answers/busy/followed replies since it; plain data |
| `board.feed [order=<ordering>] [in=<group>]` | Caller-visible threads with why_here, seats and immutable times |
| `new`, `top-this-week`, `needs-answers`, `happening-soon` | Copyable see verb notes over feed orderings |
| `board.why-here <post>` | Pin leader, upvote count, reply count, answer/outcome |
| `board.search q=… [in=… kind=… person=… since=… before=…]` | Visible post/reply text and extracted document pages |
| `board.calendar <event>` | UTF-8, escaped/folded RFC 5545 text, filename and MIME for a calendar download |
| `board.badges` | Real names, steward/group leader badges, agents as `agent for <person>` |
| `history <thing>` | Existing filtered record trail, including edits, claims and undo; sealed rows hide authorship |

Announcement channels have post may=leaders and reply may=members. Other
channels allow members. Each channel owns separate `post` and `reply` dictionary
entries: initially four/five posts and thirty replies per person per day.
Person and agent share quotas; undo frees an active use. A leader reads the
scoped entry, then changes `once` or `may` with `word-set`. A new group/channel
can be made with the same words used by the installer.

Post storage stays `kind=post`; its world-defined category is `post_kind`.
That keeps the existing sealed like and painter facts. Question, announcement,
event, poll, ask/offer and document fields are data in `kind` declarations.
Decision outcomes additionally make a linked `kind=decision` thing. Event slots
are ordinary claimable things; multiple slot things may link to an event.

Adding a category requires no source:

```text
make kind=kind name="Lost pet" fields="pet_name last_seen" required=pet_name
board.post in=<Neighbours group> post_kind="Lost pet" pet_name=Pip last_seen="Murray Street" text="Has anyone seen Pip?"
```

Anyone can make a `board-order` thing with `rule=new|top-week|needs-answers|soon|bookmarks`,
then select its returned id, or compose a new see verb. The Alex-owned
`board-settings.default_order` points to an ordering thing and has ordinary
history/undo. The rule vocabulary is implemented by board's module; arbitrary
new ranking algorithms need another module word, not arbitrary evaluated code.

## Files and security

Upload raw bytes to `POST /upload?in=<group>` with the existing authenticated
cookie/bearer and `X-Filename` (percent-encode non-ASCII). The name is display
data only. The request runs the dictionary's upload word with its may and once.
`agora.upload(new File(...), group)` uses the same operation as the widget's
viewer, narrowed to its grants; give its activation `upload files.convert`.
The direct door automatically calls the installed files converter after the
upload. The response includes `made` for the file and a separate `conversion`
receipt; keep both. Conversion is not the upload's same undo record.

- The steward-owned `file-settings.max_bytes` starts at 26,214,400 bytes (25 MiB).
  It caps the request before reading, and is rechecked by the word. The word
  initially permits forty uploads per person per day. No file contents enter
  the record; records hold digest, size, type, provenance and structural facts.
- Type detection examines bytes. A camera JPEG named `camera.txt` becomes a
  photo; HTML named `active.jpg` remains an HTML download. A Markdown extension
  confers no authority: UTF-8 Markdown is treated as text.
- Only upload can create `kind=file` and set its hash, size, MIME and uploader.
  Only the granted, named files process can publish a result. Manifest and
  derivative digests are checked against bytes. Richer objects refer to the
  file through kernel-owned facts. Generic make/set cannot forge those facts.
- Until attachment, only the uploader sees a file. `attach <file> to=<post>`
  requires the uploader, visible parent, ownership/leadership of the parent and
  current fence observations. Undo restores the previous attachment. Later
  parent hiding/restriction also hides originals, derivatives and text reads.
- `/files/<file-or-richer-thing>` authenticates and checks current visibility;
  bare digests and filesystem paths are not routes. Every response has nosniff,
  sandbox CSP and private/no-store caching. HTML, SVG, text, PDFs and unknown
  formats download. Audio/video may play inline. Images always serve cleaned
  PNGs, including when a caller asks for a download; the original photo is
  never available through this route. `?variant=thumbnail` serves the thumbnail.
  An undecodable image retains its private original and a plain-file failure
  reason, but cannot be downloaded through this route until a cleaned copy
  exists; this deliberately preserves the no-raw-photo privacy rule.
- Extracted pages/rows are stored in a JSON manifest blob, not in the log.
  `file-read <thing> [page=N]` checks permission and returns their data. A poster
  quoting a passage intentionally writes that quotation into their reply.
- Undo removes world references, retaining unreachable CAS bytes. There is no
  garbage collector yet. Backups must keep the CAS with the world log.
- Processes are reviewed and run hidden. Grants contain world power, not OS
  file/network access. This is not an OS sandbox for strangers' converters.

| Bytes | Richer thing / conversion |
|---|---|
| JPEG, PNG, WebP, GIF; HEIC/AVIF if installed Pillow can decode | photo: oriented, fresh PNG pixels, no copied metadata; width/height; 360 px thumbnail; editable alt |
| PDF | document: pypdf page count and one extracted string per page; searchable/quotable by 1-based page |
| DOCX | document: bounded zip/XML, paragraph text, one logical page (no Word pagination) |
| UTF-8 TXT/Markdown | document: text, one logical page |
| CSV | table: columns, rows, row_count; strings stay data, not formulas/code |
| One UTC/all-day ICS VEVENT | event: start/end/title/location/description; RSVP and calendar export |
| WAV | media: MIME and measured duration |
| MP3/Ogg/MP4/WebM | media: MIME, duration unknown with these dependencies |
| Other/active/malformed | file: download only; conversion reason returned by file-read |

Extraction bounds: 24 million photo pixels, 300 PDF pages, 8 MiB decoded PDF
page stream, two million text characters, 8 MiB DOCX XML, 20,000 CSV rows/200
columns, 16 MiB result manifest. No archive paths are extracted. Parser errors
become plain files with reasons. These are application bounds, not a hard OS
memory/CPU sandbox for every adversarial compression bomb.

For optional photo alt text, the poster explicitly says
`model.ask "Suggest concise alt text" about=<photo>`. Give the reviewed model
module `file-read`; it reads the cleaned thumbnail under the caller's visibility
and returns `local model · <model> · suggested photo description: …`. The poster
accepts/edits it with `set <photo> alt=… alt_source=…`. No vision model is called
by upload. Thumbnail transport and labelling have a contract test; real vision
caption quality was not evaluated.

Dependencies are pinned in root `pyproject.toml`: pypdf 6.21.2 and Pillow 12.3.0.
The environment had no pip module; installation used
`uv pip install --python C:/Projects/Agora4/.venv/Scripts/python.exe pypdf Pillow`.
No PDF renderer was installed or downloaded.

## Evidence and departures

**Ran, final:** `94 passed, 46 subtests passed in 116.75s (0:01:56)` for all
kernel-lab tests, model contracts and the seven board boundary tests together.
The separate summarize proof ran seven tests successfully. Existing Council,
Hidden Hunt, kits, BYO agent, web host, real local-model, taskboard, widgets,
pixel-guy and painter proofs passed. Taskboard's retained proof.py delegates
to proof_v2.run: its full ten-minute triage printed `34 of 34 checks passed`,
with `wall_seconds=619.27`. Painter source was not edited to run its proofs;
outputs were redirected by the regression launcher. Exact results and transient
cold-load/guide-sync failures are recorded in [verification](BOARD-VERIFICATION.md).

```text
BOARD: 62/62 checks passed; 32 people; 409 posts (82 replies); 14 simulated days.
```

Reading medians across thirty readers, at 409 posts: feed 22.47 ms, catch-up
19.74 ms, search 36.97 ms. These are loopback HTTP/module timings, not a public
deployment load test. The actual labelled qwen3.5:9b catch-up summary succeeded
on the first model attempt in this final run.

Run the scenario with the pinned Python:

```text
C:/Projects/Agora4/.venv/Scripts/python.exe -B research/community-app/board/proof.py --model
C:/Projects/Agora4/.venv/Scripts/python.exe -B -m pytest research/community-app/board/test_contracts.py -q
```

`evidence.json` records the scenario's exact printed counts, timings and real
model answer. People/messages are imagined fixtures; checks and HTTP timings
are ran. The camera photograph has its original real latitude/longitude tags;
the proof checks both were present, then verifies zero EXIF in served image and
thumbnail. See [fixture provenance](fixtures/BOARD-FIXTURES.md).

Departures/limits from MESSAGE-BOARD.md:

- PDF first-page preview is not done: pypdf extracts, no renderer is installed.
  The converter uses PyMuPDF if already available, without downloading it.
- Animated photos become the first oriented frame; HEIC decoding depends on
  installed support. UTF-8 text is supported; other encodings download.
- RSVP maybe currently reserves a seat, just like going; undo releases it.
- Imported calendars support one UTC/all-day event; TZID, recurrence and
  multi-event calendars remain plain files with an explanation.
- Timed pin expiry is a reading of its recorded deadline; it does not make an
  autonomous unpin record. Poll closing is checked at vote admission.
- Kinds and the fixed ordering vocabulary are world data; board's richer
  validation/readings are a module because thin verb notes lack collection
  processing. The generic word layer intentionally remains available; it is
  not a separate locked-down application API.
- This job builds no phone UI, map painter, weekly email digest, transcript
  player or live deployment. Calendar export is data for a download button.
  Interface contracts and remaining work are in [NEEDS.md](NEEDS.md).

Primary implementation references: [pypdf extraction](https://pypdf.readthedocs.io/en/stable/user/extract-text.html),
[Pillow EXIF orientation](https://pillow.readthedocs.io/en/stable/reference/ImageOps.html#PIL.ImageOps.exif_transpose).
