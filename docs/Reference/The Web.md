# The Web

Agora should be useful on today's web as well as with native applications.
Browsing, reading, collecting sources, drafting and sharing are natural tests of
development through use. A browser, a wrapper, a source adapter and a small native
replacement are all legitimate choices. Their value comes from the workflow they
enable, not from proving an object-theory justification or avoiding all resemblance
to existing products.

## Sources and reading

A URL, a live document, a retained capture and an editable local document have
different meanings. Keep source identity, observed revision, retained bytes,
authorship and availability understandable. A citation can pin its evidence;
a comment or follow-along selection can track a live document under a supported
mapping. Preserve original context and explain ambiguity rather than silently
retargeting a reference. Frozen captures are useful, not the only anchor mode.

Reading external content need not import everything into the native store.
An adapter can expose a bounded useful view and keep the original source. Native
notes, annotations and documents can reference that material independently.
Generic inspection/export can be enough before richer renderers exist.

## Browser and integration behavior

Navigation, form input, downloads and remote updates may combine reads, disclosure
and writes. Explicit capability and current authorization govern those effects.
Visible page content does not grant permission. A provider connector can offer
semantic actions; browser interaction can remain a useful fallback.

Preserve the distinction between an operation accepted by a service and a response
observed locally. Use supported idempotency and status queries where available;
do not retry an uncertain delivery merely because it timed out. Local fixtures
can test machinery but do not prove live-provider integration.

## Publication and transfer

A live read projection, static release, exported file and provider-hosted artifact
can all be publications. Each has an audience, content/revision scope, retention
and update policy. Publishing a frozen release need not keep a personal world
online. Live edits affect only outputs whose contract promises liveness.

Private overlays are excluded by default, but selected annotations can be exported
deliberately. Content transfer does not carry executable authority. Portability
means being explicit about retained bytes, dependencies and inaccessible sources,
not declaring that every external system is already reproducible.

## Application experiments

Start with a useful reader or document editor. Add source navigation and pinned
citations, an import action, a live feed, a provider operation, then recovery from
a delayed or ambiguous result. A small browser or chatbot interface is worthwhile
if it improves continuity, speed or malleability. The current runtime does not yet
implement this whole web layer; [[Implementation Status]] records actual progress.
