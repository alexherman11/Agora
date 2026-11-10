> Claude, 23 October 2026, story a13316. Evidence for [[DICTIONARY-ENTRY]]: a small tool built in frontier from help and the dictionary alone, then renamed and given Spanish words with no source edit. Every line below **ran** through the door as claude; the full transcript (each line and its answer) was kept in the session's scratchpad, not in git.

# The lending shelf: a dictionary trial in frontier

## What was asked

The coordinator, from Alex's guidance that tests be realistic: build a small new tool using only the dictionary and help (a lending shelf for neighbours' tools: lend, return, who has it), rename a word and add a Spanish alias without a source edit, and show that old stored lines keep working.

## What I did, as an agent who has not read the code

I read only what the desk printed: `help dictionary`, `go`, `help verbs`, `help rooms`, `help selections`. From those:

1. A room: `do create f149 kind=surface title="Tool shelf" layout=column` then `do prop $new role=room` (f13529, in Home).
2. Three tools as notes: Ladder (a13532), Drill (a13534), Wheelbarrow (a13536).
3. Four verb notes living in the room (`on=f13529`), each a few lines:
   - `lend` (a13538): `# lend <tool> <name>: ...` then `do prop $1 lent_to=$2 lent_on=$today`
   - `return` (a13540): `do prop $1 remove=lent_to,lent_on`
   - `who-has` (a13542): `table prop:lent_to,in:$here cols=title,lent_to,lent_on`
   - `borrow` (a13544): `lend $1 $me`, a stored line. Its receipt: `its words are bound (a1156): lend → a13538`.
4. Used it: `lend Ladder maya`, `borrow Drill`, `who-has` (a table of two), `return Ladder`, `who-has` (one).

Then, with no source edit:

5. `do retitle a13538 title="loan|prestar"`, `return|devolver`, `who-has|quien-tiene`; and the kernel's examine entry `examine|x|ex|examinar`.
6. A Spanish help section on loan: `do append a13538 line="## es"` and a `#` line in Spanish.
7. Old and new lines:
   - `borrow Wheelbarrow`: `(borrow a13544: lend Wheelbarrow claude)` then `(loan a13538: do prop Wheelbarrow lent_to=claude ...)`. **The old stored line still runs**: it is bound to the note, not the word.
   - `prestar Ladder juniper`, `devolver Drill`, `quien-tiene`: each works.
   - `examinar a13532`: examine's answer.
   - `rows dictionary entry=a13538`: `word=loan · aliases=prestar · kind=do · takes='<tool> <name>' ...`.

## Where it hurt

1. **A verb note's Spanish help printed inline** among its English lines (`es`, then the Spanish), although the format said translations are sections. Fixed in source (a13316's second commit; Rough spots a13518): a `## es` line in a verb note starts a section; help names it (`also in: es (read a13538 #es)`) and `read a13538 #es` prints it.
2. **The dictionary said `lend` takes `$1 $2`**, not `<tool> <name>`. I set `takes=` by hand (world); the same fix now reads the placeholders from the verb's first `#` line, so `tidy` reads `<surface>` too.
3. **The old typed word answers nothing helpful.** After the rename, `lend Drill maya` says `MISS unknown command 'lend'`, with no word that it is `loan` now. Stored lines are safe; a neighbour's habit is not. An idea for the IDEAS card (a13437): a renamed word keeps answering for a while, as `old`, saying its new name.
4. **The four kinds held up**: lend, return and borrow are `do`, who-has is in effect a `see` but the verb note defaults to `do` (it could say `word=see`; nothing told me to).

## What it shows, and what it does not

- Shown (ran): a tool made of words alone, found and used through help; renaming and Spanish aliases as note edits; a stored line surviving a rename because it is bound to an id; a kernel word gaining a Spanish alias.
- Not shown: anyone else using the shelf; a rule or a lens button calling the renamed word (only a verb's stored line was tried); who may (recorded, never checked); a kernel alias inside a stored line (not bound at save, a known gap).
- The same story is now section 10 of `notation/test_dictionary.py` (a rooms test), on a world it builds itself.
