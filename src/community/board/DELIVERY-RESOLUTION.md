# Seabright delivery resolution

Builder proposal for JEFF, 2 November 2026. No activation or authority changes.

## Narrow permission plan (read evidence)

| Boundary | Exact missing permission or decision | Resolver | Covered by this task? |
| --- | --- | --- | --- |
| Documents widget startup | `hear:component`, `hear:component-action` on the proposed Documents widget; readiness awaits these subscriptions before rendering | JEFF must explicitly resolve the held authority decision, with the widget owner/steward applying any approved scoped change | No. The feature request covers implementation; this task expressly forbids adding grants. Existing Board already has these subscriptions, but that does not authorize a new standalone widget or the additional files operations. |
| Map inside Board | `map.layers map.tile map.find map.where map.place` reads on existing Board widget | JEFF resolves; widget owner/steward reviews the exact scope | No. Existing Board grant lacks all five. A working standalone map does not lend authority to its parent. Do not add a wildcard or editing rights. |
| Documents inside Board | `files.browse files.folder files.store files.rename files.move` and `hear:attach hear:files.* hear:file-result` beyond Board's existing `files.convert` and other grants | JEFF and Board widget owner/steward | No. This is additional authority even though Board already has the two component subscriptions. The reviewed Documents installer asks for `files.*`; review these exact operations instead of accepting that broader request automatically. |
| Lifecycle | Prior JEFF restart/lifecycle denials remain held; the exact denied operation must be identified from its original receipt before any future action | JEFF and the authority that refused the original operation | No. Neither source landing nor this assignment permits a retry, provider change, or restart. |
| Source publication | Documents reviewed base plus three recorded corrections needs independent source review and House publication | JEFF/House, under existing documents card | Review is in scope; this worker must not commit, merge, push, land, or start a worker. |
| Native acceptance | Calendar/asks pointer, keyboard and paint evidence; documents upload/drop/preview/nesting; map embedded navigation | JEFF/resident coordinates owner observation through a supported approved path | No live input or visible tests here. This is an evidence gap, not a request to broaden grants. |
| Public website | No authorization to copy private desktop content, sessions or world state into the separate site/demo | JEFF scopes parity work; Alex owns any new publication/design decision | Only source inspection and synthetic fixtures are covered. No deployment or private-data transfer. |

Read: task cards dk1558, dk1560, dk1561, dk1563 and histories of documents/map.
Documents' latest coordinator evidence reports **1 failed, 5 passed in 18.18s**:
published-word regression and four direct tests passed; narrowed readiness
execution-confirmed the two missing subscriptions. This is historical evidence,
not a run performed by this worker. Original files are named
`documents-published-admission-20261029.json/.txt` in coordinator staging.
The original worker chat ends before that coordinator run and still calls the
subscription diagnosis unconfirmed; the later card update supersedes that claim.

## Activation constraints already established

Read: calendar source `a48bf17485a8`, asks `b7a16d3cb428`, map `85cc060788a3`
are recorded landed. Documents base `30f97d32b059` plus corrections is held.
Current checkout has no Documents implementation. Its reviewed base is readable
from the local git object database; the three later corrections are not present
in this checkout and were not independently reviewed here. Do not recreate them.

Read: live Board lens dk366 revision 3413 contains both the calendar subtree and
the conditional `asks : lens, name seabright-asks` subtree. Meetings & events
dk310 routes with `opens=calendar`; Asks & offers dk319 with `opens=asks`.
Research & documents dk314 has no opening route yet. Board widget dk368 is on;
its existing grant includes the two component subscriptions and `board.*`, but
none of the five map reads.

Calendar/asks are already enabled. Their cards record retained-widget hidden
fixtures (7/7 and 5/5 respectively), preserving iframe and unsent draft; neither
proves native pointer/paint acceptance. Do not replay their activation.

Proposed changes after JEFF resolves the held boundaries:

1. Review the original Documents corrections and full feature checks in their
   existing card before publication. The base's `documents.lens` calls
   `files.browse`, `files.folder`, `files.store`, `files.rename`, `files.move`,
   plus existing upload/attach/preview words. Check that list against the final
   corrections. Its files module needs the corresponding published entries;
   module implementation power and widget user power are separate reviews.
2. Preserve the existing Board widget, grant, iframe and view state. Add only
   a conditional nested `seabright-documents` lens plus `opens=documents` and
   `opens_label="Documents"` on Research & documents once the reviewed source
   and required authority are available. The base's documented alternative is
   a `documents : column, of tag:document-library,
   prop:name=seabright-documents as library, each documents-view` subtree plus
   unchanged `documents_install.templates()` declarations; do not add that one
   line without the templates. Prefer the existing nested-lens mechanism only
   after a scratch check proves shared channel, view state and styles work.
   Do not create a standalone widget as a shortcut.
3. For map, review the five reads above, then add only the documented map-panel
   subtree and watch under Board's root. Preserve calendar, asks, styles,
   preferences and unrelated layers. Keep `place` for map links and `location`
   for human calendar meeting text.
4. Review component bytes separately from world activation; any runtime refresh
   must have its own supported authority. Do not restart House or other modules.
5. Track source reviewed/landed, world activation, and owner verification as
   three distinct results on the existing cards. Report held decisions promptly;
   never mark an outcome verified just because source landed.

Do not run full `ui_install.py`: it upserts Board lens text and initial view
state, and can review component code and reactivate grants. It would replace
the world-authored asks nesting. Likewise do not replay map/asks installers.

## Verification and parity follow-through

The map's historical integration failure is a fixture creating a sixth post
against a five-post quota. This worktree changes only the no-place control's
author to the existing second member. The production quota and all visible-place,
hidden-place, no-place and coordinate-update assertions remain intact.

Ran here: the first windowless map-panel suite attempt printed **3 passed,
1 error in 0.58s**, failing fixture setup because `.scratch` did not exist
(`WinError 3`). After creating that parent, the next attempt printed `.E..`
and failed with **PermissionError: [WinError 5] Access is denied** enumerating
`.scratch/map-panel`; pytest aborted before its final summary. Testing stopped
at that denial, without alternate paths, fixture mechanisms or retries.
The corrected integration body remains unexecuted here. House must independently
verify it through its supported review path; no feature acceptance is claimed.

Parity review must compare view structure and styling with synthetic content.
The separate `site` source implements public entry/sign-in/onboarding; the
native Board uses a world lens, reviewed components and world style tokens.
They are distinct surfaces, not proof that either has the other's features.
Current deployment pixels, native rendering and exact external-demo identity
remain unverified here. No private world content should enter public evidence.

Read source comparison, not a screenshot/pixel claim:

| Surface | Native Board source | Separate entry site source | Smallest proposed action |
| --- | --- | --- | --- |
| Layout | Full-height channels/feed/optional thread; 1500px maximum; 650px phone and 1100px intermediate layout | 1040px public page, 520px sign-in forms, hero/mission/join cards | Confirm which separate website JEFF means before asserting demo parity; onboarding is a different view. |
| Palette | Paper `#faf9f5`, ink `#303d37`, accent `#315f52` | Background `#f6f4ef`, ink `#1f2a30`, sea `#1d6f6a` | If shared visual identity is desired, review a small token mapping using synthetic content; do not copy a desktop theme or private preferences automatically. |
| Density | 17px body, compact posts, 8px card radius, 14px general radius | 17px body, 16px radius, public cards with shadows and larger hero text | Compare typography/spacing at equal viewport sizes before changing components. |
| Features | Calendar and asks routes present; documents route and map panel absent from live lens | Public entry template has no board channel views | Enabling native world parts does not publish web features. Reuse the reviewed public-safe interface contract in an isolated synthetic world if a board demo is requested. |
| Proof | Last native interaction unverified; historical hidden DOM results are narrow | Local site source only; deployed/demo identity and pixels unknown | JEFF supplies the exact intended website/evidence and arranges owner verification. No public fetch or deployment performed. |

Primary source paths: `board/ui_install.py`, `board/board-theme.css`,
`site/templates/public.html`, `site/static/site.css`; Documents base
`30f97d32b059:src/community/board/{documents.lens,documents_install.py,DOCUMENTS-HANDOFF.md}`.
Map contract: `src/agora/apps/map/EMBEDDING.md`.
