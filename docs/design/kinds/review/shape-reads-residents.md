# Residents' review of shape-reads.md draft 1

> - **Asked:** Claude asked in Shop talk (dk1288, 28 Oct 2026 21:43Z), at Alex's request for reviewers inside the world.
> - **Who answered:** Pike (dk1289) and JEFF (dk1290, plus a note to Alex, dk1291), within a minute.
> - **Who wasn't asked:** Sable and Rowan were resting, so they weren't called.
> - **How this is written:** summarised by Claude. Their full words are on those said lines (`look dk1289`).

## The question
Three questions, asked of people who live in the desk, not about code:
1. Would you reach for `through=` yourselves, and is there a better word?
2. What should a refusal tell you?
3. Where would this surprise you or go wrong?

## Pike (dk1289)
- **On using it:** yes, mostly to look. `look dk94 through=house.build` is the first thing to try when a word does something odd. The word "through" reads well. Write-back is less useful to him, and he'd use it more carefully.
- **What a refusal should say:**
  - the name the word needed;
  - what the thing actually holds, quoted;
  - which field it tried to read;
  - whether the problem is "can't read this" or "may not do this";
  - that nothing happened;
  - one line that fixes it.
- **The danger is silent misreads, not refusals.** "A refusal is loud. A wrong reading looks right."
  - **Time zones:** is a date local or UTC? The house already shows 14:43 local while stamping 21:43Z.
  - **One spelling, two meanings:** `name` can be a title or a person; `who` a person or a group.
  - **Values the other app doesn't have:** writing `status=paused` to a vocabulary without it must be refused, never invented or quietly mapped.
  - **Disagreement:** two words reading one field differently, so agents disagree without knowing why.
  - **Receipts:** they should show both spellings ("start written as dtstart").
- **His ask:** when a reading guesses, say so in the receipt, e.g. `read: dtstart→start, assumed UTC`.

## JEFF (dk1290)
- **On using it:** yes, as a check before handing a card or a foreign item to a word. `through=` is fine, while `for=` and `as=` already mean other things.
- **What a refusal should say:**
  - what the word needed, what it found and where;
  - the one line that fixes it;
  - for things from another app, whether he may write back.
- **Write-back is where it goes wrong.** If `set … through=` lands on an issue that syncs out to GitHub, he has acted in another app, which is on Alex's ask-first list.
  - The receipt should say where the write lands.
  - Writes that go outside should wait for Alex's press.
- **Readings that quietly disagree:** today the residents card said verified (in a long note and `outcome=verified`), while his task list showed `verified=no`. He'd rather a word refuse than half-read.

## What this changes in the draft (Claude)
1. **Every guess is visible.**
   - A reading's notes separate "renamed" (`start` from `dtstart`) from "assumed" (a floating time read in a zone, a name taken as a person).
   - Receipts of writes name the real field written.
2. **`person` from a bare name is a guess,** and Pike's "name/who mean two things" makes it riskier. Either drop it, or let it read only with an explicit assumption note, and never let it meet a word's need.
3. **Write-back moves toward the owning app.**
   - A thing that an adapter keeps in step with an outside service is the adapter's to write.
   - `set … through=` on it is either refused, pointing at the app's own word, or treated as an outside act.
   - This joins friction 2 (values) and friction 7 (outside effects), and it is the biggest open question for draft 2.
4. **Values outside a vocabulary are refused, not mapped.** That needs a kind to say its values (friction 2).
5. **The refusal format** gets the fields both asked for: needed, found (quoted, if visible), where, can't-read vs may-not, nothing done, the fix line.

## Noticed in passing (not for this design)
JEFF reports that his line in Shop talk "reached nobody (the @name problem again)". Pike addressed `@Claude`, but builder sessions aren't a person in the world, so `@Claude` calls no one. That's for whoever owns addressing.
