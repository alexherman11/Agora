# Conversation prototype

The lens and style in this directory are authored native application content.
The current contract also lives in Frontier Handbook note `a243` and
`docs/Current Implementation.md`.

## Implemented

- A feed of the person's outgoing and explicitly addressed incoming sayings,
  including comments and replies, with original-place reply targets.
- Explicit recipients, multiline drafting, recovery after reload, and visible
  refusal reasons.
- Private captured-context previews. Send copies captured text, native identity
  and optional PNG into the durable message and detaches only the sent IDs.
- Addressed resident delivery of captured content, with the current object
  revision reported separately. Replay does not need the private capture files.

## Evidence

Copied-world browser checks covered 320, 420 and 600 px layouts, draft recovery,
unknown-recipient refusal, a 1,298-character multiline message to two recipients,
original-place replies, and captured wording retained after its source changed.
The focused conversation/compiler suite passed 104 tests; repository tests
passed 201 with 2 skipped. Copied-world health passed with 20 active lenses and
no unexpected refusal. The documentation checker still reports the pre-existing
missing Dynamic Desk image.

On 15 October 2026, a browser Send from Codex's own draft produced `m5410`.
JEFF's real reply, `m5411` / `e10449`, identified captured task revision 3 versus
current revision 5, described the received 600 by 380 PNG, and recognized the
OS-native `a604` capture as a selected title rather than its document body.
The task capture was a controlled API fixture; the PNG and title capture came
from the capture worker's controlled OS checks. This verifies resident delivery,
not the full human desktop-drag journey or every detail of image interpretation.

Alex then clarified that `a5080` is his conversation with JEFF. Keep tests and
agent coordination in Shop talk or a separate demo feed. Do not use Alex's draft
or identity for tests.

## Limits

The prototype shows the latest 80 exchanges. Older-history browsing, recipient
completion and deletion of removed/sent private capture files are not implemented.
The activity indicator currently matches a single recipient exactly; multiple
recipients can receive messages but do not show a combined working indicator.
Desktop gesture and window-management integration have separate owners.

## Visual reports

Alex's 15 October request is tracked separately as `a5431`: first demonstrate a
native lens inside a message in a separate demo. The Codex visualize tool's HTML
fragment contract is not an installed Agora capability. General HTML support
needs a separate isolated renderer and frozen message attachments; it must not
inherit the HUD's desktop bridge. JEFF asked to show the native proof before
building that renderer.

The separate native demo is `visual-chat-proof-demo` (`a5456`) in Frontier,
with its own feed `a5450`, report `a5454` and style `a5452`. It does not modify
the Alex/JEFF feed or either existing chat lens. Authored sources are
`visual-demo.lens`, `visual-report.lens` and `visual-report.style`; replace
`DEMO_FEED_ID` with the demo feed ID when publishing. The message carries
`visual=visual-chat-proof-report`, rendered with a guarded `lens $visual` child.
The report combines a sanitized native SVG with three local disclosure controls.

Six copy-only compiler checks cover absent/valid visual fields, the SVG scene,
composer identity/action continuity, subsequent append, and a missing visual.
Browser checks at 320, 420 and 600 px found no document overflow, exercised
mouse and keyboard disclosure, preserved an unsent draft through expansion and
resize, and sent that draft in the copied demo feed. No live resident was used
for this visual proof.

This is a capability demonstration, not general HTML support. Its report follows
a mutable lens name. A missing child lens can refuse the enclosing feed, so do
not add this dynamic placement to the shared conversation until individual
visual failures are contained. Disclosure controls are local; future authored
native actions can change shared state and must be treated accordingly.
