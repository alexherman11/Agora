# House messages from the Agent Book

Builder implementation note, 4 November 2026, task dk2219.

The House reads `look "Agent Book"` through its ordinary reading door on every
render. **Read:** that name resolves to dk2190 in the live desktop. There is no
saved production copy, cache, startup load or source-template fallback. Once
this code is activated, editing a section affects the next rendering without a
House restart. This worktree has not been deployed.

Headings are exact Markdown headings. The body ends at the next heading of any
level; fenced headings are literal text. This deliberately leaves the worker
brief's separate “Proposed additions” subsection out of the brief. Introductory
prose inside the selected body is preserved. A body consisting entirely of a
`text` fence is unwrapped before filling; this lets a header fragment contain
literal Markdown headings. Other fences remain in the resulting message.

`Kernel.fill_text` extends the existing `$` vocabulary for prose:

- `$.name` reads supplied message facts, such as `card`, `owner`, `words`, or `list`.
- `$[[House settings]].codex_model` reads a fact through the same reading door.
  `$[[id|label]].fact` also works; the label does not affect resolution.
- `$now` and `$today` use UTC, as in Lines.
- Quotes are prose, not command delimiters. Substitution happens once; dollars
  in inserted task text or worker words are never expanded again.

`help $` documents the prose forms. Command substitution and session names keep
their existing behavior. The renderer neither executes Lines from a template
nor evaluates expressions.

Worker briefs, follow-ups (including an already running child's next turn),
card corrections, cut-off notes, welcomes, task headers, time, chat and card-note
wakes, explicit wakes, compaction, outcomes, reminders, handovers and the older
manager receipt all use the book headings. Queued card/ownership notes retain
their heading and facts and render when the follow-up is built. Task rows remain
structured projection data; the House and compaction hook add the book's header.
Souls, personal prompts and the charter remain their existing live world texts.
The single book Welcome replaces both the old default and `cfg.welcome` override.
Prompt headers, missing-charter/task-list notices, chat about-annotations,
unavailable-owner reasons, waiting-worker rows, follow-up attribution and the
wordless-worker notice also read their own headings. Receipts, refusals, help,
logs and status descriptions stay in source, as requested. The unused
`House.context` and `House.in_chat` helpers are removed.

A missing, renamed, empty or unreadable heading yields
`Message unavailable: Agent Book / <heading> (...)`. It supplies no operational
instructions. Missing fill-ins and unreadable references also name the gap;
transport exception bodies are not included. This is deliberately not a copy of
the old wording. Root `BOOK-ADDITIONS.md` contains the 15 additional fragment
headings and `A picture is ready` / `A picture failed`, preserving the previous
source wording with `$` fill-ins. Those sections must be added to the live book
before landing; otherwise their messages name the missing headings.
`house.snap last` still holds the actual result. No live book text was changed
by this worker.

**Ran:** `tests/test_house_messages.py` edits every existing message heading in
hidden kernel fixtures, renders through the same House, then renames the heading
and checks the diagnostic. It also exercises actual brief, welcome, wake,
task-header, reminder, follow-up, outcome and compaction paths, referenced-fact
edits, visibility, single-pass expansion, unavailable documents and section
boundaries. The fragment paths also exercise edits without recreating the House,
including attribution and a simulated worker ending without words.
`fixtures/agent-book.md` is test data captured from the Workers and Messages
sections on 4 Nov, plus the proposed `BOOK-ADDITIONS.md` sections. It is not a
runtime fallback.

Source: word
Missing-word: none (heading-based prose rendering and the prose fill-ins are implemented here).
