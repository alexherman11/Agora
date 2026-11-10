# Review: the three builds Alex approved on 28 Oct

*Adversarial review by Claude, 28 Oct 2026, about 20:20 PDT. Read-only on the repository. Every probe ran on a fresh
temporary world under the session scratchpad (`review-builds/`), never the live world. Scripts: `probe_rules.py`,
`probe_rules2.py`, `probe_outside.py`, `probe_kinds.py` there.*

The code moved while I worked. `kernel._rule_hears` gained a new branch at 20:14: a module acting on its own now
counts as the person it is installed for. This review covers that version (`kernel/kernel.py:1588-1610`).

**ran**: the three test files pass: `58 passed in 3.73s`. Everything below is a gap in the tests, not a failing test.

## High

**H1. A kit drops `by`, so a rule you take hears everyone.** (ran)
`kits.py:16` lists the rule fields that travel, and `by` is not among them. `take` writes the facts directly
(`kits.py:195-205`), so the new rule has no `by`. That means it is treated like an old rule and hears everyone.
A bundle that keeps `by` is refused outright.
Output from `probe_rules2.py p2`:
`rule in crew by= maker` → `taken rule by= [None]` → `P2 kit-rule-heard: 1 made_by ['rb2']`.
Sable, a plain member, posted, and the taken rule ran as Alex.
`take bundle=… "by": "maker"` → `refused: not a definition-only kit`.
*Fix:* add `by` to `FIELDS["rule"]`. In `take`, write `by=maker` whenever a rule arrives without one. Do the same for
genesis `things` that are rules.

**H2. `own()` calls someone else's thing "yours" when a module installed for you made it for them.** (ran)
`kernel.py:1020-1025` checks the person against three values: the maker, the maker's person, and `for`. A module
installed for Alex that answers Pike's call makes the thing with `made_by=<module>` and `for=Pike`. The maker's person
is then Alex, so the thing counts as Alex's.
Every module on Alex's desktop is installed `for: steward` (`desktop/kernel-desktop/kdesk.py:66-84`).
Output from `probe_outside.py o1`:
`made_by ob74 for ob76 sees group:ob79` → `own(alex)= True own(pike)= True` →
`O1 Alex's module reading marks it: yours` → `O1 sent to Nominatim while Alex draws: ['Harbor shelter intake, 5 Elm']`.
That text belonged to the crew and was not Alex's.
(The map module itself is installed without `for` (`apps/map/install.py:126`), so today this is a trap for the next
module that reads the marks. In o1 I built the module-answer actor by hand, the same way `admit` builds it,
`kernel.py:1726`.)
*Fix:* when the thing has `for`, `for` alone decides. Fall back to the maker's person only when `for` is missing:
`owner = a.get("for") or (state.get(maker,"for") if kind(maker) in ("agent","module") else maker)`.

**H3. The map sends saved world text out as if someone had typed it.** (ran)
`point_of` sends any text that names nothing to Nominatim (`map.py:299`). Two callers pass it text read from a world
thing, not text the caller typed:
- **Replanning a route.** `w_route` reads `stops` from the route thing (`map.py:704`) and passes it to `plan`, which
  calls `point_of` (`map.py:670`). Output from `o2`: Sable replans Pike's crew-only route →
  `O2 sent while Sable (not its maker) replans: ['Harbor shelter intake']`. The text goes out before the kernel decides
  whether she may even `set` the route.
- **A layer's `shows=`.** `w_layers` runs the layer's saved reading (`map.py:742`). A `map.find …` reading reaches
  `geocode` (`map.py:433`). Output from `o3`: Pike's crew-only layer →
  `O3 sent while Sable draws the map: ['Harbor shelter intake 5 Elm']`.

*Fix:* give `point_of` and `w_find` a "typed" flag. Text read from a thing may go out only when that thing's row says
`outside` is `public` or `yours`. For a layer, run `map.find` locally unless the layer row is public or yours.

## Medium

**M1. A member's act still fires someone's `by=maker` rule, through a leader's `by=anyone` rule.** (ran)
A rule's act is recorded as its maker's. When that maker is a leader, every member's `by=maker` rule hears it.
`_rule_hears` never looks at `caused_by`. Output from `p1`: Sable posts → Alex's `by=anyone` rule makes a memo as Alex
→ `P1 pike-heard: 1`. Sable also chose the `$target`.
*Fix:* when a happening's record has `rule`, also require the first cause (`caused_by`) to be heard.

**M2. A module on its own now counts as its person, so it counts as a leader too.** (ran; new code at 20:14)
This contradicts the brief ("a module acting on its own is no one's act"), and no test covers it. On the desktop every
module is installed for the steward. So the module's own acts, including announcements that a member's request set
off (the window module says `window.opened` for any window, `kd_window.py:1174`), are heard as Alex's acts by every
member's `by=maker` rule.
Output from `p3b`: `announce win.opened` and `module_own make kind=memo` → `pike-window-rule: 1 | pike-memo-rule: 1`.
The branch does fix a real regression: `make kind=rule on=window.opened do=…` is the example in the help
(`kd_window.py:767`) and in `test_kdesk.py:216`. Without the branch, that rule would never fire.
*Fix:* treat the module's own act as its person's act only for that person's own rules (`who == maker.person`), never
as a leader's act. Add tests for both directions. Alex should confirm the new wording.

**M3. Undoing a `forget` switches a rule back on, and it runs as its maker.** (ran)
`left_off` in `undo` (`words.py:524-528`) covers the STEERING facts and `off`, but not `forgotten`. Output from `p4`:
Pike forgets his own rule; Alex runs `undo r5` → `forgotten= None off= None` → `P4 pike-rule-ran notes: 1`.
*Fix:* treat `forgotten` the way `off` is treated. When someone other than the maker un-forgets a rule they did not
forget, leave it at `off=yes`.

**M4. A mark on a grandchild kind does not count for its parent kinds.** (ran)
`meeting` extends `event`, and `council` extends `meeting`. A note marked `council` is a council and an event, but not
a meeting. `fits` checks only `is.<asked kind>` (`kinds.py:204-210`). Output from `probe_kinds.py`:
`rows council has odd: True`, `rows meeting has odd: False` (a thing whose own kind is council: `True`),
`kinds odd: ['note', 'council', 'event']`.
*Fix:* a child kind also holds things marked `is.<k>` for any declared kind `k` that descends from it.

**M5. `contacts` carries phone numbers that `outside_not` does not name.** (ran)
`shown` builds `contacts` from the `contact:*` facts (`kernel.py:469`). `outside_marks` names only the raw key. Output
from `o4`: `{'contact:ob74': '555-0101', 'contacts': 'Pike 555-0101', 'outside': 'public', 'outside_not': ['contact:ob74']}`.
A module that strips the keys in `outside_not` would still send the phone. The map is safe because its `KEEP` list
leaves `contacts` out.
*Fix:* fail closed. Have the kernel list the keys that may go out (`outside_ok`) instead of the keys that may not, or
add derived keys such as `contacts` whenever their source is narrow.

## Low

**L1. `set <rule> by=` with nothing after it removes `by`, which turns the rule back into one that hears everyone.**
(ran) Output from `p5`: `by taken away | by now: None` → `P5 empty-by heard Sable: 1`. Only the maker can do this, but
it reaches "anyone" without saying "anyone".
*Fix:* refuse an empty `by`, or store `maker`.

**L2. `outside` and `outside_not` are ordinary facts anyone may write.** (ran)
`make kind=note outside=public …` → `ok make`. Rows with a known id are marked over by the kernel. Rows without one
(`history` rows, a module's own rows) keep whatever the fact or the module put there.
*Fix:* reserve both names (`words.py:222`). In `outside_marks`, remove both keys from any row whose id the kernel
does not know.

**L3. A leader's agents are heard as the leader** (ran, `p7`). So is any co-leader a group's leaders appoint. Alex's
words were "You, your agents, leaders". "Your leaders' agents" (JEFF for Alex) is a wider reading, so ask him.

**L4. `is.<kind>` is a plain fact.** (ran) A maker may write it with `set`, or at `make`, without `mark`. Non-makers are
refused (`refused: set is for whoever made it or leaders`). It adds no power: grant `only=kind:` and a rule's `of_kind`
still match a thing's own kind (read, `kernel.py:957-958`, `_rule_matches`). One rough edge: `actions` may offer a
module word whose grant will then refuse the marked thing.

**L5. The marks are advisory, and only the map reads them.** (read: `grep outside modules/`) The house carries
residents' chats to model providers without asking. That is outside tonight's scope, but it falls under the same rule
of Alex's.

**L6. A rule made through a module call runs as the module and hears only the module.** (read, `words.py:676-679`)
It does not hear the caller it was made for. This was true before tonight.

## Checked and fine

- **Unsealing through `by`.** A `by=maker` rule never hears a sealed act, and sealed records carry no `for`
  (read, `kernel.py:1293-1301`; the test passes).
- **`place_sees` agrees with `shown`.** (ran, `o5`) Checked for a closed-chat line, a crew note, `sees=leaders`,
  `sees=me`, and the child of a forgotten parent: all `False` / not seen by a newcomer. A group cannot be closed later
  with `set` (`refused: … is a group`).
- **`outside_not` cannot leak a hidden aspect name today.** Only the kernel writes `sees.<aspect>`
  (`words.py:846`, `kernel.py:1974`), and only keys already in the row are listed.
- **Only the maker may change `by`.** Someone else's undo of a `by` change leaves the rule off (ran, `p6`:
  `by anyone off yes`).
- **No other module breaks on the new keys.** (read) `model.py` dumps rows, marks included, into a loopback prompt,
  which is harmless. The map's place card skips object values. No module writes rows back as facts.

## What the tests miss

- `test_rule_by`: the module-for-person branch, chains of rules (M1), `take` (H1), undoing a `forget` (M3), an empty
  `by` (L1), rules in a group (only the place is tested), and agents of leaders.
- `test_map_outside`: `own` through a module installed for someone (H2), route replanning and layer `shows=` (H3), and
  the `outside_not` path for `location`. No word can write a narrow `sees.location`, so that branch is dead today.
- `test_shapes`: grandchild marks (M4), and `is.<kind>` written by `set` or `make`.

*What would change my mind:* if Alex treats a leader's `by=anyone` rule as fully his own act, M1 is intended. If the
map will only ever be installed without `for`, H2 drops to Medium.
