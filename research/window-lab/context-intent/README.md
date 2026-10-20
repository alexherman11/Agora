# Intentional chat context — staged world change

Read: live `jeff-chat` computes `about` from `home-view.viewing` at send
time. Its “Not about” toggle lasts only until navigation. An empty draft
therefore does not prevent unrelated document metadata. The ordinary HUD
reply path also leaves `reply_to` set after sending.

The fix belongs in lenses. No painter, host, route implementation, draft
storage, agent prompt or source activation changes are required.

## Behavior

- Opening a document only offers **Attach open item**, beside its linked name.
  Pressing that button is the intentional gesture; ordinary link navigation
  and Ctrl-click behavior elsewhere are unchanged.
- An explicit attachment stores `draft.topic`, separate from capture
  `draft.context`. The composer shows **About [name] · next message only ×**.
  Navigation cannot retarget it. Remove clears it. HUD and native Conversation
  show the same pending topic.
- A successful send consumes topic and reply intent. A refused append leaves
  intent available for retry. The extra cleanup runs only when intent exists:
  an all-empty `do prop` would itself refuse after an otherwise successful send.
- Answer chooses the original message/thread and discards a pending topic.
  Replies inherit genuine document discussion through the existing sayings
  source; no document is inferred from whatever is open.
- Selected-text comments keep the actual writer selection, quote, paragraph
  and document Talk, including first-comment creation. A successful comment
  consumes pending topic/reply intent too. Canceling a selection does not send
  anything.
- Native main-composer sends honor a reply started in the HUD and show its
  removable reply state. Its existing inline reply controls are untouched.
- Ordinary later messages are plain. JEFF can understand continued discussion
  from the conversation itself without fabricated `about` fields.

An attachment persists visibly until send or removal; it has no silent timer
and does not turn into an invisible topic for future messages.

## Applying and reversing

The live notes **Staged intentional context: jeff-chat** and
**Staged intentional context: conversation** hold literal Old/New hunks.
They have no lens tags and do not activate behavior.

JEFF should first read and save both exact live lens texts, then check every
Old passage occurs once. Reconcile a changed passage individually. Apply the
native composer and HUD changes as one coordinated world update, leaving
styles, message bodies, drafts and Markdown/media work intact. Compile both
scenes before accepting. No restart or live-source activation was performed;
coordinate any such work through the home-base lifecycle commission.

The `before-*.lens` files are reviewed fixture baselines, not replacements for
today's live lenses. `patches.py` prints machine-readable scoped JSON and
`apply(name, current_text)` rejects absent/ambiguous Old passages. A subsequent
worker can write its returned candidate strings to `.lens` files for
`hud_playtest.py --apply` on a copy. Do not use a full candidate to overwrite a
newer live lens. Reverse individual hunks against fresh live text or use the
saved texts only if nobody has changed those lenses since.

After applying, update the Handbook's earlier description of automatic
open-document context. It remains accurate for the current unapplied world;
this branch deliberately does not claim the staged behavior is live.

## Evidence

Ran on 20 Oct:

```
C:/Projects/Agora4/.venv/Scripts/python.exe research/window-lab/context-intent/test_intent.py
```

Printed eight `ok:` groups and:
`all ok: in-memory compiled gestures only; browser/input delivery not verified`.
The fixture installs the actual patched lens text in a fresh in-memory world,
compiles both composers, executes their emitted gestures through Desk dispatch,
and inspects stored line fields and draft props. It uses tester and fake
documents/chats; no shared Conversation messages, Alex sends or raw session
reads. Checks cover navigation/repaint, plain send, explicit attach across
navigation, removal, refusal/retry, cross-composer state, actual document
reply inheritance, existing/new Talk selected comments, and plain followups.

```
C:/Projects/Agora4/.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider research/text-desk-lab/notation/test_universal_chat.py research/text-desk-lab/notation/test_default_audience.py research/text-desk-lab/notation/test_context.py
```

Printed `23 passed in 0.66s`.

Updated the existing browser `about` playtest to require intentional attach,
assert no chip merely from navigation, and check chip consumption after send.
**Not run here: needs a browser-capable run.** No shots, guarded input, visual
layout, actual browser draft-buffer persistence, live sends, reload or restart
are claimed. The in-memory test checks stored draft words, not a browser's
unsent textarea buffer. Earlier commissions documented Chrome IPC/DevTools
failure in this sandbox; this commission did not retry that environment.
