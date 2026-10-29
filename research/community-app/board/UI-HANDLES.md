# Seabright interface handles

Builder draft for Claude's review. `components for="community board"` and
`help poll`, `help slots`, `help file`, `help field-list` describe reusable pieces.
`look-view seabright-board plan=yes` describes the authored arrangement, reading
sources, declared settings, styles and last painter observations. Unobserved
reading-backed rows are not proof of paint. Each running host reads collections
through its own viewer principal, without holding the kernel lock across modules.

Channels are `board-channel`/group things. Kinds are `kind` things with `fields`
and `required`. No component changes are needed for `Lost pet` or another kind.
The `fields` setting on `field-list` selects displayed fields and their order;
empty means the kind's `card_fields` declaration (falling back to `fields` for
new kinds); `-` hides generic fields. Reorder slots in the lens to reorder
body, fields, polls, slots and files. `limit`/`offset` on any collection page its
construction. `of reading:"board.feed order=$view.order in=$view.channel" as p`
uses the world's feed ordering without reimplementing ranking in the browser.
`board-settings.default_order` points to a `board-order` thing.
`personal-view seabright-board view.order=<ordering>` chooses a private opening
ordering; `view.channel=<channel group>` chooses an opening channel. These are
general initial view-state defaults, overridden by that window's local choices.
Kinds may declare JSON `field_labels` and `field_types`; the composer uses text,
number and local date/time controls and submits dates as UTC. Neighbour-made
fields fall back to readable names and text inputs. `card_fields` independently
controls card presentation.

Every piece supports the general UI labels handle. Use
`labels ui {"compose":"Escribir","Reply":"Responder"}` beneath a piece.
A personal version is
`personal-view seabright-board tools.labels.ui=<JSON map>`; change every piece
whose labels you want translated. Domain kind/ordering values stay unchanged.
Shared label maps can be supplied in the arrangement's `setting labels=...`.
Labels cover controls, kind/field names, channel names and badges; user text
stays user text. Real names come from `board.badges`; agents retain that reading's
`agent for <person>` identity.

`personal-view seabright-board post.layout=compact detail.layout=compact`
changes card density for one person. Shared versions are lens settings.
`personal-style seabright-board target=board-post padding="8px 12px"` affects
one person's cards. Badge styles target `board-post.badge[role=agent]`,
`board-post.badge[role=leader]`, or `board-post.identity`; kind declarations may
set `accent=<theme token name>`, and kind accents also accept a style targeting
`board-post[post_kind=question]`. The post's
`data-fact-post_kind` selector is exposed as `board-post[post_kind=question]`.
The general `slots` component's `label` setting overrides its heading; an event
slot otherwise uses its declared title. Its `label`, `count` and `claim` parts
are independently styleable. The general `file` component accepts a structured
`content` JSON binding from `file-read`, a display `name` and `variant` of
`content` or `thumbnail`; its `table` slot may contain the catalogue table.
All board measures, colours, radii and type sizes live in the lens's
`part-style target=tokens` thing. For example `nb-body`, `nb-space-4`, `nb-radius`,
`accent`, `nb-soft`. Personal token styles apply after shared ones.

The lens declares `when fact likes changes play pulse` and the poll's votes
equivalent. `motion-pulse` is a bounded world token; reduced motion suppresses it.

File bytes travel only through the reviewed host: grant-checked `file-read`,
then an authenticated same-origin `/files/<thing>` GET. Components receive Blob
bytes and create disposable object URLs. They receive no session, route, token
or network capability. `connect-src 'none'` stays fixed; image sources retain
`data: blob:`, and media sources allow exactly `blob:`. Every new request checks
current permissions. Projection changes remove and revoke obsolete URLs;
bytes already viewed cannot be made unseen.

Downloads use `api.download(thing)` or `api.downloadReading("board.calendar …")`.
The trusted parent checks the viewer's grants/readings, fetches file bytes with
its own session, and creates the actual download. The child receives no route
or download authority; its sandbox still has no allow-downloads or allow-forms.
`P.submit` keeps form validation and keyboard actions local to the guarded word
bridge. The optional summary captures only that viewer's catch-up, privately,
before asking the local model; it is never called by opening or polling a board.
Native WebView2 downloads require a one-use registration from the exact trusted
top page for that parent's Blob URL. The native save chooser runs only after
the user's download action. Global browser downloads remain disabled, and
opaque components cannot register a download.

Off switch: close the board window or `off seabright-board`. Installing creates
a dock entry but opens no window. The live installer adds no fixture people or
posts. Poll counts are sealed; explicit Mark seen is the only catch-up write.

## Polish handles, 26 October (builder draft)

The slim bar uses `root.title` and labels `searchhint`, `compose`. The reading
pane exists only when `view.thread` is selected. Theme `nb-thread-width`
(520px), `nb-thread-share` (45%), `nb-nav-width`, `nb-top-height` and
`nb-phone-compose-room` control the layout. The built-in responsive transition
is 1100px; phone layout is 650px. Those breakpoints are component CSS, not
claimed world handles. No board window is opened by an install.
`root.extras=feed` places additional root parts (including their stopped cards)
at the top of the feed's existing scroll column, preserving navigation/feed/
thread widths. `extras=alongside` retains literal sibling grid placement.

`post.layout=compact`, `post.excerptLines=3` control feed density and excerpts.
`post.format.stamp=short-relative`, `post.format.date=calendar-date`, and
`post.format.initials=initials` apply to post metadata; use `detail` for the
reading pane and `result` for search dates. `date` is the general date-tile slot
with its own formats and `soonDays`. `poll.format.stamp` controls closing dates;
`fields.format.stamp` and `attachment-content.format.stamp` control other dates.
UI labels still use the general `labels ui` / personal labels handle.

`catchup.previewCount=3` controls grouped preview rows; the heading expands the
full group, and phones start collapsed. One icon per category is shown on a
thread's row. The Summarise action is present only when `model.status` reports
the selected model installed on an available service. No status error is shown
to neighbours. If inference itself returns an unavailable/offline response,
the action hides for that window session too. The optional generated paragraph
has its own block heading.

Kinds supply `compose_label`, `compose_description`, `compose_icon`,
`field_labels`, `field_types`, `fields` and `required`. New kinds are discovered
automatically. `compose.advancedFields="closes place"` moves those fields into
More options. Field types `datetime` use the small local parser described in
ARRANGEMENT.md plus a native date/time picker and visible confirmation. Only
the selected kind's fields are sent. Removing a pending attachment removes it
from the draft; it does not delete its private upload from the world.

Search filters apply on change. Time choices are Any time, Past week, Past month,
Choose dates; the last opens a labelled picker. Cards highlight literal matches
as text, never HTML. Page hits carry their owning thread and initial file/page.
`attachment-content.page` / `pageTarget` are general initial-page handles;
`pageRequest` is a request counter for re-addressing an already-open reader.

Semantic tokens `nb-amber-ink`, `nb-amber-soft`, `nb-announcement`, kind `accent`
tokens and `accent`/`muted` control contrast and state colours. Full slots omit
the action, rather than fading low-contrast disabled text. `nb-reading-width`,
`nb-reading-size`, `nb-page-leading` control document comfort; `nb-photo-height`
and `nb-phone-photo-height` bound thumbnails, never the full-size original.

Reach boundary: English smart-date grammar is deliberately small, PDF graphics
still require a renderer, and no calendar, map or notifications were added.
## Final review details

Poll totals use `labels voteCount` for the singular and `labels votes` for the
plural. Selection quoting consumes the selection only on explicit activation.
The thread lens projects its matching `forgotten` row through the same notice
template as the feed, keeping the human reason and Undo available on phones.
The compact channel picker includes a separate Your board group for Saved and
the leader-only queue/count. Returning to a channel leaves the bookmark filter;
other chosen orderings are preserved. These labels use the same label handles.


## A channel's own view (calendar first)

*Claude, 28 Oct 2026.* A `board-channel` may say `opens=<view name>` (and `opens_label=<button name>`).
Choosing that channel opens the view instead of the feed; the toolbar shows `<label> | Conversations`.
The lens arranges one part per view name, guarded by `only when $view.opens = <name>`; the feed is
`only when $view.opens = ""`. Meetings & events has `opens=calendar`:

```text
calendar : calendar, of reading:"board.events in=$view.channel around=$view.calendarDate" as e, limit 100, each calendar-event, openKey "thread replyTo"
  only when $view.opens = calendar and $view.search = "" and $view.queue != yes
  on add do board.post post_kind=event in=$view.channel $fields
  on rsvp do board.rsvp $target status=$value
```

To give Asks & offers its own view: `set <its board-channel> opens=asks opens_label="Asks & offers"`, add a
part with `only when $view.opens = asks` to the lens, and nothing else changes. `calendar` is a gallery
component (`help calendar`): its children's facts are the events (`start end title location text going maybe
coming maybe_coming your_rsvp`); without an `add` or `rsvp` gesture it offers neither. `board.events` reads
dated threads within `weeks` (default 6) of `around`, with who is coming by name. The event kind's
`defaults='{"seats":"500"}'` fills seats for a quick add; set a different number on the kind thing.

The `opens` value is just a name: the channel says which view it opens, the lens holds the parts. Lenses
built elsewhere (asks & offers, documents, map) drop in as one guarded part each; a channel without `opens`
stays a feed. Every part keeps its name, so `personal-view <board widget> calendar.view=week` and
`personal-style <board widget> target=calendar background=...` work just for the person who sets them.
(Line keys are lowercase, so camelCase settings such as `weekStart` can't be set this way yet.)

## 'New since' (card dk1512)

*Claude, 29 Oct 2026.* The catch-up header shows only inside a channel (`only when $view.channel != ""`), and
only when that channel has something new for you; otherwise the part is hidden. Its heading
("2 new since Thursday") jumps to the oldest unseen thing: it opens that thread with `$view.focus` set to the
post (for a busy thread, its oldest unseen reply), which the thread pane outlines and scrolls to once.
*Mark all seen* in a channel writes that channel's marker (`board.seen in=<group>`), leaving other channels'
news alone. Your own posts are never news to you; channel unread counts use the same markers.
