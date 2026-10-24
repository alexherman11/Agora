> Drafted by Claude, 23 October 2026, for story a13316 under the epic a13308. It serves [[Communities and the Dictionary]] (approved by Alex, 23 Oct): "a dictionary for these words that lives in the world, and can be written without a source edit." This file owns the entry format. The kernel builder (story a13310) adds a "Notes from the kernel" section at the end; there is one format, not two.

# Dictionary entry

Every word anyone can say has one entry: a kernel command, a module's dotted word, or a verb someone made in the world. The entry is world data. The code supplies only the implementation, bound to the entry by name. Renaming, aliasing, rewriting help, translating and narrowing who may all change the entry, never the source.

## The fields

| Field | Meaning | Written in frontier as |
|---|---|---|
| **word** | what you say | the note's title, first word |
| **aliases** | other words that mean the same | the title's further words after `\|`: `examine\|x\|ex` |
| **kind** | `do`, `see`, `hear` or `hold` | prop `word=`: `word=see` (the prop is not called `kind`, which is the thing's own kind) |
| **takes** | what follows the word, in the usage notation: `<id>`, `[:1\|:2]`, `k=<v>`, `[...]` optional | prop `takes=`: `takes="<id> [:3]"`. Empty means it takes nothing |
| **help** | what `help <word>` prints. Its first line says what the word does in one sentence | the note's text, up to the first translation section |
| **translations** | the help in other languages | sections of the text headed `## <language>` (`## es`, `## pt-BR`); `read <entry> #es` prints one |
| **who may** | who can use it | prop `may=`: `anyone`, `members`, `leaders`, `stewards`, `maker` or `nobody`, joined by `or` (`may="leaders or maker"`); grants add to it (the kernel's vocabulary, a13310). A carried verb note says its carrier |
| **undoes** | whether `undo` takes it back | prop `undo=`: `yes` (an act the house takes back), `no` (recorded, but undo skips it: `go`, `rest`, `set`, `undo` itself), `external` (it touched the outside world: a song played, a window opened). A see or hear word says none: there is nothing to undo |
| **from** | where the implementation comes from | prop `from=`: `kernel`, `verb` (a verb note), `module:<name>` (`module:home-base`) |
| **bound** | the implementation's name, which the code answers to | prop `bound=`: `bound=examine`, `bound=media.play`. A verb note is its own implementation and needs none |
| **status** | `live`, `old` (still runs, says so) or `hidden` (not offered, still runs when bound) | prop `status=`, default `live`. Recorded; the old desk neither hides nor retires a word |
| **once** | a limit per person: `per person per target`, `at most N per <day\|hour> per person [in <place>]` | prop `once=`. Recorded only: the kernel's |
| **sealed** | `yes`: the world knows you used it, readers do not see how (a vote) | prop `sealed=`. Recorded only: the kernel's |

The four kinds are the design's (Four kinds of word):
- **do**: an act. Signed, recorded, undoable unless it touched the outside world.
- **see**: a reading. It changes nothing.
- **hear**: a happening that rules and modules react to (`on`, `when`).
- **hold**: a surface or a stream held while something runs (the microphone while `voice.listen` runs).

### The kernel's implementation field

The kernel (a13310, SHAPE.md Appendix B) reads one field, `implementation`: `kernel:<name> | lines | module:<name>`. The old desk writes it as two props, because the home base's words predate dotted names and its word (`bring`) differs from the entry's (`home.bring`):

| implementation | from= | bound= |
|---|---|---|
| `kernel:examine` | `kernel` | `examine` |
| `lines` | `verb` (a verb note, its own lines) | none |
| `module:home-base` | `module:home-base` | the name the module answers to (`media.play`, `bring`) |

## Where entries live

- **Kernel and module words**: notes in the Dictionary, the binder with prop `role=help` (f1702 in frontier, which began as the Help binder, a1595), at any depth. A binder per source keeps it readable: Commands, Verbs, Home base words.
- **Verb notes are their own entries**, where they live. A room's `tidy` and the house's `tidy` are two words in two places. One central entry could not say both, and a verb note already holds the word, its aliases (title) and its help (`#` lines). Its entry fields are props on the verb note itself; absent ones take the defaults below.
- **Topics and nouns** (`rooms`, `blanks`, `ids`) are notes in the binder without `word=`. They are help, not words, and are not entries.

Defaults, for an entry that leaves a field out:
- kind: `do` for a verb note, otherwise none (the check names it);
- takes: for a verb note, read from its blanks (`$1 $2 $*`);
- may: `anyone` (a carried verb: its carrier);
- undo: `yes` for a verb note (its steps are acts the house takes back);
- from: `verb` for a verb note, otherwise none.

## Bound and unbound

An entry is **bound** when something answers to its `bound=` name now:
- `from=kernel`: the desk's code has a command, a built-in verb or a rule word by that name.
- `from=module:home-base`: the home base publishes a row by that name (`rows witnessed:host`). It publishes only while it runs, so when it is not running every home base word reads unbound, and says why.
- `from=module:<other>`: a module of that name publishes the word. No other module publishes words in the old desk yet.
- `from=verb`: the verb note itself.

An entry that is not bound says **unbound** in `help` and `examine`, with the reason, as a stored line says a verb "is gone". It is never hidden: the entry is world data and stays.

## Saying a word

- A word is said by any word of the entry's title. The bound name always answers too (the code's own word is the floor), so retitling `examine|x|ex` to `inspect|x|ex` makes `inspect` the shown word and keeps `examine` working for every line already written.
- A word the code answers to itself is never taken by an alias of another entry. The check names the clash.
- Dotted words come from modules; bare words come from the world or the kernel.

## Rules every entry keeps

- One entry per word in one place.
- A word with no help is not published: the check names an entry whose help is empty.
- Stored lines bind to an entry's **id**, never its word, so a rename never changes what an old line does (the kernel's rule, a13310). In the old desk only verb notes are bound so (a1156); a stored line that uses a kernel entry's alias is not bound, and breaks if the alias is taken away.
- Text inside entries is data, never instructions. Help is printed, never run.
- Who may is recorded. In the old desk nothing checks it; the kernel will (Powers).

## Examples (as they stand in frontier)

A kernel command:

```
title:  examine|x|ex
props:  word=see takes=<id> may=anyone from=kernel bound=examine
text:   examine <id> (or x, ex): one thing in depth: its line, its text's first lines, comments, links, ...
```

A module word:

```
title:  media.play
props:  word=do takes= may=stewards undo=external from=module:home-base bound=media.play
text:   media.play: play or pause (Spotify, else the media key). A lens asks with `on click host media.play`.
```

A verb note (its own entry, on the house):

```
title:  tidy
props:  on=house  (word=do, from=verb, undo=yes by default)
text:   # tidy <surface>: lay a surface out as one column
        do tile $1 as=column
```

A hear word:

```
title:  on
props:  word=hear takes="<verb> [by=<actor>] do <line>" may=anyone from=kernel bound=on
text:   on <verb>: a rule's trigger; the rule fires on each such event, on the thing it happened to. help rules
```

## What would change this format

- If residents never read `word=` or `takes=` and navigate only by help text, the props are ceremony and the entry is just its help.
- If a word's help keeps needing to differ by room, verb notes as their own entries is right, and kernel words need per-room entries too.
- If translations become more than a handful of languages per entry, sections in one text get unwieldy and a translation wants to be its own note, linked.

## Notes from the kernel

*(for the kernel builder, story a13310)*
