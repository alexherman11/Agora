# Kinds lab: working notes

> Working notes by Claude, 27 Oct 2026. Thinking in progress, not a proposal. The proposal, with the probe results, is README.md.

## Close reading of Alex's ask (C10, 27 Oct)

Eight moves in his paragraph, in order:
1. "start making a graph out of the agora space": the *space*, so kinds, words and people too, not only things.
2. "so many objects that are not well linked ... we need ways to traverse them": the problem is traversal of unlinked things.
3. Railing / fence / wood / wall: one object, many descriptions, "all kind of the same things, but some are subsets".
4. "a railing is a type of wall, but a wall isn't necessarily a railing": asymmetric.
5. document / pamphlet, running program / video game: the computing cases.
6. "object-type inheritance ... nested kinds ... if something specifies a certain number of features or aspects ... If something has less than it, it kind of sits inside": an intensional (aspect) definition.
7. "a verb for something ... that has the same but less of the aspects, should probably also apply to the outer one. Maybe not always": verbs flow from general to specific, with exceptions.
8. "think ... how we can think about kinds more dynamically": the deliverable is a way of thinking.

The logic from 2 to 6 is the thing I missed first time: **he reaches for nested kinds *because* things are unlinked.** Kinds are roads. A book with no citations is still findable because it sits on a shelf among its kin. Flat kinds are fifty islands; nested kinds are shelves within shelves, so the railing leads to other walls.

## Two pictures, one lattice

Alex uses both readings in one breath:
- *things*: railings sit inside walls (every railing is a wall);
- *aspects*: wall's aspects sit inside railing's (a railing has all of a wall's aspects, and more).

They are the same order read in opposite directions. Formal Concept Analysis (Wille, 1982; recall) makes this exact: things × aspects gives concepts (a set of things, and the aspects they all share), and more things always means fewer shared aspects. The lattice can be *computed from the world*, which is one meaning of "more dynamically".

## His railing example holds three different relations

- railing → wall: a sortal under a sortal (what it is).
- railing → fence: a role or function (what it does: marks a boundary, keeps people on the boardwalk).
- railing → wood: a material (what it is made of). Not essential: replace it with steel and it is still the railing.

OntoClean (Guarino and Welty, 2002; recall) says a property that is not essential to its things (wooden) must not subsume one that is (railing). That is why "a railing as wood" feels different from "a railing as a wall". The design should treat material, state and role as adjectives a thing *has*, and only identity as nouns it *is*.

## What a kind does today in the kernel (read)

Nine jobs, from kernel.py, readings.py, helping.py and the live world:
1. views select by kind (`rows <kind>`, a board's `model_kind`, a map layer's `shows rows spot`);
2. words find their targets by kind (namespace = kind or a hyphen part; `<kind>` in usage);
3. authority (`grant ... only=kind:window`);
4. hearing (`rule of_kind=`);
5. explanation (`help <kind>`: words whose help mentions the kind);
6. making (declared `fields`, `required`, compose labels);
7. look (`accent nb-kind-*`);
8. name hints (`window.close Help` prefers a window called Help);
9. lifetime (proposed, clutter C2).

Nesting affects each job differently. The jobs that only read (1, 5, 7) can carry down freely. Making (6) accumulates. Lifetime and look (7, 9) cascade, nearest wins. Words (2) carry with exceptions. **Authority (3) must not carry through a classification someone else made**: if anyone can declare `secret-note is window`, every grant `only=kind:window` silently reaches secret notes. Principle to propose, alongside SHAPE's "composing words never adds power": **classifying never adds power.**

## Where kinds hide in code today (read)

- The window manager classifies native windows by a cascade of tests with a `why` for each: not top-level, cloaked, shell class, owned dialog, frameless without an app rule, elevated (`agora-wm/win32_host.py`, `Native.windows`).
- The game gate (`kernel-desktop/gaming_gate.py`) defines "video game" three ways at once: a declared list (`KNOWN`, rocketleague.exe first), a name test (`'game' in name`, minus `HELPERS`), and a state test (full-screen in front). Exceptions were added after dated misfires: the touch keyboard (26 Oct), Agora's own wallpaper layer (before 27 Oct). Each fix was a source edit.
- What "game" withholds: every WM move while the gate is up, and the bars hide.

So Alex's "running program / video game" already exists, as code nobody in the world can see, question or correct. Windows has the same move in its Game Bar: it guesses, and offers "Remember this is a game" (recall; check).

## Names already nest, and conflate two relations (read)

`plain_verb` fits a family word to a kind when the word's namespace is the kind or a hyphen part of it. `taskboard-task` (a task *of* the taskboard) and `wm-settings` (settings *for* the WM) read the same way, but the first is is-a-task and the second is is-a-settings and belongs-to-wm. Part-of and is-a are confused by the name rule. Probe: does `close` on the wm-settings thing find `wm.close`?

## When a verb should not carry (Alex's "maybe not always")

Cases, each with a real or near-real instance:
1. Same word, different act. `close` is three acts: window.close (forget the window thing, undoable), wm.close (WM_CLOSE to a native window, external), pane.close. The inner kind needs its own version. window.close's own help says it *is* a forget, narrower.
2. The inner kind's rule forbids it. Square/rectangle; the view-update problem in databases; a pamphlet's fixed panels against a document's "add page"; a decision (`leaders_only`) against a post's edit.
3. The effect can't be undone and the verb's author never thought of this kind. WM moves on a game.
4. Authority (above).
5. The verb reads aspects the inner kind spells differently (`colour` 34 vs `color` 3 in the live world): a mapping, not a refusal.
6. Who is looking. A trail crew's railing is an asset to inspect; a birding group's is a perch.
7. State. A game at its menu vs in a match. Some "kinds" are states: adjectives that come and go.

A rule set that reads only facts the dictionary already holds (`word_kind`, `undo`):
- see and hear words carry freely;
- undoable do words carry, nearest kind's own version first;
- external do words reach a narrower kind only where it said yes;
- a kind may withhold any word, with a reason the refusal quotes;
- two outer kinds offering different versions: ask (P2, "ask only when two fit"), and the answer can be kept;
- classifying never adds power.

## Bidirectional lenses

The cleanest frame for case 2: being seen as an outer kind is a view. Reading through a view always works. Writing through it works only when the write can be put back (Bancilhon and Spyratos 1981 view update; Foster, Pierce et al. bidirectional lenses, get/put laws; recall). Agora already calls its views lenses, and the old desk already hit lost updates when editing through a sibling appearance (object-facet-frontier SYNTHESIS). Kinds and lenses may share one question.

## Prototypes: kinds are things

Kind declarations are already things (`kind=kind`, dk337). Self and JavaScript (recall: Ungar and Smith 1987; Lieberman 1986) drop classes for things that delegate to things. Dynamic Desk already leans this way: "A copy is a new thing that remembers where it came from"; "A value that depends on another either follows it or says plainly that it has stopped following." If `is` means *delegate*, a kind is a prototype: its things follow its defaults (lifetime, look, fields, words) unless they say otherwise. One mechanism instead of class machinery. Risk: the fragile parent (change the kind, every thing changes), which is the same late-binding risk as verbs.

## `is:<kind>` mirrors `in:<place>`

SHAPE section 2: a thing is in many places at once, one aspect `in:<place>` each. A thing could be of many kinds the same way: `is:<kind>`, each with its own history ("became a task on 3 Nov, by Alex"). Kind things nest by `is:` as groups nest by `in:`. The contrast matters: places carry authority down (leaders reach inner groups); kinds must not.

## Graph sources

1. Link aspects (values are ids): explicit.
2. Kind shelves: thing → kind → outer kind.
3. Acts: things touched in one record; one author in one burst.
4. Mentions: ids, @names, names in text.
5. Name-valued aspects: `lane=Now` points at the lane called Now, as text.
6. Shared adjectives: same place, same time, same model.
7. Similarity (embeddings, later, on Alex's yes).

Edges are aspects, so edges nest too (RDF subPropertyOf): `reply_to` is a narrower `about`; `made_by`, `for`, `via_actor` are all "who". One relation, *narrower than*, over kinds, aspects and words.

## Per-group kinds

Agora.md: two groups may keep their own page for one park, "both pages agree on the underlying content ... bridge by place, rather than make it a dividing line." Kinds and nestings declared in a group would apply in it, nearest first, as words do. The railing stays one thing.
