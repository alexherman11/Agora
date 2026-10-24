> Written by Claude (kernel story, Board a13310), 23 October 2026. What the walking skeleton is, how to run it, and the evidence for it, labelled **ran** (executed here, numbers as printed), **read** (from source) or **imagined**. The design it follows is [[SHAPE]] (the kernel's first shape), section 14.

# The walking skeleton

A small kernel that holds the shape's core: a log of facts as the truth, persons from the sign-in seam, the dictionary, who may, who sees, sealed likes, undo, and a module in another language. People and agents use it only over HTTP on loopback. It touches nothing of the desk's: no file in `research/text-desk-lab/`, no world, no port of the desk's.

## What is here

| File | Lines | What it is |
|---|---|---|
| `kernel/store.py` | 153 | The log: records of facts, chained by a digest over value hashes; replay that never runs a word |
| `kernel/lines.py` | 69 | `split_batch`, copied from the desk unchanged, and one parser for every word |
| `kernel/kernel.py` | 672 | The act loop, the dictionary lookup, who may (with the module intersection), who sees, the fence, the seal, joining |
| `kernel/words.py` | 300 | The kernel's own words and their entries, in the dictionary story's format: `look`, `help`, `post`, `like`, `pin`, `undo`, `off`, `status` |
| `kernel/modules.py` | 197 | The module host: processes speaking newline JSON on stdin and stdout |
| `kernel/door.py` | 190 | HTTP on loopback: `/do`, `/see`, `/keep/account`, `/health`; sessions asked of the entry service |
| `modules/tally/tally.js` | 90 | The module, in JavaScript (Node): `tally.top` (see) and `tally.pin-top` (do) |
| `tests/test_skeleton.py` | 587 | 20 tests over real HTTP: 18 with a stand-in for the entry service, 2 against the real one |
| `genesis.example.json` | | A world's first record, with placeholders and no secrets |

(**ran**: `wc -l`.)

## Running it

From `research/kernel-lab/`:

```bash
C:/Projects/Agora4/.venv/Scripts/python.exe -m unittest discover -s tests -v
```

The door by hand (loopback only; the shared secret comes from the environment, which Alex sets himself):

```bash
C:/Projects/Agora4/.venv/Scripts/python.exe -m kernel.door --world <a new folder> --genesis genesis.example.json --port 8840 --entry http://127.0.0.1:8841
```

Nothing appears on the screen: the module runs with no window (`CREATE_NO_WINDOW`), and the tests start and stop everything themselves.

## What it does, in the words a person sees

From an in-process run of the same words (**ran**, 23 Oct; the tests check each of these over HTTP):

```
[Maya]  like sb15             ok like sb15 [r6] · 1 like; who liked it is sealed
[Maya's agent] like sb15      refused: you already like sb15; once each. undo takes yours back
[Maya]  pin sb15              refused: pin is for leaders of Seabright; help pin says more
[Alex]  pin sb15              refused: you have not looked at sb15 yet; look sb15 first
[Alex]  look                  Seabright: the feed, 2 posts …
[Alex]  pin sb15              ok pin sb15 [r7] · it stays at the top of the feed
[Maya]  like sb17             refused: no thing called sb17 here; look shows what there is   (a post in Organizers)
[Maya]  like sb999            refused: no thing called sb999 here; look shows what there is  (no such thing)
[Maya]  undo r7               refused: r7 is Alex's; you may undo your own acts, leaders the acts in their groups, stewards any
```

## Evidence

**Ran**, 23 Oct 2026, Windows 11, Python 3.12 (the pinned venv), Node v25.6.1:
- The suite: `Ran 20 tests in 25.835s`, `OK`, then `Ran 20 tests in 24.730s`, `OK`. Each test makes a fresh world and real HTTP servers on free loopback ports. (Earlier the same day: 17 tests, `OK` twice, before the seam and dictionary changes below.)
- After the runs, no process was left running `tally.js` (counted through `Win32_Process`: 36 `node.exe` belonged to other programs, 0 to the tests).
- The door started by hand on port 8849 answered `{"ok": true, "records": 3}` (genesis and the two words tally offered) and refused `look` without a session: `{"error": "sign in first"}`.
- A load of 200 people in process, without HTTP: 1,801 records; a post 1.75 ms and a like 1.65 ms each, including the fsync; `look` over 600 posts 6.0 ms; a full replay of the log 74 ms; the log 639,161 bytes (about 355 bytes a record); the replay matched memory. The fsync dominates; I did not profile it.

What the 20 tests show (each named after what it checks):

| Claim from SHAPE | Test | What it checks |
|---|---|---|
| A person and an agent both use it over HTTP | `test_person_and_agent_use_it_over_http` | Maya's agent posts; the record says `by` the agent, `for` Maya, `via agent`; the feed names it "agent for Maya" |
| Every word has an entry with help (section 4) | `test_every_word_has_an_entry_with_help` | All seven words have entries with help; tally's are `module:tally`; an offer without help, and one outside tally's namespace, are not published |
| `pin` refused to non-leaders; look before acting (sections 6, 9) | `test_pin_is_for_leaders_and_needs_a_look` | Maya and her agent are refused; Alex is refused until he looks; a second pin changes nothing and writes nothing |
| Sealed authorship (section 8) | `test_like_is_sealed_and_once_each` | Once each across a person and her agent; the two sealed records hold neither liker's id; no reader is shown who liked; Maya's own undo finds her sealed like, and the undo is sealed too |
| Who sees, at every read (section 7) | `test_who_sees_applies_at_every_read` | A group's post is missing from a non-member's feed and from `tally.top` read for her; refusing it reads exactly as refusing a thing that does not exist; sign-in answers are seen by the person and the leaders, not by another member |
| Undo's own may (section 6, approved) | `test_undo_has_its_own_may` | Maya can't undo Alex's pin; a post that has been liked and pinned can't be undone ("changed since"); the steward may undo Maya's post; no redo; genesis can't be undone |
| Once each, "at most N" | `test_the_feed_takes_a_few_posts_a_day` | The sixth post of a day is refused, counting her agent's; another person is not limited by hers; an undone post no longer counts |
| A module publishes words and answers with lines (section 11) | `test_module_publishes_and_answers_with_lines` | `tally.top` ranks by likes; Maya's `tally.pin-top` is refused because she can't pin, though tally holds a pin grant; Alex's is one record, `by` tally `for` Alex, its part's words `pin sb…`; `status tally` answers; undo takes it back |
| The other half of the intersection | `test_a_module_holds_only_its_grants` | With tally granted only `look`, Alex (who may pin) is refused: "tally holds no grant for pin" |
| The off word | `test_off_takes_every_grant_and_undo_turns_it_on` | Only a steward may; it revokes the grant in one record and stops the process; its words then say "unbound"; undo starts it again and it re-binds its words without writing new entries |
| A module's answer is admitted only if what it read still holds | `test_a_module_answer_is_admitted_only_if_what_it_read_still_holds` | A pin read before a like is refused as stale; an act on a thing it never read is refused; an answer holding a reading is refused; nothing is written by any of them. (Called on the kernel directly: HTTP cannot place a like between a module's read and its answer.) |
| The door trusts only the session | `test_the_seam_and_the_door_trust_only_the_session` | `/keep/account` without the secret is 403; a wrong invite is refused; no token, a made-up token and a cross-site `Origin` are refused; an `as` in the body is ignored; a repeated press id is "already done" and writes nothing |
| The log is the truth (section 1) | `test_replay_checks_the_chain_and_survives_redaction` | A changed value breaks the digest; a value redacted to `{"redacted": <its hash>}` still replays, and the record after it still applies |
| | `test_a_cut_short_last_line_never_happened` | A half-written last line is dropped on replay |
| Many people at once | `test_many_people_at_once` | Eight neighbours post and like on threads at once: no refusal, 8 likes, 33 posts, and the replay matches memory |
| A restart | `test_a_restart_rebuilds_from_the_log` | A new kernel on the same folder, with no genesis, shows the same feed; Maya can still undo her sealed like (the seal secret is in the keep); seen marks are gone, so Alex looks again |
| A module that dies | `test_a_module_that_dies_mid_call` | Its call is refused with its last error line; it is not restarted at once; the next call says when it stopped and when it will be started again |
| A renamed word keeps working (DICTIONARY-ENTRY.md) | `test_a_renamed_module_word_still_reaches_its_module` | After `tally.top` is given the word `best` and the alias `top`, all three answer and tally is asked by its bound name; restarted, tally binds the renamed entry and publishes no second one. With the fix taken out in a scratch copy, it fails with "tally has no word best" |
| The seam, with the real entry service | `test_a_real_session_reaches_the_kernel` | The sign-in story's own service, in test mode on a free port, told to read no `.env`: a Google sign-in on a three-use invite; its `/internal/session/check` hands over the record; `/keep/account` makes the person with `joined_via` holding the invite's id; the kernel takes a post from her `agora_session` cookie and shows it to the leader; after `sign_out` her next line is 401 |
| | `test_no_invite_from_the_entry_service_means_no_person` | In a world where the entry service counts invites, a join with no invite is refused |

Every test ends by checking that a refusal wrote no record, and most by replaying the log from disk and comparing it with memory, fact for fact.

## What the tests found

Five things I would not have known from the shape alone:

1. **An agent should be announced at sign-in.** The first run created an agent's thing lazily, on its first request, so a refused line still wrote a record. The fix belongs to the seam: the entry service says `agent` on `/keep/account` when it opens an agent's session. I've added it to the seam notes.
2. **Your own act counts as having seen what it wrote.** I had not carried this desk rule over, and Alex's second `pin` of a post he had just pinned was refused as stale against his own act.
3. **A crashed module would be restarted after every act.** The world says it is on, so the reconciler started it again each time. It now rests 30 s after dying, and the refusal says when it stopped and when it will be tried again. Whether a module that keeps dying should turn itself off is a question for the steward, not a timer.
4. **The kernel said "did not answer in 10 s" after half a second,** because a dying process had closed its output but had not yet been reaped. It now waits for the exit and quotes the module's last error line.
5. **A module cannot know whether its answer was admitted.** Tally counts three calls answered where the kernel admitted one. If modules need to know, the protocol needs a `done {use, record | refused}` message back. I have not added it.

Two more came from building against the sibling stories' files rather than my own guesses:

6. **A module must be asked by its bound name.** The dictionary format's `bound` field looked like a frontier detail. It isn't: with one implementation field the kernel sent a module the word as typed, and a rename in the world broke it. The kernel now reads `from` and `bound`, and the bound name always answers too, as the format says.
7. **Building a seam from both sides at once crosses.** I moved the kernel to the conventions SEAM.md first described while the sign-in story moved its service to the kernel's first ones. We froze on its working tree (`X-Kernel-Secret`, the `agora_session` cookie, `{account: <id>, method, agent, record}`); the kernel accepts the older forms until that is committed. Recorded in SEAM.md's "Notes from the kernel".

And two choices made while building: the seam's invite counting is a fact of each world, `invites_counted_by: entry | kernel`, so exactly one side counts; and the seal is keyed by the entry's **id**, not its word, so renaming `like` never stops anyone undoing their own like.

## Not built, or not yet tested

- **Not built:** *hear* and *hold* (no happenings, no stream, no leases); verb notes (`impl: lines`) and rules; blanks (`$me`, `$new`); selections; snapshots and log segments; the `redact`, `grant`, `freeze` and membership words (redaction is tested in the store only); words that edit an entry (rename, alias, hide); the painter's routes.
- **Seen marks are in memory**, not in `seen/` beside the world as SHAPE says, so a restart forgets them (the restart test shows it).
- **The real entry service** is tested in process, against its working tree of 23 Oct evening, which was not yet committed; the two tests may need the frozen contract once it is. It does not yet call `/keep/account` itself, so the test makes that call where it will (SEAM.md section 4). Agent sessions do not exist there yet; the stand-in has them.
- **No sandbox.** A module process can do anything the account it runs as can do on the machine (SHAPE section 11).
- **One machine, one process.** 200 people in process at under 2 ms an act is evidence about the kernel's own cost, not about HTTP under load or the box in Oregon (**imagined** beyond what was measured).

## Next

The lens compiler facade (SHAPE section 12): give `scene.py` and `lens_ir.py` an adapter that answers as the desk's World from kernel things, and report its size honestly, because it decides whether "new kernel, same language" holds.

## Related documents

- [[SHAPE]]
- [[Communities and the Dictionary]]
- [[Current Implementation]]
