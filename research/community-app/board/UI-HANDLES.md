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
