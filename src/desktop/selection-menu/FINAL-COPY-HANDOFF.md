# Canonical paired release checkpoint — 21 Oct

SOURCE/COPY PASS; NOT READY OR LIVE. This supersedes the earlier appearance-ID
menu refusal and earlier “exactly one command” restriction. House preserved the
implementation in 22d7470. This continuation changes tests/artifacts/docs only.
Main is bf0974894c36c36a3a7f4e4e44d4a35a13e10336; no merge/override attempted.
An eventual house merge and execution acceptance remain required.

Rowan's exact corrected direct-note menu, paired with the native-preserving
consumer already printed in PAIRED-WORLD-EXAMPLE.txt:

```text
              let destination_title = join($title of $d.talk) when talk != ""
              let destination_title = "" otherwise
              let destination_id = join($id of $d.talk) when talk != ""
              let destination_id = "" otherwise
              on menu "Comment" prepare home/tiles/lens:home-tiling/stage/f5664/body/tiling/a6802/body/lens:jeff-chat/chat/a5082/dock/say context=$d.id destination=$(destination_id)
```

RAN `python src/desktop/selection-menu/inspect_paired_copy.py`:
**5 copied mounted guard cases passed** at copied e18947, **18949 events**,
events18949->18949 with no dispatch. Same mounted key in all ordinary branches;
four native ordinary actions preserved byte-for-byte (1/3/3/3 commands);
ambiguous reply/thread withholds the composer. Exact corrected menu plus
consumer accepted in the SAME in-memory actor-bound copy. Fixture setup:
18949->18953 events; assertions18953->18953. Emitted context s8535/rev1 and
destination s8531/rev1 both have integer fences; source is s8535/rev1/text,
UTF16 range[5,9), quote "same", before "same", after "**bold** end".
These are disposable fixture IDs, not production bindings. Unreadable Talk,
stale Talk and stale source refuse. Separate disposable delivery copy accepts
native append to canonical fixture Talk s8531:18953->18954 events. No real
Conversation sends, session writes, browser or private capture-store access.

RAN `node src/desktop/selection-menu/test_composer_quote.cjs`:
**8 composer quote scenarios passed** plus **2 exact compiled paired-menu
scenarios passed**. Actual prepare/composer functions consume the emitted menu,
fence, validated snapshot and mounted consumer; DOM and transport are mocks.
Preparation makes zero sends and preserves words/capture arguments. Changing
copied viewer and To from Rowan to Pike, then same-key repaint, keeps the quote
and captured Talk. One mocked quoted dispatch targets that canonical Talk,
with both original capture IDs. Remove quote restores exact ordinary Send;
stale preflight dispatches nothing and retains words/quote. Conflicting existing
quote/About and filtered quoted branch refuse preparation.

RAN `node src/desktop/selection-menu/test_send_receipts.cjs`:
**2 sender receipt scenarios passed** (actual sender/Viewer, mocked door).
RAN `python src/text-desk/notation/test_selection_snapshot.py`:
**5 tests OK**. `git diff --check` clean. Earlier selected health and Rowan
review-menu copy proofs remain historical, explicitly not fresh browser proof.
Review menus home-board240nodes/waiting-on-me46nodes, tag/design/dual
eligibility, stale refusal, undo/tag preservation remain in the same bounded
acceptance artifact; no deletion.

Copy recipe: run the four commands above in order; inspect PAIRED-COPY.json,
PAIRED-MENU-COPY.json and PAIRED-WORLD-EXAMPLE.txt. Use the official read-only
Session/deepcopy path in the script, actor alex; do not open session pickles
directly. Do not run explicit_acceptance.py here: it includes a browser lane
already stopped before page-ready.

Remaining execution/rollout gaps:

- Browser selection restoration, native fallback, editable Cut undo, Markdown
  mapping and viewport journeys unverified for changed behavior. No screenshots.
- Real capture delivery/detach unproven; capture rows and consumer sends mocked.
- Quote display names source/quote only. It does not show captured Talk or
  explain its precedence over To chips: visible destination clarity is a gap.
- Existing-Talk/direct-note initial scope only. No absent-Talk creation,
  generated/paragraph/thread/Reader/standalone Writing quote consumers or reload
  persistence. No production world rollout; inspect legacy held drafts first.
- Native batches remain non-atomic: append may succeed before cleanup refuses.
  Same-gesture dedup can clear draft without recovering cleanup; fresh gesture
  risks duplicate append. Native 3/5-command suffixes are preserved, not repaired.
- The single browser attempt failed before ready. PID59660 native creation,
  parent/executable and ownership remain UNKNOWN; owners=[]; both cleanup
  receipts refused “ownership incomplete.” Guard0 is not cleanup proof.
  Exact manifest/profile/desktop/launcher evidence remains in EXPLICIT-HANDOFF.md.
  No new process query, cleanup action or retry. Preserve retained profile;
  exclude scratch runtime/profile from eventual source landing.
- Requested model matches actual receipt; actual effort remains blank/UNKNOWN.
  JEFF owns execution-owner transfer; recipient acknowledgment is unestablished.

The implementation stays paused. No ready/landing or browser retry by this worker.
